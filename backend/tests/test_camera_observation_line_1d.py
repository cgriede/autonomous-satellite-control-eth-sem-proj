import unittest

import numpy as np

from environment_definition.constants import EARTH_RADIUS, OBSERVATION_LINE_NOT_COMPUTED
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.camera_2d import (
    observation_codes_to_ascii_line,
    simulate_camera_observation_line_1d,
)


class CameraObservationLine1DTest(unittest.TestCase):
    def test_boresight_away_from_earth_is_all_space(self):
        earth_radius_km = EARTH_RADIUS.to(ureg.km).magnitude
        altitude = 500 * ureg.km
        alt_km = altitude.to(ureg.km).magnitude

        sat_pos_xy_km = np.array([earth_radius_km + alt_km, 0.0], dtype=float)
        boresight_dir_unit_xy = np.array([1.0, 0.0], dtype=float)  # outward (+x)

        # Target angle doesn't matter here; rays won't hit Earth anyway.
        target_angle_rad = np.pi / 2.0

        result = simulate_camera_observation_line_1d(
            sat_pos_xy_km=sat_pos_xy_km,
            boresight_dir_unit_xy=boresight_dir_unit_xy,
            altitude=altitude,
            earth_radius_km=earth_radius_km,
            sim_time_s=0.0,
            sim_total_s=1.0,
            target_angle_rad=target_angle_rad,
            n_bins=100,
            cloud_arc_specs=[],
            target_code=3,
            earth_code=1,
            space_code=0,
            cloud_code=2,
        )

        self.assertEqual(result.observation_types.shape, (100,))
        self.assertEqual(result.observation_types.dtype, np.int8)
        self.assertTrue(np.all(result.observation_types == 0), "Expected all bins to be space.")

    def test_boresight_to_earth_center_counts_target_bins(self):
        earth_radius_km = EARTH_RADIUS.to(ureg.km).magnitude
        altitude = 500 * ureg.km
        alt_km = altitude.to(ureg.km).magnitude

        sat_pos_xy_km = np.array([earth_radius_km + alt_km, 0.0], dtype=float)
        boresight_dir_unit_xy = np.array([-1.0, 0.0], dtype=float)  # toward origin (nadir)

        # Target point on Earth at theta=pi => (-R, 0).
        target_angle_rad = np.pi

        result = simulate_camera_observation_line_1d(
            sat_pos_xy_km=sat_pos_xy_km,
            boresight_dir_unit_xy=boresight_dir_unit_xy,
            altitude=altitude,
            earth_radius_km=earth_radius_km,
            sim_time_s=0.0,
            sim_total_s=1.0,
            target_angle_rad=target_angle_rad,
            n_bins=100,
            cloud_arc_specs=[],
            target_code=3,
            earth_code=1,
            space_code=0,
            cloud_code=2,
        )

        obs = result.observation_types

        # With empty clouds and nadir-looking boresight, rays should hit Earth for all bins.
        self.assertFalse(np.any(obs == 0), "Expected no space bins when boresight hits Earth.")
        self.assertFalse(np.any(obs == 2), "Expected no cloud bins when cloud_arc_specs is empty.")

        # For even 100-bin sampling with half-bin tolerance, target should cover the two bins
        # immediately around boresight-relative angle 0.
        self.assertEqual(int(obs[49]), 3)
        self.assertEqual(int(obs[50]), 3)

        # Bins one step away should fall outside tolerance and map to Earth.
        self.assertEqual(int(obs[48]), 1)
        self.assertEqual(int(obs[51]), 1)

        # Sanity: only {earth, target} codes appear.
        self.assertTrue(set(int(x) for x in obs.tolist()).issubset({1, 3}))

    def test_observation_codes_to_ascii_line(self):
        arr = np.array([0, 1, 2, 3, OBSERVATION_LINE_NOT_COMPUTED], dtype=np.int8)
        self.assertEqual(observation_codes_to_ascii_line(arr), "-ECX?")

    def test_observation_codes_to_ascii_line_unknown_raises(self):
        with self.assertRaises(ValueError):
            observation_codes_to_ascii_line(np.array([42], dtype=np.int8))


if __name__ == "__main__":
    unittest.main()

