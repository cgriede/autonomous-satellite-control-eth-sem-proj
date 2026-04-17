import unittest

import numpy as np

from environment_definition.constants import (
    EARTH_GRAVITATIONAL_PARAMETER,
    EARTH_RADIUS,
    SIMULATION,
    UREG as ureg,
)
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE, SATELLITE_ALTITUDE
from simulation.observation_line_constants import (
    FIXED_GROUND_CONE_HIT_EARTH,
    OBSERVATION_CLOUD,
    OBSERVATION_EARTH,
    OBSERVATION_SPACE,
    OBSERVATION_TARGET,
)
from simulation.run_simulation import run_simulation
from simulation.run_simulation import _fixed_ground_codes_from_observation_line


class FixedGroundLineCodesTest(unittest.TestCase):
    def test_fixed_ground_conversion_remaps_space_to_earth(self):
        observation = np.array(
            [
                OBSERVATION_SPACE,
                OBSERVATION_EARTH,
                OBSERVATION_CLOUD,
                OBSERVATION_TARGET,
                OBSERVATION_SPACE,
            ],
            dtype=np.int8,
        )
        rel = np.array([-0.4, -0.1, 0.0, 0.2, 0.5], dtype=float)

        fixed_codes = _fixed_ground_codes_from_observation_line(
            observation_codes=observation,
            rel_angles_rad=rel,
            center_ray_code=np.int8(OBSERVATION_CLOUD),
        )

        self.assertFalse(np.any(fixed_codes == np.int8(OBSERVATION_SPACE)))
        self.assertEqual(int(fixed_codes[0]), int(OBSERVATION_EARTH))
        self.assertEqual(int(fixed_codes[4]), int(OBSERVATION_EARTH))
        self.assertEqual(int(fixed_codes[2]), int(OBSERVATION_CLOUD))
        self.assertEqual(int(fixed_codes[3]), int(OBSERVATION_TARGET))

    def test_fixed_ground_s_marker_only_when_center_hits_earth(self):
        observation = np.array([OBSERVATION_EARTH, OBSERVATION_EARTH, OBSERVATION_EARTH], dtype=np.int8)
        rel = np.array([-0.2, 0.0, 0.2], dtype=float)

        with_s = _fixed_ground_codes_from_observation_line(
            observation_codes=observation,
            rel_angles_rad=rel,
            center_ray_code=np.int8(OBSERVATION_EARTH),
        )
        without_s = _fixed_ground_codes_from_observation_line(
            observation_codes=observation,
            rel_angles_rad=rel,
            center_ray_code=np.int8(OBSERVATION_CLOUD),
        )

        self.assertEqual(
            int(np.sum(with_s == np.int8(FIXED_GROUND_CONE_HIT_EARTH))),
            1,
        )
        self.assertEqual(
            int(np.sum(without_s == np.int8(FIXED_GROUND_CONE_HIT_EARTH))),
            0,
        )

    def test_fixed_ground_line_codes_shape_dtype_and_values(self):
        theta_center = SIMULATION.theta_center.to(ureg.rad).magnitude
        earth_radius_km = EARTH_RADIUS.to(ureg.km).magnitude
        alpha = np.arccos(earth_radius_km / (earth_radius_km + SATELLITE_ALTITUDE.to(ureg.km).magnitude))
        contact_half_angle_deg = np.rad2deg(alpha)
        margin_deg = SIMULATION.contact_margin_angle.to(ureg.deg).magnitude

        series = run_simulation(
            earth_radius=EARTH_RADIUS,
            earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
            satellite=SATELLITE,
            satellite_altitude=SATELLITE_ALTITUDE,
            theta_center_rad=float(theta_center),
            start_angle_deg=float(-(contact_half_angle_deg + margin_deg)),
            end_angle_deg=float(contact_half_angle_deg + margin_deg),
            sat_motion_span_scale=float(SIMULATION.sat_motion_span_scale),
            num_frames=8,
            sat_z_offset_deg=float(SIMULATION.sat_z_offset.to(ureg.deg).magnitude),
            ureg=ureg,
            observer_target_angle_rad=float(np.arctan2(earth_radius_km, 0.0)),
            camera_pixel_ray_samples=16,
            camera_observation_line_n_bins=32,
        )

        fixed_codes = series.fixed_ground_line_codes
        self.assertEqual(fixed_codes.shape, (8, 32))
        self.assertEqual(fixed_codes.dtype, np.int8)

        allowed = {
            int(OBSERVATION_EARTH),
            int(OBSERVATION_CLOUD),
            int(OBSERVATION_TARGET),
            int(FIXED_GROUND_CONE_HIT_EARTH),
        }
        observed = set(int(v) for v in np.unique(fixed_codes).tolist())
        self.assertTrue(observed.issubset(allowed), msg=f"Unexpected fixed-ground codes: {observed - allowed}")

        cone_hit_count_per_frame = np.sum(
            fixed_codes == np.int8(FIXED_GROUND_CONE_HIT_EARTH),
            axis=1,
        )
        self.assertTrue(np.all(cone_hit_count_per_frame <= 1))
        self.assertFalse(np.any(fixed_codes == np.int8(OBSERVATION_SPACE)))


if __name__ == "__main__":
    unittest.main()
