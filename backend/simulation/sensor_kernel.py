from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from environment_definition.constants.EARTH import WGS84_ELLIPSOID
from environment_definition.constants.MISSION import OBSERVATION_TARGET_AREAS
from environment_definition.constants.SIMULATION import (
    OBSERVATION_CLOUD,
    OBSERVATION_EARTH,
    OBSERVATION_SPACE,
    SIMULATION,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.constants.observation_codes import observation_target_code_for_index
from utils.geometry.mission_stripe_disk import (
    batch_geodetic_target_area_indices,
    target_areas_track_offset_ranges_deg,
)
from utils.geometry.orbit_disk_wgs84 import batch_disk_xy_rows_km_to_geodetic_deg
from utils.units.require_compatible_unit import require_compatible_units

from .camera_2d import (
    _batch_first_hit_earth_or_clouds,
    _ray_earth_ellipsoid_intersection_distance_km,
    _rotate_unit_xy,
    _rotate_unit_xy_batch,
    calculate_fov_angles,
    compute_cloud_arc_specs_at_time,
    effective_gsd_m,
)

_FOV_CACHE: tuple[Any, Any] | None = None
_BIN_ANGLES_CACHE: dict[tuple[int, float], np.ndarray] = {}


def _primary_vertical_fov_rad() -> float:
    global _FOV_CACHE
    if _FOV_CACHE is None:
        _FOV_CACHE = calculate_fov_angles()
    return float(_FOV_CACHE[1].to(ureg.rad).magnitude)


def _cached_bin_ray_angles_rel_boresight(n_bins: int, vertical_fov_rad: float) -> np.ndarray:
    key = (int(n_bins), float(vertical_fov_rad))
    cached = _BIN_ANGLES_CACHE.get(key)
    if cached is None:
        half_vertical_fov_rad = 0.5 * vertical_fov_rad
        half_bin = vertical_fov_rad / (2.0 * n_bins)
        cached = np.linspace(
            -half_vertical_fov_rad + half_bin,
            +half_vertical_fov_rad - half_bin,
            n_bins,
            dtype=float,
        )
        _BIN_ANGLES_CACHE[key] = cached
    return cached


@dataclass(frozen=True)
class SensorTimestepResult:
    camera_gsd_m: float
    camera_ground_left_xy_km: np.ndarray
    camera_ground_right_xy_km: np.ndarray
    camera_ground_center_xy_km: np.ndarray
    camera_center_first_hit_xy_km: np.ndarray
    camera_center_first_hit_is_cloud: bool
    camera_center_ray_observation_code: np.int8
    camera_cloud_blocked_fraction: float
    camera_observation_line_codes: np.ndarray
    cloud_arc_radius_km: np.ndarray
    cloud_arc_start_rad: np.ndarray
    cloud_arc_end_rad: np.ndarray
    secondary_camera_observation_line_codes: np.ndarray
    secondary_camera_cloud_blocked_fraction: float


def _line_bin_ray_dirs(
    boresight_dir_unit_xy: np.ndarray,
    *,
    n_bins: int,
    vertical_fov_rad: float,
) -> np.ndarray:
    bin_ray_angles = _cached_bin_ray_angles_rel_boresight(n_bins, vertical_fov_rad)
    return _rotate_unit_xy_batch(boresight_dir_unit_xy, bin_ray_angles)


def _cloud_blocked_fraction_from_earth_valid_hits(
    hit_types: np.ndarray,
    earth_valid_mask: np.ndarray,
) -> float:
    """Fraction of rays with a valid Earth intersection whose first hit is cloud."""
    valid = int(np.count_nonzero(earth_valid_mask))
    if valid == 0:
        return 0.0
    blocked = (hit_types == 2) & earth_valid_mask
    return float(np.count_nonzero(blocked) / max(valid, 1))


def _cloud_blocked_fraction_from_hit_types(
    hit_types: np.ndarray,
    *,
    sat_pos_xy_km: np.ndarray,
    ray_dirs: np.ndarray,
    earth_valid_mask: np.ndarray | None = None,
) -> float:
    if earth_valid_mask is not None:
        return _cloud_blocked_fraction_from_earth_valid_hits(hit_types, earth_valid_mask)
    from .camera_2d import _batch_earth_hit_distances_km

    t_earth = _batch_earth_hit_distances_km(sat_pos_xy_km, ray_dirs)
    valid_mask = np.isfinite(t_earth)
    return _cloud_blocked_fraction_from_earth_valid_hits(hit_types, valid_mask)


def _classify_line_from_hits(
    hit_types: np.ndarray,
    hit_xy: np.ndarray,
    *,
    target_offset_ranges: tuple[tuple[float, float], ...],
    space_code: int = 0,
    earth_code: int = 1,
    cloud_code: int = 2,
) -> np.ndarray:
    n = hit_types.shape[0]
    observation_types = np.full(n, int(space_code), dtype=np.int8)
    observation_types[hit_types == 2] = np.int8(cloud_code)
    earth_mask = hit_types == 1
    observation_types[earth_mask] = np.int8(earth_code)

    if np.any(earth_mask):
        earth_pts = hit_xy[earth_mask]
        lon_deg, lat_deg = batch_disk_xy_rows_km_to_geodetic_deg(earth_pts, ell=WGS84_ELLIPSOID)
        target_indices = batch_geodetic_target_area_indices(
            lon_deg,
            lat_deg,
            target_offset_ranges,
        )
        earth_indices = np.nonzero(earth_mask)[0]
        for j, idx in enumerate(earth_indices):
            t_idx = int(target_indices[j])
            if t_idx >= 0:
                observation_types[int(idx)] = observation_target_code_for_index(t_idx)
    return observation_types


def _resolve_cloud_arc_rows(
    cloud_arc_specs: list[dict[str, float]] | None,
    *,
    cloud_arc_radius_km: np.ndarray | None,
    cloud_arc_start_rad: np.ndarray | None,
    cloud_arc_end_rad: np.ndarray | None,
    n_clouds: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if cloud_arc_radius_km is not None:
        radius_km = np.asarray(cloud_arc_radius_km, dtype=float).reshape(-1)
        start_rad = np.asarray(cloud_arc_start_rad, dtype=float).reshape(-1)
        end_rad = np.asarray(cloud_arc_end_rad, dtype=float).reshape(-1)
        return radius_km, start_rad, end_rad
    if cloud_arc_specs is None:
        return (
            np.full((n_clouds,), np.nan, dtype=float),
            np.full((n_clouds,), np.nan, dtype=float),
            np.full((n_clouds,), np.nan, dtype=float),
        )
    radius_km = np.full((n_clouds,), np.nan, dtype=float)
    start_rad = np.full((n_clouds,), np.nan, dtype=float)
    end_rad = np.full((n_clouds,), np.nan, dtype=float)
    for i, spec in enumerate(cloud_arc_specs):
        if i >= n_clouds:
            break
        radius_km[i] = float(spec["radius_km"])
        start_rad[i] = float(spec["start_rad"])
        end_rad[i] = float(spec["end_rad"])
    return radius_km, start_rad, end_rad


def _evaluate_sensors(
    *,
    sat_pos_xy_km: np.ndarray,
    boresight_dir_unit_xy: np.ndarray,
    altitude: Any,
    earth_radius_km: float,
    n_bins: int,
    n_clouds: int,
    cloud_arc_specs: list[dict[str, float]] | None,
    cloud_arc_radius_km: np.ndarray | None,
    cloud_arc_start_rad: np.ndarray | None,
    cloud_arc_end_rad: np.ndarray | None,
    n_bins_secondary: int,
    secondary_boresight_dir_unit_xy: np.ndarray | None,
    secondary_vertical_fov_rad: float | None,
    target_offset_ranges: tuple[tuple[float, float], ...],
) -> SensorTimestepResult:
    _ = earth_radius_km
    primary_vertical_fov_rad = _primary_vertical_fov_rad()
    half_primary_fov = 0.5 * primary_vertical_fov_rad
    gsd_m = effective_gsd_m(altitude, sat_pos_xy_km, boresight_dir_unit_xy)

    left_dir = _rotate_unit_xy(boresight_dir_unit_xy, -half_primary_fov)
    right_dir = _rotate_unit_xy(boresight_dir_unit_xy, +half_primary_fov)
    center_dir = boresight_dir_unit_xy

    t_center = _ray_earth_ellipsoid_intersection_distance_km(sat_pos_xy_km, center_dir)
    t_left = _ray_earth_ellipsoid_intersection_distance_km(sat_pos_xy_km, left_dir)
    t_right = _ray_earth_ellipsoid_intersection_distance_km(sat_pos_xy_km, right_dir)

    radius_row, start_row, end_row = _resolve_cloud_arc_rows(
        cloud_arc_specs,
        cloud_arc_radius_km=cloud_arc_radius_km,
        cloud_arc_start_rad=cloud_arc_start_rad,
        cloud_arc_end_rad=cloud_arc_end_rad,
        n_clouds=n_clouds,
    )

    nan2 = np.full(2, np.nan, dtype=float)
    scnd_cloud_fraction = 0.0
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
    else:
        ground_center = sat_pos_xy_km + t_center * center_dir
        ground_left = sat_pos_xy_km + t_left * left_dir
        ground_right = sat_pos_xy_km + t_right * right_dir

        primary_dirs = _line_bin_ray_dirs(
            boresight_dir_unit_xy,
            n_bins=n_bins,
            vertical_fov_rad=primary_vertical_fov_rad,
        )
        ray_parts = [primary_dirs]
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
        hit_types, _t_hit, hit_xy, earth_valid = _batch_first_hit_earth_or_clouds(
            ray_origin_xy_km=sat_pos_xy_km,
            ray_dirs_unit_xy=all_dirs,
            cloud_arc_radius_km=radius_row,
            cloud_arc_start_rad=start_row,
            cloud_arc_end_rad=end_row,
        )

        primary_types = hit_types[:n_primary]
        primary_xy = hit_xy[:n_primary]
        primary_codes = _classify_line_from_hits(
            primary_types,
            primary_xy,
            target_offset_ranges=target_offset_ranges,
        )
        cloud_blocked_fraction = _cloud_blocked_fraction_from_earth_valid_hits(
            primary_types,
            earth_valid[:n_primary],
        )

        center_idx = n_primary // 2
        center_ray_observation_code = np.int8(primary_codes[center_idx])
        center_first_hit_is_cloud = bool(primary_types[center_idx] == 2)
        center_hit_xy = primary_xy[center_idx]
        center_first_hit_xy_km = (
            np.full((2,), np.nan, dtype=float)
            if not np.all(np.isfinite(center_hit_xy))
            else np.asarray(center_hit_xy, dtype=float)
        )

        if n_scnd > 0:
            scnd_types = hit_types[n_primary:]
            scnd_xy = hit_xy[n_primary:]
            scnd_codes = _classify_line_from_hits(
                scnd_types,
                scnd_xy,
                target_offset_ranges=target_offset_ranges,
            )
            scnd_cloud_fraction = _cloud_blocked_fraction_from_earth_valid_hits(
                scnd_types,
                earth_valid[n_primary:],
            )
        else:
            scnd_codes = np.empty(0, dtype=np.int8)
            scnd_cloud_fraction = 0.0

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
        cloud_arc_radius_km=radius_row,
        cloud_arc_start_rad=start_row,
        cloud_arc_end_rad=end_row,
        secondary_camera_observation_line_codes=np.asarray(scnd_codes, dtype=np.int8),
        secondary_camera_cloud_blocked_fraction=float(scnd_cloud_fraction),
    )


class SensorKernel:
    @staticmethod
    def evaluate(
        *,
        sat_pos_xy_km: np.ndarray,
        boresight_dir_unit_xy: np.ndarray,
        altitude: Any,
        earth_radius_km: float,
        sim_time_s: float,
        sim_total_s: float,
        n_bins: int,
        n_clouds: int,
        clouds: tuple | None = None,
        camera_kernel_backend: str | None = None,
        n_bins_secondary: int = 0,
        secondary_boresight_dir_unit_xy: np.ndarray | None = None,
        secondary_vertical_fov_rad: float | None = None,
        target_areas: tuple | None = None,
        target_offset_ranges: tuple[tuple[float, float], ...] | None = None,
        cloud_arc_specs: list[dict[str, float]] | None = None,
        cloud_arc_radius_km: np.ndarray | None = None,
        cloud_arc_start_rad: np.ndarray | None = None,
        cloud_arc_end_rad: np.ndarray | None = None,
    ) -> SensorTimestepResult:
        _ = camera_kernel_backend if camera_kernel_backend is not None else SIMULATION.camera_kernel_backend
        require_compatible_units(altitude, "meter", "altitude")

        sat_pos_xy_km = np.asarray(sat_pos_xy_km, dtype=float)
        boresight_dir_unit_xy = np.asarray(boresight_dir_unit_xy, dtype=float)
        dir_norm = float(np.linalg.norm(boresight_dir_unit_xy))
        if dir_norm <= 0.0:
            raise ValueError("boresight_dir_unit_xy must be non-zero.")
        boresight_dir_unit_xy = boresight_dir_unit_xy / dir_norm

        if cloud_arc_radius_km is not None:
            cloud_specs = None
        elif cloud_arc_specs is not None:
            cloud_specs = cloud_arc_specs
        else:
            cloud_specs = compute_cloud_arc_specs_at_time(
                sim_time_s=sim_time_s,
                sim_total_s=sim_total_s,
                earth_radius_km=earth_radius_km,
                clouds=clouds,
            )

        areas = target_areas if target_areas is not None else OBSERVATION_TARGET_AREAS
        if target_offset_ranges is None:
            target_offset_ranges = target_areas_track_offset_ranges_deg(areas)

        return _evaluate_sensors(
            sat_pos_xy_km=sat_pos_xy_km,
            boresight_dir_unit_xy=boresight_dir_unit_xy,
            altitude=altitude,
            earth_radius_km=earth_radius_km,
            n_bins=n_bins,
            n_clouds=n_clouds,
            cloud_arc_specs=cloud_specs,
            cloud_arc_radius_km=cloud_arc_radius_km,
            cloud_arc_start_rad=cloud_arc_start_rad,
            cloud_arc_end_rad=cloud_arc_end_rad,
            n_bins_secondary=n_bins_secondary,
            secondary_boresight_dir_unit_xy=secondary_boresight_dir_unit_xy,
            secondary_vertical_fov_rad=secondary_vertical_fov_rad,
            target_offset_ranges=target_offset_ranges,
        )
