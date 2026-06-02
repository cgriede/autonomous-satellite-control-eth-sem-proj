"""Unit tests for notebook-cycle cloud formation helpers (s01_utils)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

from environment_definition.constants.SIMULATION import GeodeticLonLat
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.geometry.orbit_disk_polar_meridian import (
    disk_phi_deg_from_geodetic_deg,
    geodetic_lonlat_deg,
)

_S01_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "s01"
if str(_S01_DIR) not in sys.path:
    sys.path.insert(0, str(_S01_DIR))

from s01_utils.cloud_formation import (  # noqa: E402
    cloud_formation_generator,
    geodetic_deg_on_disk_path_between,
    sample_extent_km,
    sample_start_km,
    sample_vertical_extent_km,
    vertical_extent_km,
)


class S01CloudFormationUtilsTest(unittest.TestCase):
    def test_path_endpoints_match_formation_lat_lon(self) -> None:
        lat_s, lon_s = geodetic_deg_on_disk_path_between(75.0, 0.0, 75.0, 180.0, 0.0)
        lat_e, lon_e = geodetic_deg_on_disk_path_between(75.0, 0.0, 75.0, 180.0, 1.0)
        self.assertAlmostEqual(lat_s, 75.0, places=5)
        self.assertAlmostEqual(lon_s, 0.0, places=5)
        self.assertAlmostEqual(lat_e, 75.0, places=3)
        self.assertAlmostEqual(abs(lon_e), 180.0, places=3)

    def test_vertical_extent_cap_at_max_top(self) -> None:
        self.assertEqual(vertical_extent_km(10, 12, max_top_km=20), (10, 20))
        self.assertEqual(vertical_extent_km(4, 3, max_top_km=20), (4, 7))

    def test_sample_vertical_extent_in_bounds(self) -> None:
        rng = np.random.default_rng(0)
        for _ in range(50):
            base_km, top_km = sample_vertical_extent_km(
                rng,
                base_lo_km=4,
                base_hi_km=12,
                thickness_lo_km=1,
                thickness_hi_km=16,
                max_top_km=20,
            )
            self.assertGreaterEqual(base_km, 4)
            self.assertLessEqual(base_km, 12)
            self.assertGreaterEqual(top_km, base_km + 1)
            self.assertLessEqual(top_km, 20)

    def test_sample_extent_and_start_are_integers(self) -> None:
        rng = np.random.default_rng(1)
        for _ in range(50):
            extent_km = sample_extent_km(rng, range_lo_km=1, range_hi_km=100)
            self.assertIsInstance(extent_km, int)
            self.assertGreaterEqual(extent_km, 1)
            self.assertLessEqual(extent_km, 100)
            start_km = sample_start_km(rng, path_km=500, extent_km=extent_km)
            self.assertIsNotNone(start_km)
            assert start_km is not None
            self.assertIsInstance(start_km, int)
            self.assertGreaterEqual(start_km, 0)
            self.assertLessEqual(start_km + extent_km, 500)

    def test_generated_clouds_within_formation_disk_phi(self) -> None:
        start = GeodeticLonLat(lat=75.0 * ureg.deg, lon=0.0 * ureg.deg)
        end = GeodeticLonLat(lat=75.0 * ureg.deg, lon=180.0 * ureg.deg)
        phi_lo = disk_phi_deg_from_geodetic_deg(*geodetic_lonlat_deg(start))
        phi_hi = disk_phi_deg_from_geodetic_deg(*geodetic_lonlat_deg(end))
        phi_min, phi_max = min(phi_lo, phi_hi), max(phi_lo, phi_hi)
        clouds = cloud_formation_generator(
            formation_start=start,
            formation_end=end,
            cloud_number_bounds=(5, 6),
            cloud_range_bounds=(10 * ureg.km, 50 * ureg.km),
            cloud_base_altitude_bounds=(4 * ureg.km, 12 * ureg.km),
            cloud_thickness_bounds=(1 * ureg.km, 16 * ureg.km),
            max_top_altitude=20 * ureg.km,
            rng=np.random.default_rng(42),
        )
        self.assertGreaterEqual(len(clouds), 1)
        for cloud in clouds:
            base_km = int(round(float(cloud.base_altitude.to(ureg.km).magnitude)))
            top_km = int(round(float(cloud.top_altitude.to(ureg.km).magnitude)))
            self.assertGreaterEqual(base_km, 4)
            self.assertLessEqual(base_km, 12)
            self.assertLessEqual(top_km, 20)
            self.assertGreater(top_km, base_km)
            lat_a, lon_a = geodetic_lonlat_deg(cloud.start_location)
            lat_b, lon_b = geodetic_lonlat_deg(cloud.end_location)
            phi_a = disk_phi_deg_from_geodetic_deg(lat_a, lon_a)
            phi_b = disk_phi_deg_from_geodetic_deg(lat_b, lon_b)
            self.assertGreaterEqual(min(phi_a, phi_b), phi_min - 1e-6)
            self.assertLessEqual(max(phi_a, phi_b), phi_max + 1e-6)


if __name__ == "__main__":
    unittest.main()
