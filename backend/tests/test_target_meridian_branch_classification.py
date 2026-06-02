"""Target hits must match meridian branch (δ), not latitude alone."""

import unittest

from environment_definition.constants import ureg
from environment_definition.constants.MISSION import LON_GLOBAL
from utils.geometry.mission_stripe_disk import geodetic_deg_in_target_areas, target_areas_track_offset_ranges_deg
from utils.geometry.polar_meridian_track import build_target_grid_polar_meridian


class TargetMeridianBranchClassificationTest(unittest.TestCase):
    def test_same_latitude_wrong_branch_is_not_target(self) -> None:
        segments = build_target_grid_polar_meridian(
            anchor_lat=85 * ureg.deg,
            anchor_lon=LON_GLOBAL,
            n_targets=50,
            target_size=15 * ureg.kilometer,
            spacing=40 * ureg.kilometer,
        )
        areas = tuple(s.to_observation_target_area() for s in segments)
        ranges = target_areas_track_offset_ranges_deg(areas)
        last = segments[-1]
        lat_mid = 0.5 * (
            float(last.lat_min.to(ureg.deg).magnitude) + float(last.lat_max.to(ureg.deg).magnitude)
        )
        # Descending-leg band (lon 180) should not match ascending-leg hit (lon 0) at same latitude.
        self.assertFalse(
            geodetic_deg_in_target_areas(lon_deg=0.0, lat_deg=lat_mid, offset_ranges=ranges)
        )
        self.assertTrue(
            geodetic_deg_in_target_areas(
                lon_deg=float(last.lon_min_deg),
                lat_deg=lat_mid,
                offset_ranges=ranges,
            )
        )


if __name__ == "__main__":
    unittest.main()
