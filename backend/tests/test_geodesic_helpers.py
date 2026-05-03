import unittest

import numpy as np

from environment_definition.constants.EARTH import geod
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.geodesics.geodesic_helpers import (
    circle_stripe_footprint_overlap_ratio,
    east_north_km_to_lon_lat,
    geodesic_initial_bearing,
    geodesic_distance,
    geodetic_bbox_contains,
    geodetic_bbox_intersection_ratio,
    GeodeticBoundingBox,
    lonlat_to_z0_plane_angle_deg,
    minor_arc_midpoint_deg,
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

    def test_geodesic_initial_bearing_matches_pyproj_azimuth(self):
        lon1, lat1 = 8.0, 46.8
        lon2, lat2 = 8.3, 47.0
        az12, _az21, _dist_m = geod.inv(lon1, lat1, lon2, lat2)
        b = geodesic_initial_bearing(
            lon1 * ureg.deg,
            lat1 * ureg.deg,
            lon2 * ureg.deg,
            lat2 * ureg.deg,
            geod=geod,
        )
        self.assertAlmostEqual(float(b.to(ureg.deg).magnitude), float(az12), places=9)

    def test_geodetic_bbox_contains_non_wrapping(self):
        bbox = GeodeticBoundingBox(
            lon_min=8.0 * ureg.deg,
            lon_max=9.0 * ureg.deg,
            lat_min=46.0 * ureg.deg,
            lat_max=47.0 * ureg.deg,
        )
        self.assertTrue(
            geodetic_bbox_contains(
                lon=8.5 * ureg.deg,
                lat=46.5 * ureg.deg,
                bbox=bbox,
            )
        )
        self.assertFalse(
            geodetic_bbox_contains(
                lon=9.5 * ureg.deg,
                lat=46.5 * ureg.deg,
                bbox=bbox,
            )
        )

    def test_geodetic_bbox_contains_date_line_wrap(self):
        bbox = GeodeticBoundingBox(
            lon_min=170.0 * ureg.deg,
            lon_max=-170.0 * ureg.deg,
            lat_min=-2.0 * ureg.deg,
            lat_max=2.0 * ureg.deg,
        )
        self.assertTrue(
            geodetic_bbox_contains(
                lon=179.0 * ureg.deg,
                lat=0.0 * ureg.deg,
                bbox=bbox,
            )
        )
        self.assertTrue(
            geodetic_bbox_contains(
                lon=-179.5 * ureg.deg,
                lat=0.0 * ureg.deg,
                bbox=bbox,
            )
        )
        self.assertFalse(
            geodetic_bbox_contains(
                lon=160.0 * ureg.deg,
                lat=0.0 * ureg.deg,
                bbox=bbox,
            )
        )

    def test_geodetic_bbox_intersection_ratio(self):
        target = GeodeticBoundingBox(
            lon_min=10.0 * ureg.deg,
            lon_max=12.0 * ureg.deg,
            lat_min=45.0 * ureg.deg,
            lat_max=47.0 * ureg.deg,
        )
        full_overlap = GeodeticBoundingBox(
            lon_min=10.0 * ureg.deg,
            lon_max=12.0 * ureg.deg,
            lat_min=45.0 * ureg.deg,
            lat_max=47.0 * ureg.deg,
        )
        quarter_overlap = GeodeticBoundingBox(
            lon_min=11.0 * ureg.deg,
            lon_max=12.0 * ureg.deg,
            lat_min=45.0 * ureg.deg,
            lat_max=46.0 * ureg.deg,
        )
        disjoint = GeodeticBoundingBox(
            lon_min=13.0 * ureg.deg,
            lon_max=14.0 * ureg.deg,
            lat_min=45.0 * ureg.deg,
            lat_max=46.0 * ureg.deg,
        )
        self.assertAlmostEqual(
            geodetic_bbox_intersection_ratio(target_bbox=target, footprint_bbox=full_overlap, geod=geod),
            1.0,
            places=9,
        )
        ratio_quarter = geodetic_bbox_intersection_ratio(
            target_bbox=target,
            footprint_bbox=quarter_overlap,
            geod=geod,
        )
        self.assertGreater(ratio_quarter, 0.20)
        self.assertLess(ratio_quarter, 0.30)
        self.assertEqual(
            geodetic_bbox_intersection_ratio(target_bbox=target, footprint_bbox=disjoint, geod=geod),
            0.0,
        )

    def test_lonlat_equator_lon_matches_plane_angle(self):
        ang = lonlat_to_z0_plane_angle_deg(90.0 * ureg.deg, 0.0 * ureg.deg)
        self.assertAlmostEqual(ang, 90.0, places=6)

    def test_minor_arc_midpoint_crossing_zero(self):
        mid = minor_arc_midpoint_deg(350.0, 10.0)
        self.assertAlmostEqual(mid, 0.0, places=6)

    def test_circle_stripe_footprint_overlap_inside_stripe(self):
        r = 6371.0
        left = np.array([r * np.cos(np.deg2rad(88.0)), r * np.sin(np.deg2rad(88.0))], dtype=float)
        right = np.array([r * np.cos(np.deg2rad(92.0)), r * np.sin(np.deg2rad(92.0))], dtype=float)
        ratio = circle_stripe_footprint_overlap_ratio(
            footprint_left_xy_km=left,
            footprint_right_xy_km=right,
            stripe_angle_start_deg=85.0,
            stripe_angle_end_deg=95.0,
            n_samples=16,
        )
        self.assertGreaterEqual(ratio, 0.99)

    def test_circle_stripe_footprint_overlap_outside_stripe(self):
        r = 6371.0
        left = np.array([r * np.cos(np.deg2rad(80.0)), r * np.sin(np.deg2rad(80.0))], dtype=float)
        right = np.array([r * np.cos(np.deg2rad(82.0)), r * np.sin(np.deg2rad(82.0))], dtype=float)
        ratio = circle_stripe_footprint_overlap_ratio(
            footprint_left_xy_km=left,
            footprint_right_xy_km=right,
            stripe_angle_start_deg=85.0,
            stripe_angle_end_deg=95.0,
            n_samples=12,
        )
        self.assertLessEqual(ratio, 0.05)


if __name__ == "__main__":
    unittest.main()
