"""Tests for capture reward series derived from SimulationStateSeries."""

from __future__ import annotations

import unittest

import numpy as np

from environment_definition.constants.SIMULATION import OBSERVATION_TARGET
from simulation.capture_reward import (
    applied_capture_reward_series,
    capture_time_windows_s,
    latent_capture_reward_series,
    primary_target_pixel_coverage,
)
from simulation.state_types import SimulationMetadata, SimulationStateSeries


def _minimal_series(*, n: int = 5) -> SimulationStateSeries:
    codes = np.full((n, 4), np.int8(1), dtype=np.int8)
    codes[2, :] = np.int8(OBSERVATION_TARGET)
    quality = np.array([0.1, 0.2, 0.9, 0.3, 0.4], dtype=float)
    cloud = np.zeros(n, dtype=float)
    meta = SimulationMetadata(
        orbit_period_s=90.0,
        omega_rad_s=0.07,
        sim_total_s=float(n - 1) * 0.4,
        sim_dt_s=0.4,
        theta_start_rad=0.0,
        theta_end_rad=0.1,
        sat_theta_start_rad=0.0,
        sat_theta_span_rad=0.1,
        start_angle_deg=-3.0,
        end_angle_deg=3.0,
        take_picture_cmd_steps=(2,),
    )
    z = np.zeros(n, dtype=float)
    empty2d = np.zeros((n, 2), dtype=float)
    empty_cloud = np.full((n, 0), np.nan, dtype=float)
    return SimulationStateSeries(
        t_s=np.arange(n, dtype=float) * 0.4,
        theta_orbit_rad=z,
        radius_km=z + 7000.0,
        body_z_angle_rad=z,
        simulation_reward=z,
        wheel_torque_cmd_nm=z,
        camera_gsd_m=z + 1.0,
        camera_vertical_fov_rad=0.1,
        camera_ground_left_xy_km=empty2d,
        camera_ground_right_xy_km=empty2d,
        camera_ground_center_xy_km=empty2d,
        camera_center_first_hit_xy_km=empty2d,
        camera_center_first_hit_is_cloud=np.zeros(n, dtype=bool),
        camera_center_ray_observation_code=np.zeros(n, dtype=np.int8),
        camera_cloud_blocked_fraction=cloud,
        camera_observation_line_codes=codes,
        sat_subpoint_lat_deg=z,
        sat_subpoint_lon_deg=z,
        sat_altitude_m=z + 500000.0,
        camera_ground_left_lon_lat_deg=empty2d,
        camera_ground_right_lon_lat_deg=empty2d,
        camera_ground_center_lon_lat_deg=empty2d,
        target_area_intersection_ratio=z,
        target_area_novelty_ratio=z,
        cloud_arc_radius_km=empty_cloud,
        cloud_arc_start_rad=empty_cloud,
        cloud_arc_end_rad=empty_cloud,
        metadata=meta,
        camera_image_smear_px=z,
        camera_image_quality=quality,
    )


class CaptureRewardSeriesTest(unittest.TestCase):
    def test_primary_target_pixel_coverage(self) -> None:
        codes = np.array([1, 3, 3, 0], dtype=np.int8)
        self.assertAlmostEqual(primary_target_pixel_coverage(codes), 0.5)

    def test_latent_positive_on_target_frame(self) -> None:
        series = _minimal_series()
        latent = latent_capture_reward_series(series)
        self.assertGreater(latent[2], latent[0])

    def test_applied_spike_only_on_cmd_step(self) -> None:
        series = _minimal_series()
        applied = applied_capture_reward_series(series, cmd_steps=(2,))
        self.assertGreater(applied[2], 0.0)
        self.assertEqual(applied[0], 0.0)
        self.assertAlmostEqual(applied[2], latent_capture_reward_series(series)[2])

    def test_capture_time_windows(self) -> None:
        series = _minimal_series()
        windows = capture_time_windows_s(series, (2,))
        self.assertEqual(len(windows), 1)
        t0, t1 = windows[0]
        self.assertAlmostEqual(t0, 0.8)
        self.assertGreater(t1, t0)


if __name__ == "__main__":
    unittest.main()
