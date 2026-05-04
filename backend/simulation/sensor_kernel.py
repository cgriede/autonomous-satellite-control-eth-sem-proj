from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from environment_definition.constants.SIMULATION import FIXED_GROUND_CONE_HIT_EARTH, SIMULATION

from .camera_2d import (
    OBSERVATION_EARTH,
    OBSERVATION_SPACE,
    compute_cloud_arc_specs_at_time,
    simulate_camera_observation_line_1d,
    simulate_camera_strip_2d,
)


def fixed_ground_codes_from_observation_line(
    *,
    observation_codes: np.ndarray,
    rel_angles_rad: np.ndarray,
    center_ray_code: np.int8,
) -> np.ndarray:
    fixed_codes = np.asarray(observation_codes, dtype=np.int8).copy()
    if fixed_codes.ndim != 1:
        raise ValueError("observation_codes must be a 1D array.")
    if rel_angles_rad.shape != fixed_codes.shape:
        raise ValueError("rel_angles_rad shape must match observation_codes shape.")
    fixed_codes[fixed_codes == np.int8(OBSERVATION_SPACE)] = np.int8(OBSERVATION_EARTH)
    if int(center_ray_code) == int(OBSERVATION_EARTH):
        center_idx = int(np.argmin(np.abs(np.asarray(rel_angles_rad, dtype=float))))
        fixed_codes[center_idx] = np.int8(FIXED_GROUND_CONE_HIT_EARTH)
    return fixed_codes


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
    fixed_ground_line_codes: np.ndarray
    cloud_arc_radius_km: np.ndarray
    cloud_arc_start_rad: np.ndarray
    cloud_arc_end_rad: np.ndarray


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
        camera_pixel_ray_samples: int,
    ) -> SensorTimestepResult:
        cloud_specs = compute_cloud_arc_specs_at_time(
            sim_time_s=sim_time_s,
            sim_total_s=sim_total_s,
            earth_radius_km=earth_radius_km,
        )
        cam = simulate_camera_strip_2d(
            sat_pos_xy_km=sat_pos_xy_km,
            boresight_dir_unit_xy=boresight_dir_unit_xy,
            altitude=altitude,
            earth_radius_km=earth_radius_km,
            sim_time_s=sim_time_s,
            sim_total_s=sim_total_s,
            pixel_ray_samples=camera_pixel_ray_samples,
            kernel_backend=SIMULATION.camera_kernel_backend,
        )
        center_first_hit_xy_km = np.full((2,), np.nan, dtype=float)
        if cam.center_first_hit_xy_km is not None:
            center_first_hit_xy_km = np.asarray(cam.center_first_hit_xy_km, dtype=float)

        line_res = simulate_camera_observation_line_1d(
            sat_pos_xy_km=sat_pos_xy_km,
            boresight_dir_unit_xy=boresight_dir_unit_xy,
            altitude=altitude,
            earth_radius_km=earth_radius_km,
            sim_time_s=sim_time_s,
            sim_total_s=sim_total_s,
            n_bins=n_bins,
            cloud_arc_specs=cloud_specs,
            kernel_backend=SIMULATION.camera_kernel_backend,
        )
        fixed_codes = fixed_ground_codes_from_observation_line(
            observation_codes=line_res.observation_types,
            rel_angles_rad=line_res.bin_ray_angles_rel_boresight_rad,
            center_ray_code=np.int8(cam.center_ray_observation_code),
        )

        cloud_arc_radius_km = np.full((n_clouds,), np.nan, dtype=float)
        cloud_arc_start_rad = np.full((n_clouds,), np.nan, dtype=float)
        cloud_arc_end_rad = np.full((n_clouds,), np.nan, dtype=float)
        for i, spec in enumerate(cloud_specs):
            cloud_arc_radius_km[i] = float(spec["radius_km"])
            cloud_arc_start_rad[i] = float(spec["start_rad"])
            cloud_arc_end_rad[i] = float(spec["end_rad"])

        return SensorTimestepResult(
            #state we feed into controller
            camera_observation_line_codes=np.asarray(line_res.observation_types, dtype=np.int8),
            #metadata we include in timestep state but don't feed into controller
            camera_gsd_m=float(cam.gsd_m),
            camera_ground_left_xy_km=np.asarray(cam.ground_left_xy_km, dtype=float),
            camera_ground_right_xy_km=np.asarray(cam.ground_right_xy_km, dtype=float),
            camera_ground_center_xy_km=np.asarray(cam.ground_center_xy_km, dtype=float),
            camera_center_first_hit_xy_km=center_first_hit_xy_km,
            camera_center_first_hit_is_cloud=bool(cam.center_first_hit_is_cloud),
            camera_center_ray_observation_code=np.int8(cam.center_ray_observation_code),
            camera_cloud_blocked_fraction=float(cam.cloud_blocked_fraction),
            fixed_ground_line_codes=fixed_codes,
            cloud_arc_radius_km=cloud_arc_radius_km,
            cloud_arc_start_rad=cloud_arc_start_rad,
            cloud_arc_end_rad=cloud_arc_end_rad,
        )
