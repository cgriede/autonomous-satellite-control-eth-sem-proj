from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from environment_definition.constants import RENDER, SIMULATION, UREG as ureg
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
    rot = np.array([[cos_a, -sin_a], [sin_a, cos_a]], dtype=float)
    return rot @ dir_unit_xy


def _compute_cloud_arc_specs_at_time(
    *,
    sim_time_s: float,
    sim_total_s: float,
    earth_radius_km: float,
) -> list[dict[str, float]]:
    """
    Build opaque cloud arc specs in the renderer's 2D geometry convention.

    Note:
    In the current renderer implementation, cloud *angular placement* is fixed
    (a shift term is set to 0.0), and only the arc span grows over time.
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
) -> CameraStrip2DResult:
    """
    Simulate a single 2D camera "strip" capture.

    2D convention:
    - The renderer runs everything in the satellite's XY plane.
    - The camera boresight is the satellite body's +Z direction projected into XY.
    - The full sensor rectangle reduces to a 1D ground line segment in this plane.
    - We use the *vertical* FOV for that in-plane 1D strip.
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
    cloud_arc_specs = _compute_cloud_arc_specs_at_time(
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

    if t_center is None or t_left is None or t_right is None:
        raise RuntimeError("Camera strip ray did not intersect the Earth; check pointing geometry.")

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

    # Cloud blocked fraction: fraction of pixel rays that intersect clouds first.
    #
    # We sample pixel rays for performance; for a narrow strip, sampling is a
    # good approximation to the true per-pixel mask.
    sample_count = int(np.clip(pixel_ray_samples, 2, max(2, N_PIXELS_Y)))
    pixel_indices = np.linspace(0.0, N_PIXELS_Y - 1.0, sample_count)

    blocked = 0
    valid = 0
    for pix_idx in pixel_indices:
        pix_idx_i = int(round(float(pix_idx)))
        # Sensor y coordinate for this pixel center, relative to sensor center.
        y_m = (pix_idx_i - 0.5 * (N_PIXELS_Y - 1)) * PIXEL_SIZE.to(ureg.m).magnitude
        angle_rel_boresight = float(np.arctan2(y_m, FOCAL_LENGTH.to(ureg.m).magnitude))

        ray_dir = _rotate_unit_xy(boresight_dir_unit_xy, angle_rel_boresight)

        t_earth = _ray_circle_intersection_distance(
            sat_pos_xy_km, ray_dir, radius_km=earth_radius_km
        )
        if t_earth is None:
            continue
        valid += 1

        # Find the nearest cloud hit on this ray (if any)
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

        if t_cloud_best is not None and t_cloud_best < t_earth:
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
        cloud_blocked_fraction=cloud_blocked_fraction,
        swath_height_flat_km=swath_height_flat_km,
    )


def calculate_swath_height(
    altitude: Any,
    *,
    off_nadir_angle: Any | None = None,
) -> Any:
    """
    Convenience swath helper using the required GSD formula:
        swath_height = N_PIXELS_Y * GSD
    """
    gsd = calculate_gsd(altitude, off_nadir_angle=off_nadir_angle)
    return (N_PIXELS_Y * gsd).to(ureg.m)

