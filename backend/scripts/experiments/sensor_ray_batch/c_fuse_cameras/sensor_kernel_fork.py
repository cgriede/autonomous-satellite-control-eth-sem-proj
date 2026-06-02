"""Hypothesis C — fused multi-camera ray batch (fork of sensor_kernel.evaluate)."""

from __future__ import annotations

from typing import Any, cast

import numpy as np

from environment_definition.constants.MISSION import OBSERVATION_TARGET_AREAS
from environment_definition.constants.SATELLITE import FOCAL_LENGTH, N_PIXELS_Y, PIXEL_SIZE
from environment_definition.constants.SIMULATION import OBSERVATION_CLOUD, OBSERVATION_EARTH, OBSERVATION_SPACE, SIMULATION
from environment_definition.constants.EARTH import WGS84_ELLIPSOID
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.camera_2d import (
    OBSERVATION_CLOUD,
    _batch_earth_hit_distances_km,
    _batch_first_hit_earth_or_clouds,
    _first_hit_point_ray_earth_or_clouds,
    _ray_earth_ellipsoid_intersection_distance_km,
    _rotate_unit_xy,
    _rotate_unit_xy_batch,
    calculate_fov_angles,
    calculate_gsd,
    compute_cloud_arc_specs_at_time,
)
from simulation.sensor_kernel import SensorTimestepResult
from utils.geometry.orbit_disk_wgs84 import batch_disk_xy_rows_km_to_geodetic_deg
from utils.units.require_compatible_unit import require_compatible_units


def _strip_pixel_ray_dirs(boresight_dir_unit_xy: np.ndarray, pixel_ray_samples: int) -> np.ndarray:
    sample_count = int(np.clip(pixel_ray_samples, 2, max(2, N_PIXELS_Y)))
    pixel_indices = np.linspace(0.0, N_PIXELS_Y - 1.0, sample_count)
    pix_idx_i = np.rint(pixel_indices).astype(int)
    pixel_size_m = float(cast(Any, PIXEL_SIZE).to(ureg.m).magnitude)
    focal_length_m = float(cast(Any, FOCAL_LENGTH).to(ureg.m).magnitude)
    y_m = (pix_idx_i - 0.5 * (N_PIXELS_Y - 1)) * pixel_size_m
    angle_rel_boresight = np.arctan2(y_m, focal_length_m).astype(float)
    return _rotate_unit_xy_batch(boresight_dir_unit_xy, angle_rel_boresight)


def _line_bin_ray_dirs(
    boresight_dir_unit_xy: np.ndarray,
    *,
    n_bins: int,
    vertical_fov_rad: float,
) -> np.ndarray:
    half_vertical_fov_rad = 0.5 * vertical_fov_rad
    half_bin = vertical_fov_rad / (2.0 * n_bins)
    bin_ray_angles = np.linspace(
        -half_vertical_fov_rad + half_bin,
        +half_vertical_fov_rad - half_bin,
        n_bins,
        dtype=float,
    )
    return _rotate_unit_xy_batch(boresight_dir_unit_xy, bin_ray_angles)


def _classify_line_from_hits(
    hit_types: np.ndarray,
    hit_xy: np.ndarray,
    *,
    target_areas: tuple | None,
    space_code: int = 0,
    earth_code: int = 1,
    cloud_code: int = 2,
    target_code: int = 3,
) -> np.ndarray:
    n = hit_types.shape[0]
    observation_types = np.full(n, int(space_code), dtype=np.int8)
    observation_types[hit_types == 2] = np.int8(cloud_code)
    earth_mask = hit_types == 1
    observation_types[earth_mask] = np.int8(earth_code)

    areas = target_areas if target_areas is not None else OBSERVATION_TARGET_AREAS
    target_area_lat_ranges = [
        (float(area.lat_min.to(ureg.deg).magnitude), float(area.lat_max.to(ureg.deg).magnitude))
        for area in areas
    ]
    if np.any(earth_mask):
        earth_pts = hit_xy[earth_mask]
        _lon_deg, lat_deg = batch_disk_xy_rows_km_to_geodetic_deg(earth_pts, ell=WGS84_ELLIPSOID)
        earth_indices = np.nonzero(earth_mask)[0]
        for j, idx in enumerate(earth_indices):
            lat = float(lat_deg[j])
            if any(low <= lat <= high for low, high in target_area_lat_ranges):
                observation_types[int(idx)] = np.int8(target_code)
    return observation_types


def evaluate_fused(
    *,
    sat_pos_xy_km: np.ndarray,
    boresight_dir_unit_xy: np.ndarray,
    altitude: Any,
    earth_radius_km: float,
    sim_time_s: float,
    sim_total_s: float,
    n_bins: int,
    n_clouds: int,
    camera_pixel_ray_samples: int,
    clouds: tuple | None = None,
    camera_kernel_backend: str | None = None,
    n_bins_secondary: int = 0,
    secondary_boresight_dir_unit_xy: np.ndarray | None = None,
    secondary_vertical_fov_rad: float | None = None,
    target_areas: tuple | None = None,
) -> SensorTimestepResult:
    _kernel_backend = camera_kernel_backend if camera_kernel_backend is not None else SIMULATION.camera_kernel_backend
    require_compatible_units(altitude, "meter", "altitude")

    sat_pos_xy_km = np.asarray(sat_pos_xy_km, dtype=float)
    boresight_dir_unit_xy = np.asarray(boresight_dir_unit_xy, dtype=float)
    dir_norm = float(np.linalg.norm(boresight_dir_unit_xy))
    if dir_norm <= 0.0:
        raise ValueError("boresight_dir_unit_xy must be non-zero.")
    boresight_dir_unit_xy = boresight_dir_unit_xy / dir_norm

    cloud_specs = compute_cloud_arc_specs_at_time(
        sim_time_s=sim_time_s,
        sim_total_s=sim_total_s,
        earth_radius_km=earth_radius_km,
        clouds=clouds,
    )

    _hfov, _vfov = calculate_fov_angles()
    primary_vertical_fov_rad = float(_vfov.to(ureg.rad).magnitude)
    half_primary_fov = 0.5 * primary_vertical_fov_rad

    gsd_m = float(calculate_gsd(altitude).to(ureg.m).magnitude)

    left_dir = _rotate_unit_xy(boresight_dir_unit_xy, -half_primary_fov)
    right_dir = _rotate_unit_xy(boresight_dir_unit_xy, +half_primary_fov)
    center_dir = boresight_dir_unit_xy

    t_center = _ray_earth_ellipsoid_intersection_distance_km(sat_pos_xy_km, center_dir)
    t_left = _ray_earth_ellipsoid_intersection_distance_km(sat_pos_xy_km, left_dir)
    t_right = _ray_earth_ellipsoid_intersection_distance_km(sat_pos_xy_km, right_dir)

    nan2 = np.full(2, np.nan, dtype=float)
    if t_center is None or t_left is None or t_right is None:
        ground_center = ground_left = ground_right = nan2.copy()
        center_first_hit_xy_km = np.full((2,), np.nan, dtype=float)
        center_first_hit_is_cloud = False
        center_ray_observation_code = np.int8(OBSERVATION_SPACE)
        cloud_blocked_fraction = float("nan")
        primary_codes = np.full(n_bins, np.int8(OBSERVATION_SPACE), dtype=np.int8)
        scnd_codes = np.empty(0, dtype=np.int8) if n_bins_secondary <= 0 else np.full(
            n_bins_secondary, np.int8(OBSERVATION_SPACE), dtype=np.int8
        )
        scnd_cloud_fraction = 0.0
    else:
        ground_center = sat_pos_xy_km + t_center * center_dir
        ground_left = sat_pos_xy_km + t_left * left_dir
        ground_right = sat_pos_xy_km + t_right * right_dir

        hit_type, _t_hit, center_hit_xy = _first_hit_point_ray_earth_or_clouds(
            ray_origin_xy_km=sat_pos_xy_km,
            ray_dir_unit_xy=center_dir,
            earth_radius_km=earth_radius_km,
            cloud_arc_specs=cloud_specs,
        )
        center_first_hit_is_cloud = bool(hit_type == "cloud")
        if hit_type == "cloud":
            center_ray_observation_code = np.int8(OBSERVATION_CLOUD)
        elif hit_type == "earth":
            center_ray_observation_code = np.int8(OBSERVATION_EARTH)
        else:
            center_ray_observation_code = np.int8(OBSERVATION_SPACE)
        center_first_hit_xy_km = (
            np.full((2,), np.nan, dtype=float) if center_hit_xy is None else np.asarray(center_hit_xy, dtype=float)
        )

        strip_dirs = _strip_pixel_ray_dirs(boresight_dir_unit_xy, camera_pixel_ray_samples)
        primary_dirs = _line_bin_ray_dirs(
            boresight_dir_unit_xy,
            n_bins=n_bins,
            vertical_fov_rad=primary_vertical_fov_rad,
        )
        ray_parts = [strip_dirs, primary_dirs]
        n_strip = strip_dirs.shape[0]
        n_primary = primary_dirs.shape[0]
        n_scnd = 0
        if n_bins_secondary > 0 and secondary_boresight_dir_unit_xy is not None:
            scnd_bore = np.asarray(secondary_boresight_dir_unit_xy, dtype=float)
            scnd_norm = float(np.linalg.norm(scnd_bore))
            scnd_bore = scnd_bore / max(scnd_norm, 1e-15)
            scnd_fov = secondary_vertical_fov_rad
            if scnd_fov is None:
                scnd_fov = primary_vertical_fov_rad
            scnd_dirs = _line_bin_ray_dirs(scnd_bore, n_bins=n_bins_secondary, vertical_fov_rad=float(scnd_fov))
            ray_parts.append(scnd_dirs)
            n_scnd = scnd_dirs.shape[0]

        all_dirs = np.concatenate(ray_parts, axis=0)

        if str(_kernel_backend).lower() == "accelerated":
            hit_types, t_hit, hit_xy = _batch_first_hit_earth_or_clouds(
                ray_origin_xy_km=sat_pos_xy_km,
                ray_dirs_unit_xy=all_dirs,
                cloud_arc_specs=cloud_specs,
            )
        else:
            raise NotImplementedError("Fused fork supports accelerated backend only.")

        strip_types = hit_types[:n_strip]
        t_earth_strip = _batch_earth_hit_distances_km(sat_pos_xy_km, strip_dirs)
        valid_mask = np.isfinite(t_earth_strip)
        valid = int(np.count_nonzero(valid_mask))
        if valid == 0:
            cloud_blocked_fraction = 0.0
        else:
            blocked = (strip_types == 2) & valid_mask
            cloud_blocked_fraction = float(np.count_nonzero(blocked) / max(valid, 1))

        primary_types = hit_types[n_strip : n_strip + n_primary]
        primary_xy = hit_xy[n_strip : n_strip + n_primary]
        primary_codes = _classify_line_from_hits(primary_types, primary_xy, target_areas=target_areas)

        if n_scnd > 0:
            scnd_types = hit_types[n_strip + n_primary :]
            scnd_xy = hit_xy[n_strip + n_primary :]
            scnd_codes = _classify_line_from_hits(scnd_types, scnd_xy, target_areas=target_areas)
            scnd_cloud_fraction = float(np.mean(scnd_codes == np.int8(OBSERVATION_CLOUD)))
        else:
            scnd_codes = np.empty(0, dtype=np.int8)
            scnd_cloud_fraction = 0.0

    cloud_arc_radius_km = np.full((n_clouds,), np.nan, dtype=float)
    cloud_arc_start_rad = np.full((n_clouds,), np.nan, dtype=float)
    cloud_arc_end_rad = np.full((n_clouds,), np.nan, dtype=float)
    for i, spec in enumerate(cloud_specs):
        cloud_arc_radius_km[i] = float(spec["radius_km"])
        cloud_arc_start_rad[i] = float(spec["start_rad"])
        cloud_arc_end_rad[i] = float(spec["end_rad"])

    return SensorTimestepResult(
        camera_observation_line_codes=np.asarray(primary_codes, dtype=np.int8),
        camera_gsd_m=gsd_m,
        camera_ground_left_xy_km=np.asarray(ground_left, dtype=float),
        camera_ground_right_xy_km=np.asarray(ground_right, dtype=float),
        camera_ground_center_xy_km=np.asarray(ground_center, dtype=float),
        camera_center_first_hit_xy_km=center_first_hit_xy_km,
        camera_center_first_hit_is_cloud=center_first_hit_is_cloud,
        camera_center_ray_observation_code=center_ray_observation_code,
        camera_cloud_blocked_fraction=float(cloud_blocked_fraction),
        cloud_arc_radius_km=cloud_arc_radius_km,
        cloud_arc_start_rad=cloud_arc_start_rad,
        cloud_arc_end_rad=cloud_arc_end_rad,
        secondary_camera_observation_line_codes=np.asarray(scnd_codes, dtype=np.int8),
        secondary_camera_cloud_blocked_fraction=scnd_cloud_fraction,
    )
