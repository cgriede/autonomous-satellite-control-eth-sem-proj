import unittest
from unittest.mock import patch

import numpy as np

from environment_definition.constants import EARTH_RADIUS, OBSERVATION_LINE_NOT_COMPUTED
from environment_definition.constants.MISSION import ObservationTargetArea
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

        result = simulate_camera_observation_line_1d(
            sat_pos_xy_km=sat_pos_xy_km,
            boresight_dir_unit_xy=boresight_dir_unit_xy,
            altitude=altitude,
            earth_radius_km=earth_radius_km,
            sim_time_s=0.0,
            sim_total_s=1.0,
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

        with patch(
            "simulation.camera_2d.OBSERVATION_TARGET_AREAS",
            (
                ObservationTargetArea(
                    lat_min=-1.0 * ureg.deg,
                    lat_max=1.0 * ureg.deg,
                    label="test_band",
                ),
            ),
        ):
            result = simulate_camera_observation_line_1d(
                sat_pos_xy_km=sat_pos_xy_km,
                boresight_dir_unit_xy=boresight_dir_unit_xy,
                altitude=altitude,
                earth_radius_km=earth_radius_km,
                sim_time_s=0.0,
                sim_total_s=1.0,
                n_bins=100,
                cloud_arc_specs=[],
                target_code=3,
                earth_code=1,
                space_code=0,
                cloud_code=2,
            )

        obs = result.observation_types

        self.assertFalse(np.any(obs == 0), "Expected no space bins when boresight hits Earth.")
        self.assertFalse(np.any(obs == 2), "Expected no cloud bins when cloud_arc_specs is empty.")
        self.assertTrue(np.any(obs == 3), "Expected at least one target bin inside the latitude band.")
        self.assertTrue(set(int(x) for x in obs.tolist()).issubset({1, 3}))

    def test_boresight_to_earth_center_outside_target_band_is_earth(self):
        earth_radius_km = EARTH_RADIUS.to(ureg.km).magnitude
        altitude = 500 * ureg.km
        alt_km = altitude.to(ureg.km).magnitude

        sat_pos_xy_km = np.array([earth_radius_km + alt_km, 0.0], dtype=float)
        boresight_dir_unit_xy = np.array([-1.0, 0.0], dtype=float)

        with patch(
            "simulation.camera_2d.OBSERVATION_TARGET_AREAS",
            (
                ObservationTargetArea(
                    lat_min=10.0 * ureg.deg,
                    lat_max=20.0 * ureg.deg,
                    label="test_band",
                ),
            ),
        ):
            result = simulate_camera_observation_line_1d(
                sat_pos_xy_km=sat_pos_xy_km,
                boresight_dir_unit_xy=boresight_dir_unit_xy,
                altitude=altitude,
                earth_radius_km=earth_radius_km,
                sim_time_s=0.0,
                sim_total_s=1.0,
                n_bins=100,
                cloud_arc_specs=[],
                target_code=3,
                earth_code=1,
                space_code=0,
                cloud_code=2,
            )

        obs = result.observation_types
        self.assertFalse(np.any(obs == 3), "Expected no target bins outside the latitude band.")
        self.assertTrue(np.all(obs == 1), "Expected all Earth hits to remain Earth outside the band.")

    def test_observation_codes_to_ascii_line(self):
        arr = np.array([0, 1, 2, 3, OBSERVATION_LINE_NOT_COMPUTED], dtype=np.int8)
        self.assertEqual(observation_codes_to_ascii_line(arr), "-EC0?")

    def test_observation_codes_to_ascii_line_unknown_raises(self):
        with self.assertRaises(ValueError):
            observation_codes_to_ascii_line(np.array([42], dtype=np.int8))


if __name__ == "__main__":
    unittest.main()

