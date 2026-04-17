import unittest

import numpy as np

from environment_definition.constants import EARTH_RADIUS
from environment_definition.constants.SATELLITE import (
    FOCAL_LENGTH,
    N_PIXELS_Y,
    PIXEL_SIZE,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.camera_2d import (
    OBSERVATION_CLOUD,
    OBSERVATION_EARTH,
    OBSERVATION_SPACE,
    calculate_fov_angles,
    calculate_gsd,
    simulate_camera_strip_2d,
)


class CameraOptics2DTest(unittest.TestCase):
    def test_calculate_gsd_uses_required_formula(self):
        altitude = 500 * ureg.km
        gsd = calculate_gsd(altitude)
        expected = (PIXEL_SIZE * altitude / FOCAL_LENGTH).to(ureg.m)
        self.assertAlmostEqual(gsd.to(ureg.m).magnitude, expected.to(ureg.m).magnitude, places=12)
        # Qualitative check against the design target (~1.5 m)
        self.assertAlmostEqual(gsd.to(ureg.m).magnitude, 1.5, places=2)

    def test_calculate_fov_angles_match_design_values(self):
        horizontal_fov, vertical_fov = calculate_fov_angles()
        self.assertAlmostEqual(horizontal_fov.to(ureg.deg).magnitude, 1.61, places=2)
        self.assertAlmostEqual(vertical_fov.to(ureg.deg).magnitude, 1.20, places=2)

    def test_swath_height_flat_from_gsd(self):
        altitude = 500 * ureg.km
        gsd = calculate_gsd(altitude)
        swath_height = (N_PIXELS_Y * gsd).to(ureg.km)
        self.assertAlmostEqual(swath_height.magnitude, 10.5, places=1)

    def test_footprint_endpoints_nadir_reasonable(self):
        altitude = 500 * ureg.km
        earth_radius_km = EARTH_RADIUS.to(ureg.km).magnitude
        sat_radius_km = earth_radius_km + altitude.to(ureg.km).magnitude

        # Place the satellite on the +x axis; nadir points towards the origin => boresight = (-1,0)
        sat_pos_xy_km = np.array([sat_radius_km, 0.0], dtype=float)
        boresight_dir_unit_xy = np.array([-1.0, 0.0], dtype=float)

        result = simulate_camera_strip_2d(
            sat_pos_xy_km=sat_pos_xy_km,
            boresight_dir_unit_xy=boresight_dir_unit_xy,
            altitude=altitude,
            earth_radius_km=earth_radius_km,
            sim_time_s=0.0,
            sim_total_s=1.0,
            pixel_ray_samples=200,
        )

        ground_edge_distance_km = float(np.linalg.norm(result.ground_left_xy_km - result.ground_right_xy_km))
        self.assertAlmostEqual(ground_edge_distance_km, result.swath_height_flat_km, places=1)
        self.assertIn(
            result.center_ray_observation_code,
            (OBSERVATION_EARTH, OBSERVATION_CLOUD),
            "nadir strip should see Earth or cloud on center ray",
        )

    def test_strip_footprint_missing_earth_is_space_not_error(self):
        altitude = 500 * ureg.km
        earth_radius_km = EARTH_RADIUS.to(ureg.km).magnitude
        sat_radius_km = earth_radius_km + altitude.to(ureg.km).magnitude
        sat_pos_xy_km = np.array([sat_radius_km, 0.0], dtype=float)
        # Boresight away from Earth: no Earth intersection for footprint rays.
        boresight_dir_unit_xy = np.array([1.0, 0.0], dtype=float)
        result = simulate_camera_strip_2d(
            sat_pos_xy_km=sat_pos_xy_km,
            boresight_dir_unit_xy=boresight_dir_unit_xy,
            altitude=altitude,
            earth_radius_km=earth_radius_km,
            sim_time_s=0.0,
            sim_total_s=1.0,
            pixel_ray_samples=32,
        )
        self.assertEqual(result.center_ray_observation_code, OBSERVATION_SPACE)
        self.assertTrue(np.all(np.isnan(result.ground_center_xy_km)))
        self.assertFalse(result.center_first_hit_is_cloud)


if __name__ == "__main__":
    unittest.main()

