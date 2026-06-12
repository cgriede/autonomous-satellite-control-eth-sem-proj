"""Unit tests for analytic bore ground-track velocity and smear."""

from __future__ import annotations

import math
import unittest

import numpy as np

from environment_definition.constants.EARTH import WGS84_ELLIPSOID
from simulation.image_quality import (
    analytic_bore_ground_velocity_disk_m_s,
    bore_ground_speed_m_s,
)
from utils.geometry.orbit_disk_wgs84 import disk_ray_earth_hit_xy_km


class AnalyticBoreGroundVelocityTest(unittest.TestCase):
    def test_nadir_body_orbit_rate_matches_ground_track(self):
        """Nadir PD feedforward (omega_body ≈ omega_orbit) gives ~R_earth·ω ground speed."""
        r_earth_km = 6371.0
        r_orbit_km = r_earth_km + 548.0
        omega = 0.001097
        theta = 0.42
        sat = r_orbit_km * np.array([math.cos(theta), math.sin(theta)], dtype=float)
        nadir_dir = -sat / np.linalg.norm(sat)
        v = analytic_bore_ground_velocity_disk_m_s(
            sat_pos_xy_km=sat,
            boresight_dir_unit_xy=nadir_dir,
            theta_orbit_rad=theta,
            omega_orbit_rad_s=omega,
            orbit_radius_km=r_orbit_km,
            omega_body_rad_s=omega,
        )
        v_coast = analytic_bore_ground_velocity_disk_m_s(
            sat_pos_xy_km=sat,
            boresight_dir_unit_xy=nadir_dir,
            theta_orbit_rad=theta,
            omega_orbit_rad_s=omega,
            orbit_radius_km=r_orbit_km,
            omega_body_rad_s=0.0,
        )
        v_ground_expected = r_earth_km * omega * 1000.0
        self.assertAlmostEqual(float(np.linalg.norm(v)), v_ground_expected, delta=0.15 * v_ground_expected)
        self.assertGreater(float(np.linalg.norm(v_coast)), 1.05 * float(np.linalg.norm(v)))

    def test_analytic_matches_finite_diff_on_ray_hit(self):
        r_earth_km = 6371.0
        r_orbit_km = r_earth_km + 548.0
        omega = 0.001097
        theta = 0.9
        dt = 0.4
        omega_body = 0.0013
        sat0 = r_orbit_km * np.array([math.cos(theta), math.sin(theta)], dtype=float)
        phi = theta + math.pi
        bore0 = np.array([math.cos(phi), math.sin(phi)], dtype=float)

        def hit_xy(sat_xy: np.ndarray, bore: np.ndarray) -> np.ndarray:
            t_km, hit = disk_ray_earth_hit_xy_km(
                sat_xy_km=sat_xy,
                ray_dir_unit_xy=bore,
                ell=WGS84_ELLIPSOID,
            )
            self.assertIsNotNone(t_km)
            return np.asarray(hit, dtype=float)

        sat1 = r_orbit_km * np.array(
            [math.cos(theta + omega * dt), math.sin(theta + omega * dt)],
            dtype=float,
        )
        phi1 = phi + omega_body * dt
        bore1 = np.array([math.cos(phi1), math.sin(phi1)], dtype=float)
        v_emp = bore_ground_speed_m_s(hit_xy(sat1, bore1), dt_s=dt, prev_bore_ground_xy_km=hit_xy(sat0, bore0))
        v_analytic = float(
            np.linalg.norm(
                analytic_bore_ground_velocity_disk_m_s(
                    sat_pos_xy_km=sat0,
                    boresight_dir_unit_xy=bore0,
                    theta_orbit_rad=theta,
                    omega_orbit_rad_s=omega,
                    orbit_radius_km=r_orbit_km,
                    omega_body_rad_s=omega_body,
                )
            )
        )
        self.assertAlmostEqual(v_analytic, v_emp, delta=0.08 * max(v_emp, 1.0))


class ImageQualityIntegrationTest(unittest.TestCase):
    def test_target_track_rollout_quality_exceeds_nadir(self):
        import sys
        from pathlib import Path

        backend = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(backend / "notebooks" / "s01"))
        from s01_utils import image_quality_verification as iqv

        nadir = iqv.run_nadir_pointing_image_quality_gate(seed=0, fast=True)
        target = iqv.run_target_pointing_image_quality_gate(seed=0, fast=True)
        q_nadir = float(np.nanmedian(nadir.camera_image_quality))
        q_target = float(np.nanmedian(target.camera_image_quality))
        self.assertGreater(q_target, q_nadir)


if __name__ == "__main__":
    unittest.main()
