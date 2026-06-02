"""Tests for pole-meridian ↔ orbit-disk ↔ geodetic coordinate bridge."""

import unittest

import numpy as np
from pymap3d.ecef import geodetic2ecef

from environment_definition.constants.EARTH import WGS84_ELLIPSOID
from utils.geometry.orbit_disk_polar_meridian import (
    disk_phi_deg_from_geodetic_deg,
    disk_phi_deg_from_track_offset_deg,
    geodetic_deg_from_disk_phi_deg,
    geodetic_deg_from_track_offset_deg,
    track_offset_deg_from_disk_phi_deg,
    track_offset_deg_from_geodetic_deg,
)
from utils.geometry.orbit_disk_wgs84 import KM_TO_M, disk_xy_km_to_geodetic_deg
from utils.geodesics.geodesic_helpers import lonlat_to_z0_plane_angle_deg
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg


class OrbitDiskPolarMeridianCoordsTest(unittest.TestCase):
    def test_delta_plus_minus_one_examples(self) -> None:
        lat_m, lon_m = geodetic_deg_from_track_offset_deg(-1.0)
        self.assertAlmostEqual(lat_m, 89.0, places=9)
        self.assertAlmostEqual(lon_m, 0.0, places=9)

        lat_p, lon_p = geodetic_deg_from_track_offset_deg(1.0)
        self.assertAlmostEqual(lat_p, 89.0, places=9)
        self.assertAlmostEqual(abs(lon_p), 180.0, places=9)

    def test_track_offset_round_trip(self) -> None:
        for delta in (-5.0, -1.0, 0.0, 1.0, 5.0):
            lat, lon = geodetic_deg_from_track_offset_deg(delta)
            back = track_offset_deg_from_geodetic_deg(lat, lon)
            self.assertAlmostEqual(back, delta, places=9, msg=f"delta={delta}")

    def test_phi_round_trip(self) -> None:
        for delta in (-5.0, -1.0, 0.0, 1.0, 5.0):
            phi = disk_phi_deg_from_track_offset_deg(delta)
            back = track_offset_deg_from_disk_phi_deg(phi)
            self.assertAlmostEqual(back, delta, places=9)
            lat, lon = geodetic_deg_from_disk_phi_deg(phi)
            self.assertAlmostEqual(
                track_offset_deg_from_geodetic_deg(lat, lon), delta, places=9
            )

    def test_disk_phi_matches_geodetic_projection(self) -> None:
        for delta in (-3.0, -1.0, 0.0, 1.0, 3.0):
            lat, lon = geodetic_deg_from_track_offset_deg(delta)
            phi_geo = disk_phi_deg_from_geodetic_deg(lat, lon)
            phi_delta = disk_phi_deg_from_track_offset_deg(delta)
            # WGS84 atan2(z,x) vs spherical track-offset φ differ slightly off the pole.
            self.assertAlmostEqual(phi_geo, phi_delta, delta=0.05)

    def test_surface_disk_xy_geodetic_lon_sign(self) -> None:
        """ECEF x-z surface points: descending leg has negative x → lon ≈ ±180°."""
        for delta in (-2.0, 2.0):
            lat, lon = geodetic_deg_from_track_offset_deg(delta)
            x_m, _y_m, z_m = geodetic2ecef(lat, lon, 0.0, ell=WGS84_ELLIPSOID, deg=True)
            xy_km = np.array([x_m, z_m], dtype=float) / KM_TO_M
            lon_disk, lat_disk = disk_xy_km_to_geodetic_deg(xy_km, ell=WGS84_ELLIPSOID)
            self.assertAlmostEqual(lat_disk, lat, places=4)
            if delta > 0.0:
                self.assertAlmostEqual(abs(lon_disk), 180.0, places=3)
            elif delta < 0.0:
                self.assertAlmostEqual(lon_disk, 0.0, places=3)

    def test_z0_plane_angle_is_not_orbit_disk_phi(self) -> None:
        """Renderer/z=0 azimuth must not be used as simulation disk φ past the pole."""
        lat, lon = geodetic_deg_from_track_offset_deg(2.0)
        wrong = lonlat_to_z0_plane_angle_deg(lon * ureg.deg, lat * ureg.deg)
        phi = disk_phi_deg_from_geodetic_deg(lat, lon)
        self.assertNotAlmostEqual(wrong, phi, places=1)

    def test_rejects_off_meridian_lon(self) -> None:
        with self.assertRaises(ValueError):
            track_offset_deg_from_geodetic_deg(80.0, 45.0)


    def test_cloud_geodetic_past_pole_yields_phi_gt_90(self) -> None:
        from environment_definition.constants import ureg
        from environment_definition.constants.SIMULATION import Cloud, GeodeticLonLat
        from simulation.camera_2d import compute_cloud_arc_specs_at_time

        cloud = Cloud(
            base_altitude=10.0 * ureg.km,
            top_altitude=20.0 * ureg.km,
            start_location=GeodeticLonLat(lat=89.0 * ureg.deg, lon=180.0 * ureg.deg),
            end_location=GeodeticLonLat(lat=88.0 * ureg.deg, lon=180.0 * ureg.deg),
        )
        specs = compute_cloud_arc_specs_at_time(
            sim_time_s=0.0,
            sim_total_s=100.0,
            earth_radius_km=6371.0,
            clouds=(cloud,),
        )
        phi_start_deg = float(np.rad2deg(specs[0]["start_rad"]))
        self.assertGreater(phi_start_deg, 90.0)


if __name__ == "__main__":
    unittest.main()
