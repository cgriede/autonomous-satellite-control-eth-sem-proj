import unittest

import numpy as np

from environment_definition.constants import EARTH_RADIUS, UREG as ureg
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE_ALTITUDE
from simulation.camera_2d import (
    compute_cloud_arc_specs_at_time,
    simulate_camera_observation_line_1d,
    simulate_camera_strip_2d,
)


class CameraKernelBackendParityTest(unittest.TestCase):
    def test_strip_cloud_fraction_matches_python_backend(self):
        sat_xy = np.array([6800.0, 120.0], dtype=float)
        bore = np.array([-1.0, 0.05], dtype=float)
        earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
        py = simulate_camera_strip_2d(
            sat_pos_xy_km=sat_xy,
            boresight_dir_unit_xy=bore,
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=earth_r,
            sim_time_s=12.0,
            sim_total_s=100.0,
            pixel_ray_samples=96,
            kernel_backend="python",
        )
        acc = simulate_camera_strip_2d(
            sat_pos_xy_km=sat_xy,
            boresight_dir_unit_xy=bore,
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=earth_r,
            sim_time_s=12.0,
            sim_total_s=100.0,
            pixel_ray_samples=96,
            kernel_backend="accelerated",
        )
        self.assertAlmostEqual(py.cloud_blocked_fraction, acc.cloud_blocked_fraction, places=8)

    def test_observation_line_codes_match_python_backend(self):
        sat_xy = np.array([6800.0, 120.0], dtype=float)
        bore = np.array([-1.0, 0.02], dtype=float)
        earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
        cloud_specs = compute_cloud_arc_specs_at_time(
            sim_time_s=20.0,
            sim_total_s=200.0,
            earth_radius_km=earth_r,
        )
        py = simulate_camera_observation_line_1d(
            sat_pos_xy_km=sat_xy,
            boresight_dir_unit_xy=bore,
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=earth_r,
            sim_time_s=20.0,
            sim_total_s=200.0,
            n_bins=80,
            cloud_arc_specs=cloud_specs,
            kernel_backend="python",
        )
        acc = simulate_camera_observation_line_1d(
            sat_pos_xy_km=sat_xy,
            boresight_dir_unit_xy=bore,
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=earth_r,
            sim_time_s=20.0,
            sim_total_s=200.0,
            n_bins=80,
            cloud_arc_specs=cloud_specs,
            kernel_backend="accelerated",
        )
        np.testing.assert_array_equal(py.observation_types, acc.observation_types)


if __name__ == "__main__":
    unittest.main()
