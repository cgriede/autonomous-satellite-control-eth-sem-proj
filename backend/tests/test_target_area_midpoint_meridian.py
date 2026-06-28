"""Target view anchors must use descending-meridian longitude past the pole."""

from __future__ import annotations

import unittest

from environment_definition.constants import ureg
from environment_definition.constants.MISSION import LON_GLOBAL
from utils.geometry.mission_stripe_disk import (
    observation_target_area_midpoint_geodetic_deg,
    target_areas_midpoint_disk_xy_km_on_sphere,
)
from utils.geometry.orbit_disk_polar_meridian import disk_phi_deg_from_geodetic_deg
from utils.geometry.polar_meridian_track import build_target_grid_polar_meridian


class TargetAreaMidpointMeridianTest(unittest.TestCase):
    def test_descending_leg_anchor_uses_opposite_meridian(self) -> None:
        segments = build_target_grid_polar_meridian(
            anchor_lat=80 * ureg.deg,
            anchor_lon=LON_GLOBAL,
            n_targets=50,
            target_size=15 * ureg.kilometer,
            spacing=40 * ureg.kilometer,
        )
        north = segments[0].to_observation_target_area()
        south = segments[35].to_observation_target_area()

        lat_n, lon_n = observation_target_area_midpoint_geodetic_deg(north)
        lat_s, lon_s = observation_target_area_midpoint_geodetic_deg(south)
        self.assertAlmostEqual(abs(lon_n - lon_s), 180.0, places=3)

        earth_radius_km = 6378.0
        xy_n = target_areas_midpoint_disk_xy_km_on_sphere(
            (north,), earth_radius_km=earth_radius_km
        )
        xy_s = target_areas_midpoint_disk_xy_km_on_sphere(
            (south,), earth_radius_km=earth_radius_km
        )
        phi_n = disk_phi_deg_from_geodetic_deg(lat_n, lon_n)
        phi_s = disk_phi_deg_from_geodetic_deg(lat_s, lon_s)
        self.assertGreater(phi_s, phi_n)
        self.assertGreater(float(xy_s[1]), float(xy_n[1]))


if __name__ == "__main__":
    unittest.main()
