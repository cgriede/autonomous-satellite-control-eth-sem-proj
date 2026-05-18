"""Stripe polar angles stay aligned across overlap inputs, rim framing, and θ-offset façade."""

import unittest

import numpy as np

from environment_definition.constants.MISSION import LON_GLOBAL, OBSERVATION_TARGET_AREAS, primary_target_stripe_theta_offsets_deg
from environment_definition.constants.SIMULATION import SIMULATION
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.geometry.mission_stripe_disk import (
    geodetic_on_lon_meridian_to_disk_polar_deg,
    primary_stripe_disk_phi_bounds_deg,
)


class GeometryStripeDiskUnificationTest(unittest.TestCase):
    def test_primary_stripe_offsets_are_phi_minus_theta_center(self) -> None:
        phi_lo, phi_hi = primary_stripe_disk_phi_bounds_deg()
        tc_deg = float(SIMULATION.theta_center.to(ureg.deg).magnitude)
        lo, hi = primary_target_stripe_theta_offsets_deg()
        self.assertAlmostEqual(lo, phi_lo - tc_deg, places=9)
        self.assertAlmostEqual(hi, phi_hi - tc_deg, places=9)

    def test_phi_bounds_match_endpoint_latitudes_on_lon_global(self) -> None:
        area = OBSERVATION_TARGET_AREAS[0]
        lon_deg = float(LON_GLOBAL.to(ureg.deg).magnitude)
        lat_s = float(area.lat_min.to(ureg.deg).magnitude)
        lat_n = float(area.lat_max.to(ureg.deg).magnitude)
        phi_s = geodetic_on_lon_meridian_to_disk_polar_deg(lat_deg=lat_s, lon_deg=lon_deg)
        phi_n = geodetic_on_lon_meridian_to_disk_polar_deg(lat_deg=lat_n, lon_deg=lon_deg)
        phi_lo, phi_hi = primary_stripe_disk_phi_bounds_deg()
        self.assertAlmostEqual(phi_lo, min(phi_s, phi_n), places=9)
        self.assertAlmostEqual(phi_hi, max(phi_s, phi_n), places=9)

    def test_render_main_used_absolute_degrees_compat(self) -> None:
        """Absolute rim angles equal φ bounds used by overlap (documentation anchor)."""
        lo, hi = primary_stripe_disk_phi_bounds_deg()
        self.assertLess(lo, hi)
        self.assertTrue(np.isfinite(lo))
        self.assertTrue(np.isfinite(hi))


if __name__ == "__main__":
    unittest.main()
