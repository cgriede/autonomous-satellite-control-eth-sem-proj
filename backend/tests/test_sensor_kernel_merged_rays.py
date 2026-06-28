"""Merged primary camera ray pass: observation line bins also drive cloud_blocked_fraction."""

from __future__ import annotations

import unittest

import numpy as np

from dataclasses import replace

from environment_definition.constants import EARTH_RADIUS, SIMULATION, UREG as ureg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import (
    S01_SECONDARY_MOUNT,
    build_setup,
)
from simulation.sensor_kernel import (
    SensorKernel,
    _cloud_blocked_fraction_from_earth_valid_hits,
)
from simulation.setup_types import SimulationOverrides


class CloudBlockedFractionHelperTest(unittest.TestCase):
    def test_blocked_fraction_counts_cloud_first_among_valid_earth_rays(self) -> None:
        hit_types = np.array([2, 1, 2], dtype=np.int8)
        earth_valid = np.array([True, True, True], dtype=bool)
        frac = _cloud_blocked_fraction_from_earth_valid_hits(hit_types, earth_valid)
        self.assertAlmostEqual(frac, 2.0 / 3.0)


class MergedSensorKernelTest(unittest.TestCase):
    def test_dual_camera_primary_and_secondary_line_shapes(self) -> None:
        setup = replace(
            build_setup(seed=0, include_cameras=True),
            simulation_overrides=SimulationOverrides(
                secondary_camera_observation_line_n_bins=200,
            ),
        )
        resolved = setup.resolve(require_camera=True)
        earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
        sat_xy = np.array([6800.0, 120.0], dtype=float)
        bore = np.array([-1.0, 0.05], dtype=float)
        bore = bore / np.linalg.norm(bore)

        scnd_tilt = float(S01_SECONDARY_MOUNT.tilt_off_nadir.to(ureg.rad).magnitude)
        z_ang = 0.0
        secondary_bore = np.array(
            [
                np.sin(z_ang + scnd_tilt),
                -np.cos(z_ang + scnd_tilt),
            ],
            dtype=float,
        )
        secondary_bore = secondary_bore / np.linalg.norm(secondary_bore)
        secondary_fov = float(S01_SECONDARY_MOUNT.camera.fov(axis="y").to(ureg.rad).magnitude)

        out = SensorKernel.evaluate(
            sat_pos_xy_km=sat_xy,
            boresight_dir_unit_xy=bore,
            altitude=resolved.altitude,
            earth_radius_km=earth_r,
            sim_time_s=12.0,
            sim_total_s=100.0,
            n_bins=int(SIMULATION.camera_observation_line_n_bins),
            n_clouds=len(resolved.clouds),
            clouds=resolved.clouds,
            n_bins_secondary=200,
            secondary_boresight_dir_unit_xy=secondary_bore,
            secondary_vertical_fov_rad=secondary_fov,
            target_areas=resolved.target_areas,
        )

        n_primary = int(SIMULATION.camera_observation_line_n_bins)
        self.assertEqual(out.camera_observation_line_codes.shape, (n_primary,))
        self.assertEqual(out.secondary_camera_observation_line_codes.shape, (200,))
        self.assertEqual(out.secondary_camera_cloud_blocked_fraction, 0.0)
        if np.isfinite(out.camera_cloud_blocked_fraction):
            self.assertGreaterEqual(out.camera_cloud_blocked_fraction, 0.0)
            self.assertLessEqual(out.camera_cloud_blocked_fraction, 1.0)


if __name__ == "__main__":
    unittest.main()
