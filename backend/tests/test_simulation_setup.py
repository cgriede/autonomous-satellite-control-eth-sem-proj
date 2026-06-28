"""TDD: EnvironmentSetup.resolve() — validation, defaults, camera opt-in."""
from __future__ import annotations

import unittest

from environment_definition.constants import SIMULATION, UREG as ureg
from environment_definition.constants.MISSION import OBSERVATION_TARGET_AREAS
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import (
    SATELLITE,
    sample_satellite_altitude,
)
from simulation.camera_image import CameraMount, DEFAULT_NADIR_CAMERA
from simulation.setup_types import (
    OrbitConfig,
    ResolvedSimulationSetup,
    SimulationOverrides,
    EnvironmentSetup,
    SimulationSetupError,
)


_ALTITUDE = sample_satellite_altitude(seed=42)


def _minimal_config(**kwargs) -> EnvironmentSetup:
    """Smallest valid config: satellite + altitude."""
    defaults = dict(
        satellite=SATELLITE,
        orbit=OrbitConfig(altitude=_ALTITUDE),
    )
    defaults.update(kwargs)
    return EnvironmentSetup(**defaults)


class ResolveDefaultsTest(unittest.TestCase):
    def test_resolve_returns_resolved_setup(self):
        cfg = _minimal_config()
        resolved = cfg.resolve()
        self.assertIsInstance(resolved, ResolvedSimulationSetup)

    def test_resolve_fills_clouds_from_simulation_constants(self):
        cfg = _minimal_config()
        resolved = cfg.resolve()
        self.assertEqual(resolved.clouds, SIMULATION.clouds)

    def test_resolve_fills_target_areas_from_mission_constants(self):
        cfg = _minimal_config()
        resolved = cfg.resolve()
        self.assertEqual(resolved.target_areas, OBSERVATION_TARGET_AREAS)

    def test_resolve_fills_theta_center_from_simulation_constants(self):
        cfg = _minimal_config()
        resolved = cfg.resolve()
        expected_rad = float(SIMULATION.theta_center.to(ureg.rad).magnitude)
        self.assertAlmostEqual(resolved.theta_center_rad, expected_rad, places=10)

    def test_resolve_fills_sat_motion_span_scale_from_simulation_constants(self):
        cfg = _minimal_config()
        resolved = cfg.resolve()
        self.assertAlmostEqual(
            resolved.sat_motion_span_scale, float(SIMULATION.sat_motion_span_scale), places=10
        )

    def test_resolve_fills_camera_observation_line_n_bins_from_simulation_constants(self):
        cfg = _minimal_config()
        resolved = cfg.resolve()
        self.assertEqual(
            resolved.camera_observation_line_n_bins, int(SIMULATION.camera_observation_line_n_bins)
        )

    def test_resolve_propagates_satellite(self):
        cfg = _minimal_config()
        resolved = cfg.resolve()
        self.assertIs(resolved.satellite, SATELLITE)

    def test_resolve_propagates_altitude(self):
        cfg = _minimal_config()
        resolved = cfg.resolve()
        self.assertAlmostEqual(
            float(resolved.altitude.to(ureg.km).magnitude),
            float(_ALTITUDE.to(ureg.km).magnitude),
            places=6,
        )

    def test_resolve_start_end_angle_are_finite_floats(self):
        cfg = _minimal_config()
        resolved = cfg.resolve()
        self.assertIsInstance(resolved.start_angle_deg, float)
        self.assertIsInstance(resolved.end_angle_deg, float)
        self.assertLess(resolved.start_angle_deg, 0.0)
        self.assertGreater(resolved.end_angle_deg, 0.0)


class ResolveValidationTest(unittest.TestCase):
    def test_missing_satellite_raises_setup_error(self):
        cfg = EnvironmentSetup(orbit=OrbitConfig(altitude=_ALTITUDE))
        with self.assertRaises(SimulationSetupError):
            cfg.resolve()

    def test_missing_altitude_raises_setup_error(self):
        cfg = EnvironmentSetup(satellite=SATELLITE, orbit=OrbitConfig())
        with self.assertRaises(SimulationSetupError):
            cfg.resolve()

    def test_missing_orbit_entirely_raises_setup_error(self):
        cfg = EnvironmentSetup(satellite=SATELLITE)
        with self.assertRaises(SimulationSetupError):
            cfg.resolve()


class CameraOptInTest(unittest.TestCase):
    def test_empty_cameras_allowed_by_default(self):
        cfg = _minimal_config()
        resolved = cfg.resolve()
        self.assertEqual(len(resolved.cameras), 0)

    def test_require_camera_true_with_empty_cameras_raises(self):
        cfg = _minimal_config()
        with self.assertRaises(SimulationSetupError) as ctx:
            cfg.resolve(require_camera=True)
        self.assertIn("cameras is empty", str(ctx.exception))

    def test_require_camera_true_with_cameras_passes(self):
        mount = CameraMount(camera=DEFAULT_NADIR_CAMERA, tilt_off_nadir=0 * ureg.deg)
        cfg = _minimal_config(cameras=(mount,))
        resolved = cfg.resolve(require_camera=True)
        self.assertEqual(len(resolved.cameras), 1)

    def test_multi_camera_setup_stores_all_mounts(self):
        mount1 = CameraMount(camera=DEFAULT_NADIR_CAMERA, tilt_off_nadir=0 * ureg.deg)
        mount2 = CameraMount(camera=DEFAULT_NADIR_CAMERA, tilt_off_nadir=5 * ureg.deg)
        cfg = _minimal_config(cameras=(mount1, mount2))
        resolved = cfg.resolve()
        self.assertEqual(len(resolved.cameras), 2)
        self.assertIs(resolved.cameras[0], mount1)
        self.assertIs(resolved.cameras[1], mount2)


class SimulationOverridesTest(unittest.TestCase):
    def test_override_camera_observation_line_n_bins(self):
        cfg = _minimal_config(
            simulation_overrides=SimulationOverrides(camera_observation_line_n_bins=50)
        )
        resolved = cfg.resolve()
        self.assertEqual(resolved.camera_observation_line_n_bins, 50)

    def test_reward_config_propagated_when_set(self):
        from autonomous_control.reward import RewardConfig

        rc = RewardConfig(enable_energy=True)
        cfg = _minimal_config(simulation_overrides=SimulationOverrides(reward_config=rc))
        resolved = cfg.resolve()
        self.assertIs(resolved.reward_config, rc)

    def test_reward_config_is_none_when_not_set(self):
        cfg = _minimal_config()
        resolved = cfg.resolve()
        self.assertIsNone(resolved.reward_config)


if __name__ == "__main__":
    unittest.main()
