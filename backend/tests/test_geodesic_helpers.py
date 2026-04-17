import unittest

import numpy as np

from environment_definition.constants.EARTH import geod
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.geodesics.geodesic_helpers import (
    east_north_km_to_lon_lat,
    geodesic_distance,
    sigma_deg_to_meters_north,
)


def _flat_approx_lat_lon(
    lat0_deg: float,
    lon0_deg: float,
    east_km: float,
    north_km: float,
) -> tuple[float, float]:
    """Previous project approximation (degrees / km per degree)."""
    lat_deg = lat0_deg + north_km / 110.574
    lon_scale_km = max(111.320 * np.cos(np.deg2rad(lat_deg)), 1e-6)
    lon_deg = lon0_deg + east_km / lon_scale_km
    return lat_deg, lon_deg


class GeodesicHelpersTest(unittest.TestCase):
    def test_east_north_matches_two_step_fwd(self):
        lon0_deg, lat0_deg = 8.2, 46.8
        east_km, north_km = 3.5, -2.0

        lat_q, lon_q = east_north_km_to_lon_lat(
            lon0_deg * ureg.deg,
            lat0_deg * ureg.deg,
            east_km * ureg.km,
            north_km * ureg.km,
            geod=geod,
        )

        lon1, lat1, _ = geod.fwd(lon0_deg, lat0_deg, 0.0, north_km * 1000.0)
        lon2, lat2, _ = geod.fwd(lon1, lat1, 90.0, east_km * 1000.0)

        self.assertAlmostEqual(
            float(lat_q.to(ureg.deg).magnitude), lat2, places=9
        )
        self.assertAlmostEqual(
            float(lon_q.to(ureg.deg).magnitude), lon2, places=9
        )

    def test_geodesic_distance_short_hop(self):
        """~1 km north from a Switzerland-like latitude — distance ≈ 1000 m."""
        lon1, lat1 = 8.0, 46.8
        lon2, lat2 = 8.0, 46.8 + (1.0 / 111.32)
        d = geodesic_distance(
            lon1 * ureg.deg,
            lat1 * ureg.deg,
            lon2 * ureg.deg,
            lat2 * ureg.deg,
            geod=geod,
        )
        self.assertAlmostEqual(float(d.to(ureg.m).magnitude), 1000.0, delta=15.0)

    def test_sigma_deg_to_meters_north_order_of_111km(self):
        lon = 8.0 * ureg.deg
        lat = 46.8 * ureg.deg
        sigma = 1.0 * ureg.deg
        sigma_m = sigma_deg_to_meters_north(lon, lat, sigma, geod=geod)
        self.assertAlmostEqual(float(sigma_m.to(ureg.km).magnitude), 111.0, delta=2.0)

    def test_small_offset_near_flat_formula(self):
        lat0_deg, lon0_deg = 46.80, 8.20
        east_km, north_km = 2.0, -1.5
        flat_lat, flat_lon = _flat_approx_lat_lon(
            lat0_deg, lon0_deg, east_km, north_km
        )
        lat_q, lon_q = east_north_km_to_lon_lat(
            lon0_deg * ureg.deg,
            lat0_deg * ureg.deg,
            east_km * ureg.km,
            north_km * ureg.km,
            geod=geod,
        )
        g_lat = float(lat_q.to(ureg.deg).magnitude)
        g_lon = float(lon_q.to(ureg.deg).magnitude)
        self.assertAlmostEqual(g_lat, flat_lat, places=3)
        self.assertAlmostEqual(g_lon, flat_lon, places=3)


if __name__ == "__main__":
    unittest.main()
