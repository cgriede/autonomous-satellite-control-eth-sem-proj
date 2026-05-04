import unittest

from environment_definition.constants import SIMULATION
from environment_definition.constants.MISSION import (
    OBSERVATION_TARGET_AREAS,
    los_theta_offsets_deg,
    mission_target_latitude_bounds_deg,
    mission_target_window_deg,
    primary_target_stripe_theta_offsets_deg,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE_ALTITUDE
from utils.flight_geometry.line_of_sight import minimum_contact_angle


class MissionTargetWindowTest(unittest.TestCase):
    def test_latitude_bounds_contain_stripe_and_are_ordered(self):
        margin = float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude)
        lat_low, lat_high = mission_target_latitude_bounds_deg(
            orbit_height=SATELLITE_ALTITUDE,
            margin_deg=margin,
        )
        self.assertLessEqual(lat_low, lat_high)
        area = OBSERVATION_TARGET_AREAS[0]
        s = float(area.lat_min.to(ureg.deg).magnitude)
        e = float(area.lat_max.to(ureg.deg).magnitude)
        smin, smax = min(s, e), max(s, e)
        self.assertLessEqual(lat_low, smin + 1e-9)
        self.assertGreaterEqual(lat_high, smax - 1e-9)

    def test_theta_offsets_are_lat_minus_ninety(self):
        margin = float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude)
        lat_low, lat_high = mission_target_latitude_bounds_deg(
            orbit_height=SATELLITE_ALTITUDE,
            margin_deg=margin,
        )
        start_deg, end_deg = mission_target_window_deg(
            orbit_height=SATELLITE_ALTITUDE,
            margin_deg=margin,
        )
        self.assertAlmostEqual(start_deg, lat_low - 90.0, places=9)
        self.assertAlmostEqual(end_deg, lat_high - 90.0, places=9)

    def test_los_theta_offsets_symmetric_matches_contact_plus_margin(self):
        margin = float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude)
        lo, hi = los_theta_offsets_deg(
            orbit_height=SATELLITE_ALTITUDE,
            margin_deg=margin,
        )
        self.assertAlmostEqual(lo, -hi, places=9)
        half_deg = float(
            minimum_contact_angle(observer_height=0.0 * ureg.km, orbit_height=SATELLITE_ALTITUDE)
            .to(ureg.deg)
            .magnitude
        )
        self.assertAlmostEqual(lo, -(half_deg + margin), places=6)
        self.assertAlmostEqual(hi, half_deg + margin, places=6)

    def test_primary_stripe_theta_offsets_match_lat_minus_ninety(self):
        area = OBSERVATION_TARGET_AREAS[0]
        lo, hi = primary_target_stripe_theta_offsets_deg()
        lat_s = float(area.lat_min.to(ureg.deg).magnitude)
        lat_n = float(area.lat_max.to(ureg.deg).magnitude)
        self.assertAlmostEqual(lo, lat_s - 90.0, places=9)
        self.assertAlmostEqual(hi, lat_n - 90.0, places=9)
        self.assertLess(lo, hi)


if __name__ == "__main__":
    unittest.main()
