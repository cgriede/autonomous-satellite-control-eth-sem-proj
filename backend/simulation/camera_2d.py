from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from environment_definition.constants import (
    DEFAULT_CAMERA_OBSERVATION_LINE_N_BINS,
    OBSERVATION_CLOUD,
    OBSERVATION_EARTH,
    OBSERVATION_LINE_NOT_COMPUTED,
    OBSERVATION_SPACE,
    OBSERVATION_TARGET,
)

from environment_definition.constants.RENDER import RENDER
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
from utils.units.require_compatible_unit import require_compatible_units


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


def compute_cloud_arc_specs_at_time(
    *,
    sim_time_s: float,
    sim_total_s: float,
    earth_radius_km: float,
) -> list[dict[str, float]]:
    """
    Build cloud arc specs (radius + start/end angles in rad) for each `SIMULATION.clouds` entry.

    Used by `run_simulation` (per frame) and by camera raytracing. Angular placement follows
    `SIMULATION.clouds`; span grows over simulated time.
    """
    growth_phase = sim_time_s / max(sim_total_s, 1e-9)
    cloud_growth = 1.0 + (RENDER.cloud_growth_max_span_scale - 1.0) * float(
        np.clip(growth_phase, 0.0, 1.0)
    )

    specs: list[dict[str, float]] = []
    for cloud in SIMULATION.clouds:
        radius_km = earth_radius_km + float(cloud.height.to(ureg.km).magnitude)
        base_start = float(cloud.start_location.to(ureg.rad).magnitude)
        base_end = float(cloud.end_location.to(ureg.rad).magnitude)
        center = 0.5 * (base_start + base_end)
        half_span = 0.5 * (base_end - base_start) * cloud_growth
        start = center - half_span
        end = center + half_span
        specs.append({"radius_km": radius_km, "start_rad": start, "end_rad": end})
    return specs


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
    t_earth = _ray_circle_intersection_distance(
        ray_origin_xy_km, ray_dir_unit_xy, radius_km=earth_radius_km
    )
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


_ASCII_BY_CODE = {
    int(OBSERVATION_SPACE): "-",
    int(OBSERVATION_EARTH): "E",
    int(OBSERVATION_CLOUD): "C",
    int(OBSERVATION_TARGET): "X",
    int(OBSERVATION_LINE_NOT_COMPUTED): "?",
}


def observation_codes_to_ascii_line(codes: np.ndarray) -> str:
    """
    Map per-bin observation codes to a single ASCII string.

    Codes follow ``CameraObservationLine1DResult`` (0–3). ``OBSERVATION_LINE_NOT_COMPUTED``
    is rendered as ``?``.
    """
    codes = np.asarray(codes, dtype=np.int8).ravel()
    parts: list[str] = []
    for c in codes:
        ci = int(c)
        ch = _ASCII_BY_CODE.get(ci)
        if ch is None:
            raise ValueError(f"Unknown observation code: {ci}")
        parts.append(ch)
    return "".join(parts)


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
) -> CameraStrip2DResult:
    """
    Simulate a single 2D camera "strip" capture.

    2D convention:
    - The renderer runs everything in the satellite's XY plane.
    - The camera boresight is the satellite body's +Z direction projected into XY.
    - The full sensor rectangle reduces to a 1D ground line segment in this plane.
    - We use the *vertical* FOV for that in-plane 1D strip.

    If the vertical-FOV footprint does not fully intersect the Earth disk (any of the
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

    horizontal_fov, vertical_fov = calculate_fov_angles()
    vertical_fov_rad = float(vertical_fov.to(ureg.rad).magnitude)
    half_vertical_fov = 0.5 * vertical_fov_rad

    gsd_m = float(calculate_gsd(altitude).to(ureg.m).magnitude)
    swath_height_flat_km = (N_PIXELS_Y * gsd_m) / 1000.0

    # Clouds for this time step
    cloud_arc_specs = compute_cloud_arc_specs_at_time(
        sim_time_s=sim_time_s,
        sim_total_s=sim_total_s,
        earth_radius_km=earth_radius_km,
    )

    # Ground intersections (Earth only) for footprint endpoints
    left_dir = _rotate_unit_xy(boresight_dir_unit_xy, -half_vertical_fov)
    right_dir = _rotate_unit_xy(boresight_dir_unit_xy, +half_vertical_fov)
    center_dir = boresight_dir_unit_xy

    t_center = _ray_circle_intersection_distance(
        sat_pos_xy_km, center_dir, radius_km=earth_radius_km
    )
    t_left = _ray_circle_intersection_distance(
        sat_pos_xy_km, left_dir, radius_km=earth_radius_km
    )
    t_right = _ray_circle_intersection_distance(
        sat_pos_xy_km, right_dir, radius_km=earth_radius_km
    )

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
            center_ray_observation_code=OBSERVATION_SPACE,
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
    elif hit_type == "earth":
        center_ray_observation_code = OBSERVATION_EARTH
    else:
        center_ray_observation_code = OBSERVATION_SPACE

    # Cloud blocked fraction: fraction of pixel rays that intersect clouds first.
    #
    # We sample pixel rays for performance; for a narrow strip, sampling is a
    # good approximation to the true per-pixel mask.
    sample_count = int(np.clip(pixel_ray_samples, 2, max(2, N_PIXELS_Y)))
    pixel_indices = np.linspace(0.0, N_PIXELS_Y - 1.0, sample_count)

    pix_idx_i = np.rint(pixel_indices).astype(int)
    y_m = (pix_idx_i - 0.5 * (N_PIXELS_Y - 1)) * PIXEL_SIZE.to(ureg.m).magnitude
    angle_rel_boresight = np.arctan2(y_m, FOCAL_LENGTH.to(ureg.m).magnitude).astype(float)
    ray_dirs = _rotate_unit_xy_batch(boresight_dir_unit_xy, angle_rel_boresight)

    if str(kernel_backend).lower() == "accelerated":
        t_earth = _ray_circle_intersection_distance_batch(
            sat_pos_xy_km,
            ray_dirs,
            radius_km=earth_radius_km,
        )
        valid_mask = np.isfinite(t_earth)
        valid = int(np.count_nonzero(valid_mask))
        if valid == 0:
            cloud_blocked_fraction = 0.0
        else:
            t_cloud_best = np.full_like(t_earth, np.nan, dtype=float)
            for cloud_spec in cloud_arc_specs:
                t_cloud = _ray_circle_intersection_distance_batch(
                    sat_pos_xy_km,
                    ray_dirs,
                    radius_km=float(cloud_spec["radius_km"]),
                )
                hit_points = sat_pos_xy_km.reshape(1, 2) + t_cloud.reshape(-1, 1) * ray_dirs
                hit_angles = np.arctan2(hit_points[:, 1], hit_points[:, 0])
                in_arc = np.vectorize(_angle_in_arc)(
                    hit_angles,
                    float(cloud_spec["start_rad"]),
                    float(cloud_spec["end_rad"]),
                )
                accepted = np.isfinite(t_cloud) & in_arc
                if not np.any(accepted):
                    continue
                assign_mask = accepted & (~np.isfinite(t_cloud_best) | (t_cloud < t_cloud_best))
                t_cloud_best[assign_mask] = t_cloud[assign_mask]
            blocked = np.isfinite(t_cloud_best) & valid_mask & (t_cloud_best < t_earth)
            cloud_blocked_fraction = float(np.count_nonzero(blocked) / max(valid, 1))
    else:
        blocked = 0
        valid = 0
        for ray_dir in ray_dirs:
            t_earth_one = _ray_circle_intersection_distance(
                sat_pos_xy_km,
                ray_dir,
                radius_km=earth_radius_km,
            )
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
        center_ray_observation_code=center_ray_observation_code,
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
      - target: 3
    """

    # Shape (n_bins,). dtype int8 for compact storage/plotting.
    observation_types: np.ndarray
    # Relative ray angles (signed) in radians, measured from the boresight direction.
    bin_ray_angles_rel_boresight_rad: np.ndarray


def _signed_angle_between_unit_xy(a_unit_xy: np.ndarray, b_unit_xy: np.ndarray) -> float:
    """
    Signed angle from `a` to `b` for 2D unit vectors.
    Range: [-pi, +pi] (via atan2 of cross/dot).
    """

    ax, ay = float(a_unit_xy[0]), float(a_unit_xy[1])
    bx, by = float(b_unit_xy[0]), float(b_unit_xy[1])
    cross = ax * by - ay * bx
    dot = ax * bx + ay * by
    return float(np.arctan2(cross, dot))


def simulate_camera_observation_line_1d(
    *,
    sat_pos_xy_km: np.ndarray,
    boresight_dir_unit_xy: np.ndarray,
    altitude: Any,
    earth_radius_km: float,
    sim_time_s: float,
    sim_total_s: float,
    target_angle_rad: float,
    n_bins: int = 100,
    cloud_arc_specs: list[dict[str, float]] | None = None,
    target_code: int = 3,
    earth_code: int = 1,
    space_code: int = 0,
    cloud_code: int = 2,
    kernel_backend: str = "python",
) -> CameraObservationLine1DResult:
    """
    Simulate a 1D camera observation line by classifying each ray bin as:
    `space`, `earth`, `cloud`, or `target`.

    The "target" is a single Earth point given by `target_angle_rad`
    using the global XY polar convention:
      target_xy = [R*cos(theta), R*sin(theta)].
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
    _hfov, vertical_fov = calculate_fov_angles()
    vertical_fov_rad = float(vertical_fov.to(ureg.rad).magnitude)
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
    target_xy_km = np.array(
        [
            float(earth_radius_km * np.cos(float(target_angle_rad))),
            float(earth_radius_km * np.sin(float(target_angle_rad))),
        ],
        dtype=float,
    )
    target_vec = target_xy_km - sat_pos_xy_km
    target_norm = float(np.linalg.norm(target_vec))
    if target_norm <= 0.0:
        raise ValueError("target point must not coincide with satellite position.")
    target_dir_unit_xy = target_vec / target_norm

    target_rel_angle_rad = _signed_angle_between_unit_xy(boresight_dir_unit_xy, target_dir_unit_xy)

    observation_types = np.full(n_bins, int(space_code), dtype=np.int8)
    # Small numerical slack to make the "half-bin" boundary stable.
    target_tol_rad = float(half_bin) + 1e-12

    # Classify each bin by first hit (cloud vs earth) and then Earth->target mapping.
    ray_dirs = _rotate_unit_xy_batch(boresight_dir_unit_xy, bin_ray_angles_rel_boresight_rad)
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
            # Only treat as target if the ray direction points near the target direction.
            # Use signed angle difference in ray-direction space.
            if str(kernel_backend).lower() == "accelerated":
                ray_rel = float(bin_ray_angles_rel_boresight_rad[i])
                delta = abs(ray_rel - target_rel_angle_rad)
            else:
                delta = abs(_signed_angle_between_unit_xy(boresight_dir_unit_xy, ray_dir_unit_xy) - target_rel_angle_rad)
            # Normalize delta to [0,pi] to handle wrap-around.
            delta = min(delta, 2.0 * np.pi - delta)
            if delta <= target_tol_rad:
                observation_types[i] = int(target_code)
            else:
                observation_types[i] = int(earth_code)
            continue

        # Defensive fallback (should not happen).
        observation_types[i] = int(space_code)

    return CameraObservationLine1DResult(
        observation_types=observation_types,
        bin_ray_angles_rel_boresight_rad=bin_ray_angles_rel_boresight_rad.astype(float),
    )



