from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast
import logging
import warnings

import numpy as np

from environment_definition.constants import (
    DEFAULT_CAMERA_OBSERVATION_LINE_N_BINS,
    OBSERVATION_CLOUD,
    OBSERVATION_EARTH,
    OBSERVATION_LINE_NOT_COMPUTED,
    OBSERVATION_SPACE,
    OBSERVATION_TARGET,
)
from environment_definition.constants.MISSION import OBSERVATION_TARGET_AREAS

from environment_definition.constants.RENDER import RENDER
from environment_definition.constants.EARTH import WGS84_ELLIPSOID
from environment_definition.constants.SIMULATION import SIMULATION
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.constants.SATELLITE import (
    FOCAL_LENGTH,
    N_PIXELS_Y,
    PIXEL_SIZE,
    SENSOR_HEIGHT,
    SENSOR_WIDTH,
)
from simulation.camera_optics import nadir_ground_sample_distance, pinhole_full_fov_rad
from utils.geometry.orbit_disk_polar_meridian import (
    cloud_disk_phi_bounds_deg,
    cloud_mean_altitude_km,
)
from utils.geometry.orbit_disk_wgs84 import (
    KM_TO_M,
    batch_disk_direction_xy_to_ecef_unit,
    batch_disk_xy_rows_km_to_geodetic_deg,
    batch_ray_oblate_spheroid_positive_hit_distance_m,
    disk_ray_earth_hit_xy_km,
    disk_xy_km_to_ecef_m,
    disk_xy_km_to_geodetic_deg,
)
from utils.units.require_compatible_unit import require_compatible_units


logger = logging.getLogger(__name__)



def _ray_circle_intersection_distance(
    ray_origin_xy_km: np.ndarray,
    ray_dir_unit_xy: np.ndarray,
    *,
    radius_km: float,
) -> float | None:
    """
    Intersection distance `t` for a 2D ray and circle:

        P(t) = ray_origin + t * ray_dir
        |P(t)| = radius

    Uses the same quadratic form as the renderer to keep conventions aligned.
    Returns the smallest positive `t`, or `None` if there is no hit.
    """
    b = 2.0 * float(np.dot(ray_origin_xy_km, ray_dir_unit_xy))
    c = float(np.dot(ray_origin_xy_km, ray_origin_xy_km) - radius_km**2)
    disc = b * b - 4.0 * c
    if disc < 0.0:
        return None

    sqrt_disc = float(np.sqrt(disc))
    t1 = (-b - sqrt_disc) / 2.0
    t2 = (-b + sqrt_disc) / 2.0

    candidates = [t for t in (t1, t2) if t > 1e-9]
    if not candidates:
        return None
    return min(candidates)


def _ray_circle_intersection_distance_batch(
    ray_origin_xy_km: np.ndarray,
    ray_dirs_unit_xy: np.ndarray,
    *,
    radius_km: float,
) -> np.ndarray:
    """Vectorized ray-circle intersection distances; NaN where no positive hit exists."""
    origins = np.asarray(ray_origin_xy_km, dtype=float).reshape(1, 2)
    dirs = np.asarray(ray_dirs_unit_xy, dtype=float)
    if dirs.ndim != 2 or dirs.shape[1] != 2:
        raise ValueError("ray_dirs_unit_xy must have shape (N,2).")
    b = 2.0 * np.sum(origins * dirs, axis=1)
    c = float(np.dot(ray_origin_xy_km, ray_origin_xy_km) - radius_km**2)
    disc = b * b - 4.0 * c
    out = np.full((dirs.shape[0],), np.nan, dtype=float)
    mask = disc >= 0.0
    if not np.any(mask):
        return out
    sqrt_disc = np.sqrt(disc[mask])
    t1 = (-b[mask] - sqrt_disc) / 2.0
    t2 = (-b[mask] + sqrt_disc) / 2.0
    t1_valid = t1 > 1e-9
    t2_valid = t2 > 1e-9
    best = np.full(t1.shape, np.nan, dtype=float)
    best[t1_valid] = t1[t1_valid]
    replace = ~t1_valid & t2_valid
    best[replace] = t2[replace]
    both = t1_valid & t2_valid
    best[both] = np.minimum(t1[both], t2[both])
    out[mask] = best
    return out


def _ray_earth_ellipsoid_intersection_distance_km(
    ray_origin_xy_km: np.ndarray,
    ray_dir_unit_xy: np.ndarray,
) -> float | None:
    """Positive ray parameter until WGS84 ellipsoid intersection (orbit-disk kinematics)."""
    t_km, _hit = disk_ray_earth_hit_xy_km(
        sat_xy_km=ray_origin_xy_km,
        ray_dir_unit_xy=ray_dir_unit_xy,
        ell=WGS84_ELLIPSOID,
    )
    return t_km


def _angle_in_arc(angle_rad: float, start_rad: float, end_rad: float) -> bool:
    """
    Returns whether `angle_rad` lies inside the arc [start_rad, end_rad],
    supporting wrap-around arcs (e.g. start > end).
    """
    two_pi = 2.0 * np.pi
    angle = angle_rad % two_pi
    start = start_rad % two_pi
    end = end_rad % two_pi
    if start <= end:
        return start <= angle <= end
    return angle >= start or angle <= end


def _angle_in_arc_batch(angles_rad: np.ndarray, start_rad: float, end_rad: float) -> np.ndarray:
    """Vectorized :func:`_angle_in_arc` for ``angles_rad`` shaped ``(N,)``."""
    two_pi = 2.0 * np.pi
    angle = np.mod(np.asarray(angles_rad, dtype=float), two_pi)
    start = start_rad % two_pi
    end = end_rad % two_pi
    if start <= end:
        return (angle >= start) & (angle <= end)
    return (angle >= start) | (angle <= end)


def _batch_earth_hit_distances_km(
    ray_origin_xy_km: np.ndarray,
    ray_dirs_unit_xy: np.ndarray,
) -> np.ndarray:
    """Positive ellipsoid hit distances in km for rows ``(N, 2)`` ray directions."""
    o_m = disk_xy_km_to_ecef_m(ray_origin_xy_km)
    dirs3 = batch_disk_direction_xy_to_ecef_unit(ray_dirs_unit_xy)
    t_m = batch_ray_oblate_spheroid_positive_hit_distance_m(o_m, dirs3, ell=WGS84_ELLIPSOID)
    return t_m / KM_TO_M


def _batch_cloud_hits_t_best(
    ray_origin_xy_km: np.ndarray,
    ray_dirs_unit_xy: np.ndarray,
    cloud_arc_specs: list[dict[str, float]],
) -> np.ndarray:
    """Nearest positive cloud-shell hit distance per ray; all clouds in one (C, N) tensor pass."""
    origin = np.asarray(ray_origin_xy_km, dtype=float).reshape(2,)
    dirs = np.asarray(ray_dirs_unit_xy, dtype=float)
    if dirs.ndim != 2 or dirs.shape[1] != 2:
        raise ValueError("ray_dirs_unit_xy must have shape (N,2).")
    n_rays = dirs.shape[0]
    if not cloud_arc_specs:
        return np.full(n_rays, np.nan, dtype=float)

    radii = np.array([float(s["radius_km"]) for s in cloud_arc_specs], dtype=float)
    starts = np.array([float(s["start_rad"]) for s in cloud_arc_specs], dtype=float)
    ends = np.array([float(s["end_rad"]) for s in cloud_arc_specs], dtype=float)
    c_count = radii.shape[0]

    b = 2.0 * (origin[0] * dirs[:, 0] + origin[1] * dirs[:, 1])
    c_origin = float(np.dot(origin, origin))
    c = c_origin - radii.reshape(c_count, 1) ** 2
    disc = b.reshape(1, n_rays) ** 2 - 4.0 * c

    t_cloud = np.full((c_count, n_rays), np.nan, dtype=float)
    mask = disc >= 0.0
    if np.any(mask):
        sqrt_disc = np.sqrt(np.maximum(disc[mask], 0.0))
        b_m = np.broadcast_to(b.reshape(1, n_rays), (c_count, n_rays))[mask]
        t1 = (-b_m - sqrt_disc) / 2.0
        t2 = (-b_m + sqrt_disc) / 2.0
        t1_valid = t1 > 1e-9
        t2_valid = t2 > 1e-9
        best = np.full(t1.shape, np.nan, dtype=float)
        best[t1_valid] = t1[t1_valid]
        replace = ~t1_valid & t2_valid
        best[replace] = t2[replace]
        both = t1_valid & t2_valid
        best[both] = np.minimum(t1[both], t2[both])
        t_cloud[mask] = best

    hit_points = origin.reshape(1, 1, 2) + t_cloud.reshape(c_count, n_rays, 1) * dirs.reshape(1, n_rays, 2)
    hit_angles = np.arctan2(hit_points[:, :, 1], hit_points[:, :, 0])

    two_pi = 2.0 * np.pi
    angle = np.mod(hit_angles, two_pi)
    start = np.mod(starts.reshape(c_count, 1), two_pi)
    end = np.mod(ends.reshape(c_count, 1), two_pi)
    wrap = start > end
    in_arc_normal = (angle >= start) & (angle <= end)
    in_arc_wrap = (angle >= start) | (angle <= end)
    in_arc = np.where(wrap, in_arc_wrap, in_arc_normal)

    accepted = np.isfinite(t_cloud) & in_arc
    t_cloud_masked = np.where(accepted, t_cloud, np.nan)
    # NOTE: Most rays miss every cloud arc, so nanmin sees all-NaN columns and NumPy emits
    # RuntimeWarning even though NaN is the intended "no cloud hit" sentinel (see has_cloud below).
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            category=RuntimeWarning,
            message="All-NaN slice encountered",
        )
        return np.nanmin(t_cloud_masked, axis=0)


def _batch_first_hit_earth_or_clouds(
    *,
    ray_origin_xy_km: np.ndarray,
    ray_dirs_unit_xy: np.ndarray,
    cloud_arc_specs: list[dict[str, float]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Batch first-hit classification for all rays.

    Returns:
        hit_type (N,) int8: 0 space, 1 earth, 2 cloud
        t_hit (N,) km
        hit_xy_km (N, 2)
    """
    origin = np.asarray(ray_origin_xy_km, dtype=float).reshape(2,)
    dirs = np.asarray(ray_dirs_unit_xy, dtype=float)
    n = dirs.shape[0]
    t_earth = _batch_earth_hit_distances_km(origin, dirs)
    t_cloud_best = _batch_cloud_hits_t_best(origin, dirs, cloud_arc_specs)

    has_earth = np.isfinite(t_earth)
    has_cloud = np.isfinite(t_cloud_best)
    cloud_wins = has_cloud & ((~has_earth) | (t_cloud_best < t_earth))
    earth_wins = has_earth & (~cloud_wins)

    hit_type = np.zeros(n, dtype=np.int8)
    hit_type[earth_wins] = np.int8(1)
    hit_type[cloud_wins] = np.int8(2)

    t_hit = np.full(n, np.nan, dtype=float)
    t_hit[earth_wins] = t_earth[earth_wins]
    t_hit[cloud_wins] = t_cloud_best[cloud_wins]

    hit_xy = origin.reshape(1, 2) + t_hit.reshape(-1, 1) * dirs
    hit_xy[~(earth_wins | cloud_wins)] = np.nan
    return hit_type, t_hit, hit_xy


def calculate_gsd(
    altitude: Any,
    *,
    off_nadir_angle: Any | None = None,
) -> Any:
    """
    Calculate Ground Sample Distance (GSD) with required formula:

        GSD = (Pixel Size × Altitude) / Focal Length

    Args:
        altitude: Pint length quantity (e.g. `500 * ureg.km`)
        off_nadir_angle: Optional pint angle quantity. If provided,
            we apply a simple geometric stretch approximation:
                GSD_eff = GSD / cos(off_nadir)
            (kept optional to avoid changing the required nadir formula).
    """
    require_compatible_units(altitude, "meter", "altitude")
    gsd = nadir_ground_sample_distance(
        pixel_size=PIXEL_SIZE,
        altitude=altitude,
        focal_length=FOCAL_LENGTH,
    )

    if off_nadir_angle is None:
        return gsd

    require_compatible_units(off_nadir_angle, "radian", "off_nadir_angle")
    off_nadir_mag = float(off_nadir_angle.to(ureg.rad).magnitude)
    cos_val = float(np.cos(off_nadir_mag))
    cos_val = max(cos_val, 1e-6)  # prevent blow-up near 90°
    return gsd / cos_val


def calculate_fov_angles() -> tuple[Any, Any]:
    """
    Required observation cone (field-of-view) angles:

        FOV = 2 * arctan((sensor_dim/2) / focal_length)

    Returns:
        (horizontal_fov, vertical_fov) as Pint angle quantities in radians.
    """
    horizontal_fov = pinhole_full_fov_rad(sensor_dim=SENSOR_WIDTH, focal_length=FOCAL_LENGTH)
    vertical_fov = pinhole_full_fov_rad(sensor_dim=SENSOR_HEIGHT, focal_length=FOCAL_LENGTH)
    return horizontal_fov, vertical_fov


def _rotate_unit_xy(dir_unit_xy: np.ndarray, angle_rad: float) -> np.ndarray:
    cos_a, sin_a = float(np.cos(angle_rad)), float(np.sin(angle_rad))
    x = float(dir_unit_xy[0])
    y = float(dir_unit_xy[1])
    return np.array([cos_a * x - sin_a * y, sin_a * x + cos_a * y], dtype=float)


def _rotate_unit_xy_batch(dir_unit_xy: np.ndarray, angles_rad: np.ndarray) -> np.ndarray:
    dirs = np.asarray(dir_unit_xy, dtype=float).reshape(2,)
    ang = np.asarray(angles_rad, dtype=float).reshape(-1)
    cos_a = np.cos(ang)
    sin_a = np.sin(ang)
    x = float(dirs[0])
    y = float(dirs[1])
    out_x = cos_a * x - sin_a * y
    out_y = sin_a * x + cos_a * y
    return np.stack((out_x, out_y), axis=1)


def boresight_dir_for_mount(body_z_angle_rad: float, tilt_off_nadir_rad: float) -> np.ndarray:
    """Compute boresight unit vector for a tilted camera mount in the orbit disk.

    Positive ``tilt_off_nadir_rad`` tilts the boresight in the prograde (forward
    along-track) direction. In the 2D orbit disk, prograde is obtained by rotating
    the nadir boresight clockwise (i.e. by –tilt_off_nadir_rad in standard CCW convention).

    Sign convention (locked): positive tilt = ahead of subsatellite ground track.
    TDD: ``test_secondary_boresight_distinct_from_primary`` verifies that the
    secondary ground center is displaced in the prograde direction.

    Args:
        body_z_angle_rad: Body-z angle in radians (defines nadir boresight direction).
        tilt_off_nadir_rad: Signed tilt angle in radians. Positive = prograde/forward.

    Returns:
        2D unit vector in the orbit disk.
    """
    nadir_boresight = np.array([np.cos(body_z_angle_rad), np.sin(body_z_angle_rad)], dtype=float)
    return _rotate_unit_xy(nadir_boresight, -tilt_off_nadir_rad)


def off_nadir_angle_rad(
    sat_pos_xy_km: np.ndarray,
    boresight_dir_unit_xy: np.ndarray,
) -> float:
    """Angle between boresight and local nadir (toward Earth disk origin) [rad]."""
    sat = np.asarray(sat_pos_xy_km, dtype=float).reshape(2)
    bore = np.asarray(boresight_dir_unit_xy, dtype=float).reshape(2)
    sat_norm = float(np.linalg.norm(sat))
    if sat_norm <= 0.0:
        return 0.0
    nadir = -sat / sat_norm
    bore_norm = float(np.linalg.norm(bore))
    if bore_norm <= 0.0:
        return 0.0
    bore = bore / bore_norm
    dot = float(np.clip(np.dot(bore, nadir), -1.0, 1.0))
    return float(np.arccos(dot))


def effective_gsd_m(
    altitude: Any,
    sat_pos_xy_km: np.ndarray,
    boresight_dir_unit_xy: np.ndarray,
) -> float:
    """Nadir GSD scaled by ``1/cos(off_nadir)`` for the current boresight."""
    off_nadir_rad = off_nadir_angle_rad(sat_pos_xy_km, boresight_dir_unit_xy)
    return float(
        calculate_gsd(altitude, off_nadir_angle=off_nadir_rad * ureg.rad).to(ureg.m).magnitude
    )


def compute_cloud_arc_specs_at_time(
    *,
    sim_time_s: float,
    sim_total_s: float,
    earth_radius_km: float,
    clouds: tuple | None = None,
) -> list[dict[str, float]]:
    """
    Build cloud arc specs (radius + start/end angles in rad) for each cloud entry.

    Used by `run_simulation` (per frame) and by camera raytracing. Angular placement
    follows the provided ``clouds`` tuple; span grows over simulated time.

    Args:
        clouds: Cloud definitions to use. Defaults to ``SIMULATION.clouds`` when ``None``.
    """
    _clouds = clouds if clouds is not None else SIMULATION.clouds
    growth_phase = sim_time_s / max(sim_total_s, 1e-9)
    cloud_growth = 1.0 + (RENDER.cloud_growth_max_span_scale - 1.0) * float(
        np.clip(growth_phase, 0.0, 1.0)
    )

    specs: list[dict[str, float]] = []
    for cloud in _clouds:
        radius_km = earth_radius_km + cloud_mean_altitude_km(cloud)
        phi_start_deg, phi_end_deg = cloud_disk_phi_bounds_deg(cloud)
        base_start = float(np.deg2rad(phi_start_deg))
        base_end = float(np.deg2rad(phi_end_deg))
        center = 0.5 * (base_start + base_end)
        half_span = 0.5 * (base_end - base_start) * cloud_growth
        start = center - half_span
        end = center + half_span
        specs.append({"radius_km": radius_km, "start_rad": start, "end_rad": end})
    return specs


def precompute_cloud_arc_specs_series(
    *,
    t_s: np.ndarray,
    sim_total_s: float,
    earth_radius_km: float,
    clouds: tuple,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Precompute cloud arc geometry for every simulation frame.

    Same semantics as calling :func:`compute_cloud_arc_specs_at_time` per row of ``t_s``.
    Returns ``(radius_km, start_rad, end_rad)`` each with shape ``(n_frames, n_clouds)``.
    """
    times = np.asarray(t_s, dtype=float).ravel()
    n_frames = int(times.shape[0])
    n_clouds = len(clouds)
    if n_clouds == 0:
        empty = np.empty((n_frames, 0), dtype=float)
        return empty, empty.copy(), empty.copy()

    growth_phase = np.clip(times / max(float(sim_total_s), 1e-9), 0.0, 1.0)
    cloud_growth = 1.0 + (float(RENDER.cloud_growth_max_span_scale) - 1.0) * growth_phase

    radius_km = np.empty((n_frames, n_clouds), dtype=float)
    start_rad = np.empty((n_frames, n_clouds), dtype=float)
    end_rad = np.empty((n_frames, n_clouds), dtype=float)

    for i, cloud in enumerate(clouds):
        r_km = float(earth_radius_km) + float(cloud_mean_altitude_km(cloud))
        phi_start_deg, phi_end_deg = cloud_disk_phi_bounds_deg(cloud)
        base_start = float(np.deg2rad(phi_start_deg))
        base_end = float(np.deg2rad(phi_end_deg))
        center = 0.5 * (base_start + base_end)
        half_span_base = 0.5 * (base_end - base_start)
        half_span = half_span_base * cloud_growth
        radius_km[:, i] = r_km
        start_rad[:, i] = center - half_span
        end_rad[:, i] = center + half_span

    return radius_km, start_rad, end_rad


def cloud_arc_specs_list_for_frame(
    *,
    radius_km: np.ndarray,
    start_rad: np.ndarray,
    end_rad: np.ndarray,
    frame_idx: int,
) -> list[dict[str, float]]:
    """Build per-cloud spec dicts for one frame index (sensor / ray API)."""
    r_row = np.asarray(radius_km[frame_idx], dtype=float)
    s_row = np.asarray(start_rad[frame_idx], dtype=float)
    e_row = np.asarray(end_rad[frame_idx], dtype=float)
    return [
        {"radius_km": float(r_row[i]), "start_rad": float(s_row[i]), "end_rad": float(e_row[i])}
        for i in range(r_row.shape[0])
    ]


def _first_hit_point_ray_earth_or_clouds(
    *,
    ray_origin_xy_km: np.ndarray,
    ray_dir_unit_xy: np.ndarray,
    earth_radius_km: float,
    cloud_arc_specs: list[dict[str, float]],
) -> tuple[str | None, float | None, np.ndarray | None]:
    """
    Determine the first intersection point along a ray between:
    - Earth surface (circle radius = earth_radius_km)
    - Cloud arcs (opaque arcs on circles at radius = earth_radius_km + height)

    Returns:
        (hit_type, t_hit, hit_point_xy_km)
        where hit_type is one of {"earth","cloud"} or None if no hit exists.
    """
    t_earth = _ray_earth_ellipsoid_intersection_distance_km(ray_origin_xy_km, ray_dir_unit_xy)
    if t_earth is None:
        best_t = None
        best_type: str | None = None
        best_point = None
    else:
        best_t = t_earth
        best_type = "earth"
        best_point = ray_origin_xy_km + best_t * ray_dir_unit_xy

    for cloud_spec in cloud_arc_specs:
        t_cloud = _ray_circle_intersection_distance(
            ray_origin_xy_km, ray_dir_unit_xy, radius_km=cloud_spec["radius_km"]
        )
        if t_cloud is None:
            continue
        hit_point = ray_origin_xy_km + t_cloud * ray_dir_unit_xy
        hit_angle = float(np.arctan2(hit_point[1], hit_point[0]))
        if not _angle_in_arc(hit_angle, cloud_spec["start_rad"], cloud_spec["end_rad"]):
            continue

        if best_t is None or t_cloud < best_t:
            best_t = t_cloud
            best_type = "cloud"
            best_point = hit_point

    return best_type, best_t, best_point


def observation_codes_to_ascii_line(codes: np.ndarray) -> str:
    """
    Map per-bin observation codes to a single ASCII string.

    Space ``-``, earth ``E``, cloud ``C``, targets ``0``–``9`` / ``A``–``Z`` for T0–T35,
    not computed ``?``.
    """
    from environment_definition.constants.observation_codes import observation_code_to_ascii

    codes = np.asarray(codes, dtype=np.int8).ravel()
    return "".join(observation_code_to_ascii(int(c)) for c in codes)


@dataclass(frozen=True)
class CameraStrip2DResult:
    # Scalar optics quantities
    gsd_m: float
    vertical_fov_rad: float

    # Ground geometry (Earth intersection points)
    ground_center_xy_km: np.ndarray
    ground_left_xy_km: np.ndarray
    ground_right_xy_km: np.ndarray

    # Center pixel first obstruction (cloud vs Earth)
    center_first_hit_xy_km: np.ndarray | None
    center_first_hit_is_cloud: bool

    # What the center (boresight) ray sees first: 0 space, 1 earth, 2 cloud, 3 target (reserved).
    center_ray_observation_code: int

    # Cloud visibility across the 1D pixel strip
    cloud_blocked_fraction: float

    # Convenience: flat swath computed from nadir GSD
    swath_height_flat_km: float


def simulate_camera_strip_2d(
    *,
    sat_pos_xy_km: np.ndarray,
    boresight_dir_unit_xy: np.ndarray,
    altitude: Any,
    earth_radius_km: float,
    sim_time_s: float,
    sim_total_s: float,
    pixel_ray_samples: int = 1000,
    kernel_backend: str = "python",
    cloud_arc_specs: list[dict[str, float]] | None = None,
    vertical_fov_rad: float | None = None,
) -> CameraStrip2DResult:
    """
    Simulate a single 2D camera "strip" capture.

    2D convention:
    - The renderer runs everything in the satellite's XY plane.
    - The camera boresight is the satellite body's +Z direction projected into XY.
    - The full sensor rectangle reduces to a 1D ground line segment in this plane.
    - We use the *vertical* FOV for that in-plane 1D strip.

    If the vertical-FOV footprint does not fully intersect the Earth ellipsoid (any of the
    three boundary rays misses), ground points are NaN, ``center_ray_observation_code``
    is ``OBSERVATION_SPACE`` (0), and ``cloud_blocked_fraction`` is NaN (no valid
    ground rays to sample). Optics scalars (GSD, FOV) are still returned.
    """
    require_compatible_units(altitude, "meter", "altitude")

    sat_pos_xy_km = np.asarray(sat_pos_xy_km, dtype=float)
    boresight_dir_unit_xy = np.asarray(boresight_dir_unit_xy, dtype=float)
    if sat_pos_xy_km.shape != (2,) or boresight_dir_unit_xy.shape != (2,):
        raise ValueError("sat_pos_xy_km and boresight_dir_unit_xy must have shape (2,).")

    # Normalize boresight direction defensively
    dir_norm = float(np.linalg.norm(boresight_dir_unit_xy))
    if dir_norm <= 0.0:
        raise ValueError("boresight_dir_unit_xy must be non-zero.")
    boresight_dir_unit_xy = boresight_dir_unit_xy / dir_norm

    if vertical_fov_rad is None:
        _hfov, _vfov = calculate_fov_angles()
        vertical_fov_rad = float(_vfov.to(ureg.rad).magnitude)
    half_vertical_fov = 0.5 * vertical_fov_rad

    gsd_m = effective_gsd_m(altitude, sat_pos_xy_km, boresight_dir_unit_xy)
    swath_height_flat_km = (N_PIXELS_Y * gsd_m) / 1000.0

    # Clouds for this time step (reuse pre-computed specs when provided)
    if cloud_arc_specs is None:
        cloud_arc_specs = compute_cloud_arc_specs_at_time(
            sim_time_s=sim_time_s,
            sim_total_s=sim_total_s,
            earth_radius_km=earth_radius_km,
        )

    # Ground intersections (Earth only) for footprint endpoints
    left_dir = _rotate_unit_xy(boresight_dir_unit_xy, -half_vertical_fov)
    right_dir = _rotate_unit_xy(boresight_dir_unit_xy, +half_vertical_fov)
    center_dir = boresight_dir_unit_xy

    t_center = _ray_earth_ellipsoid_intersection_distance_km(sat_pos_xy_km, center_dir)
    t_left = _ray_earth_ellipsoid_intersection_distance_km(sat_pos_xy_km, left_dir)
    t_right = _ray_earth_ellipsoid_intersection_distance_km(sat_pos_xy_km, right_dir)

    nan2 = np.full(2, np.nan, dtype=float)
    if t_center is None or t_left is None or t_right is None:
        return CameraStrip2DResult(
            gsd_m=gsd_m,
            vertical_fov_rad=vertical_fov_rad,
            ground_center_xy_km=nan2.copy(),
            ground_left_xy_km=nan2.copy(),
            ground_right_xy_km=nan2.copy(),
            center_first_hit_xy_km=None,
            center_first_hit_is_cloud=False,
            center_ray_observation_code=int(OBSERVATION_SPACE),
            cloud_blocked_fraction=float("nan"),
            swath_height_flat_km=swath_height_flat_km,
        )

    ground_center_xy_km = sat_pos_xy_km + t_center * center_dir
    ground_left_xy_km = sat_pos_xy_km + t_left * left_dir
    ground_right_xy_km = sat_pos_xy_km + t_right * right_dir

    # Center first hit (Earth or cloud) for "what the center pixel sees"
    hit_type, _t_hit, center_first_hit_xy_km = _first_hit_point_ray_earth_or_clouds(
        ray_origin_xy_km=sat_pos_xy_km,
        ray_dir_unit_xy=center_dir,
        earth_radius_km=earth_radius_km,
        cloud_arc_specs=cloud_arc_specs,
    )
    center_first_hit_is_cloud = bool(hit_type == "cloud")
    if hit_type == "cloud":
        center_ray_observation_code = OBSERVATION_CLOUD
    elif hit_type == "earth" and center_first_hit_xy_km is not None:
        from utils.geometry.mission_stripe_disk import classify_earth_hit_observation_code

        areas = OBSERVATION_TARGET_AREAS
        center_ray_observation_code = classify_earth_hit_observation_code(
            center_first_hit_xy_km,
            target_areas=areas,
            earth_code=int(OBSERVATION_EARTH),
            target_code=int(OBSERVATION_TARGET),
        )
    else:
        center_ray_observation_code = OBSERVATION_SPACE

    # Cloud blocked fraction: fraction of pixel rays that intersect clouds first.
    #
    # We sample pixel rays for performance; for a narrow strip, sampling is a
    # good approximation to the true per-pixel mask.
    sample_count = int(np.clip(pixel_ray_samples, 2, max(2, N_PIXELS_Y)))
    pixel_indices = np.linspace(0.0, N_PIXELS_Y - 1.0, sample_count)

    pix_idx_i = np.rint(pixel_indices).astype(int)
    pixel_size_m = float(cast(Any, PIXEL_SIZE).to(ureg.m).magnitude)
    focal_length_m = float(cast(Any, FOCAL_LENGTH).to(ureg.m).magnitude)
    y_m = (pix_idx_i - 0.5 * (N_PIXELS_Y - 1)) * pixel_size_m
    angle_rel_boresight = np.arctan2(y_m, focal_length_m).astype(float)
    ray_dirs = _rotate_unit_xy_batch(boresight_dir_unit_xy, angle_rel_boresight)

    if str(kernel_backend).lower() == "accelerated":
        t_earth = _batch_earth_hit_distances_km(sat_pos_xy_km, ray_dirs)
        valid_mask = np.isfinite(t_earth)
        valid = int(np.count_nonzero(valid_mask))
        if valid == 0:
            cloud_blocked_fraction = 0.0
        else:
            t_cloud_best_arr = _batch_cloud_hits_t_best(sat_pos_xy_km, ray_dirs, cloud_arc_specs)
            blocked = np.isfinite(t_cloud_best_arr) & valid_mask & (t_cloud_best_arr < t_earth)
            cloud_blocked_fraction = float(np.count_nonzero(blocked) / max(valid, 1))
    else:
        blocked = 0
        valid = 0
        for ray_dir in ray_dirs:
            t_earth_one = _ray_earth_ellipsoid_intersection_distance_km(sat_pos_xy_km, ray_dir)
            if t_earth_one is None:
                continue
            valid += 1
            t_cloud_best: float | None = None
            for cloud_spec in cloud_arc_specs:
                t_cloud = _ray_circle_intersection_distance(
                    sat_pos_xy_km, ray_dir, radius_km=cloud_spec["radius_km"]
                )
                if t_cloud is None:
                    continue
                hit_point = sat_pos_xy_km + t_cloud * ray_dir
                hit_angle = float(np.arctan2(hit_point[1], hit_point[0]))
                if not _angle_in_arc(hit_angle, cloud_spec["start_rad"], cloud_spec["end_rad"]):
                    continue
                if t_cloud_best is None or t_cloud < t_cloud_best:
                    t_cloud_best = t_cloud
            if t_cloud_best is not None and t_cloud_best < t_earth_one:
                blocked += 1
        cloud_blocked_fraction = float(blocked / max(valid, 1))

    return CameraStrip2DResult(
        gsd_m=gsd_m,
        vertical_fov_rad=vertical_fov_rad,
        ground_center_xy_km=ground_center_xy_km,
        ground_left_xy_km=ground_left_xy_km,
        ground_right_xy_km=ground_right_xy_km,
        center_first_hit_xy_km=center_first_hit_xy_km,
        center_first_hit_is_cloud=center_first_hit_is_cloud,
        center_ray_observation_code=int(center_ray_observation_code),
        cloud_blocked_fraction=cloud_blocked_fraction,
        swath_height_flat_km=swath_height_flat_km,
    )


@dataclass(frozen=True)
class CameraObservationLine1DResult:
    """
    Per-bin 1D camera observation classification.

    observation_types codes:
      - space: 0
      - earth: 1
      - cloud: 2
      - targets: 3 + index (T0 = 3, T1 = 4, …)
    """

    # Shape (n_bins,). dtype int8 for compact storage/plotting.
    observation_types: np.ndarray
    # Relative ray angles (signed) in radians, measured from the boresight direction.
    bin_ray_angles_rel_boresight_rad: np.ndarray

def simulate_camera_observation_line_1d(
    *,
    sat_pos_xy_km: np.ndarray,
    boresight_dir_unit_xy: np.ndarray,
    altitude: Any,
    earth_radius_km: float,
    sim_time_s: float,
    sim_total_s: float,
    n_bins: int = 100,
    cloud_arc_specs: list[dict[str, float]] | None = None,
    target_code: int = 3,
    earth_code: int = 1,
    space_code: int = 0,
    cloud_code: int = 2,
    kernel_backend: str = "python",
    vertical_fov_rad: float | None = None,
    target_areas: tuple | None = None,
) -> CameraObservationLine1DResult:
    """
    Simulate a 1D camera observation line by classifying each ray bin as:
    `space`, `earth`, `cloud`, or `target`.

        The "target" is any Earth hit whose latitude falls inside one of the
        configured target areas (defaults to ``OBSERVATION_TARGET_AREAS``).
    """

    if n_bins <= 0:
        raise ValueError("n_bins must be > 0.")
    if target_code == earth_code or target_code == space_code or target_code == cloud_code:
        raise ValueError("observation codes must be distinct.")
    if earth_code == space_code or earth_code == cloud_code:
        raise ValueError("observation codes must be distinct.")

    # Keep unit validation consistent with the rest of the optics module.
    require_compatible_units(altitude, "meter", "altitude")

    sat_pos_xy_km = np.asarray(sat_pos_xy_km, dtype=float)
    boresight_dir_unit_xy = np.asarray(boresight_dir_unit_xy, dtype=float)
    if sat_pos_xy_km.shape != (2,) or boresight_dir_unit_xy.shape != (2,):
        raise ValueError("sat_pos_xy_km and boresight_dir_unit_xy must have shape (2,).")

    # Normalize boresight direction defensively.
    dir_norm = float(np.linalg.norm(boresight_dir_unit_xy))
    if dir_norm <= 0.0:
        raise ValueError("boresight_dir_unit_xy must be non-zero.")
    boresight_dir_unit_xy = boresight_dir_unit_xy / dir_norm

    if cloud_arc_specs is None:
        cloud_arc_specs = compute_cloud_arc_specs_at_time(
            sim_time_s=sim_time_s,
            sim_total_s=sim_total_s,
            earth_radius_km=earth_radius_km,
        )

    # We reuse the vertical sensor FOV for the 1D strip.
    if vertical_fov_rad is None:
        _hfov, _vfov = calculate_fov_angles()
        vertical_fov_rad = float(_vfov.to(ureg.rad).magnitude)
    half_vertical_fov_rad = 0.5 * vertical_fov_rad

    # Ray bins: choose bin-center angles so tolerance = half-bin
    # corresponds to neighbor-inclusive binning (as intended in the plan).
    half_bin = vertical_fov_rad / (2.0 * n_bins)
    bin_ray_angles_rel_boresight_rad = np.linspace(
        -half_vertical_fov_rad + half_bin,
        +half_vertical_fov_rad - half_bin,
        n_bins,
        dtype=float,
    )

    # Target direction unit vector from the satellite to the target Earth point.
    areas = target_areas if target_areas is not None else OBSERVATION_TARGET_AREAS
    from environment_definition.constants.observation_codes import observation_target_code_for_index
    from utils.geometry.mission_stripe_disk import (
        geodetic_target_area_index,
        target_areas_track_offset_ranges_deg,
    )

    target_offset_ranges = target_areas_track_offset_ranges_deg(areas)

    def _target_index_for_hit(hit_point_xy_km: np.ndarray) -> int | None:
        lon_deg, lat_deg = disk_xy_km_to_geodetic_deg(hit_point_xy_km, ell=WGS84_ELLIPSOID)
        return geodetic_target_area_index(
            lon_deg=lon_deg,
            lat_deg=lat_deg,
            offset_ranges=target_offset_ranges,
        )

    observation_types = np.full(n_bins, int(space_code), dtype=np.int8)

    # Classify each bin by first hit (cloud vs earth) and then Earth->target mapping.
    ray_dirs = _rotate_unit_xy_batch(boresight_dir_unit_xy, bin_ray_angles_rel_boresight_rad)

    if str(kernel_backend).lower() == "accelerated":
        hit_types, _t_hit, hit_xy = _batch_first_hit_earth_or_clouds(
            ray_origin_xy_km=sat_pos_xy_km,
            ray_dirs_unit_xy=ray_dirs,
            cloud_arc_specs=cloud_arc_specs,
        )
        observation_types[hit_types == 2] = np.int8(cloud_code)
        earth_mask = hit_types == 1
        observation_types[earth_mask] = np.int8(earth_code)
        if np.any(earth_mask):
            earth_pts = hit_xy[earth_mask]
            _lon_deg, lat_deg = batch_disk_xy_rows_km_to_geodetic_deg(earth_pts, ell=WGS84_ELLIPSOID)
            earth_indices = np.nonzero(earth_mask)[0]
            for j, idx in enumerate(earth_indices):
                lon = float(_lon_deg[j])
                lat = float(lat_deg[j])
                t_idx = geodetic_target_area_index(
                    lon_deg=lon,
                    lat_deg=lat,
                    offset_ranges=target_offset_ranges,
                )
                if t_idx is not None:
                    observation_types[int(idx)] = observation_target_code_for_index(t_idx)
    else:
        for i, ray_dir_unit_xy in enumerate(ray_dirs):

            hit_type, _t_hit, _hit_xy_km = _first_hit_point_ray_earth_or_clouds(
                ray_origin_xy_km=sat_pos_xy_km,
                ray_dir_unit_xy=ray_dir_unit_xy,
                earth_radius_km=earth_radius_km,
                cloud_arc_specs=cloud_arc_specs,
            )

            if hit_type is None:
                observation_types[i] = int(space_code)
                continue
            if hit_type == "cloud":
                observation_types[i] = int(cloud_code)
                continue
            if hit_type == "earth":
                if _hit_xy_km is not None:
                    t_idx = _target_index_for_hit(_hit_xy_km)
                    if t_idx is not None:
                        observation_types[i] = int(observation_target_code_for_index(t_idx))
                    else:
                        observation_types[i] = int(earth_code)
                else:
                    observation_types[i] = int(earth_code)
                continue

            # Defensive fallback (should not happen).
            observation_types[i] = int(space_code)

    return CameraObservationLine1DResult(
        observation_types=observation_types,
        bin_ray_angles_rel_boresight_rad=bin_ray_angles_rel_boresight_rad.astype(float),
    )



