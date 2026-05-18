import unittest

import numpy as np

from utils.flight_geometry.line_of_sight import subsatellite_latitude_deg_polar_meridian
from utils.geometry.orbit_disk_wgs84 import satellite_disk_xy_rows_km_to_geodetic_deg


class SubsatelliteGeodeticDiskTest(unittest.TestCase):
    """Authoritative subsatellite LLA uses ``ecef2geodetic(disk_xy→ECEF)``; polar formula is legacy."""

    def test_theta_center_xy_yields_near_north_pole_latitude(self) -> None:
        theta_center = float(np.pi / 2)
        r_km = 7000.0
        xy = np.array([[r_km * np.cos(theta_center), r_km * np.sin(theta_center)]], dtype=float)
        lon_deg, lat_deg = satellite_disk_xy_rows_km_to_geodetic_deg(xy)
        self.assertAlmostEqual(float(lat_deg[0]), 90.0, places=3)
        self.assertAlmostEqual(float(lon_deg[0]), 0.0, places=3)

    def test_disk_geodetic_tracks_polar_meridian_latitude_near_sphere(self) -> None:
        theta_center = float(np.pi / 2)
        r_km = 7000.0
        for delta_deg in (-23.0, -10.0, 15.0):
            th = theta_center + np.deg2rad(delta_deg)
            xy = np.array([[r_km * np.cos(th), r_km * np.sin(th)]], dtype=float)
            _lon, lat_disk = satellite_disk_xy_rows_km_to_geodetic_deg(xy)
            lat_polar = subsatellite_latitude_deg_polar_meridian(th, theta_center_rad=theta_center)
            np.testing.assert_allclose(float(lat_disk[0]), lat_polar, rtol=0.0, atol=0.2)


if __name__ == "__main__":
    unittest.main()
