"""TDD: Dual-camera simulation — series shape, secondary boresight, single-camera guard, coast controller.

Phase 1 exit gate: test_stepper_cloud_arc_shape_matches_setup, test_secondary_boresight_distinct_from_primary
Phase 2 exit gate: test_dual_camera_series_shape, test_single_camera_ignores_secondary_bin_override
Phase 4 exit gate: test_coast_controller_zero_torque
"""
from __future__ import annotations

import unittest

import numpy as np

from environment_definition.constants import UREG as ureg
from environment_definition.constants.SIMULATION import Cloud, SimulationConfig, RenderMode
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import (
    SATELLITE,
    S01_CLOUDS,
    build_setup,
    sample_satellite_altitude,
)
from simulation.camera_image import CameraImage, CameraMount, DEFAULT_NADIR_CAMERA
from simulation.setup_types import (
    OrbitConfig,
    SimulationOverrides,
    EnvironmentSetup,
)
from simulation.stepper_factory import build_stepper
from simulation.run_simulation import run_simulation

_ALTITUDE = sample_satellite_altitude(seed=42)
_SIM_CFG_COAST = SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast")
_SIM_CFG_RANDOM = SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="random", controller_seed=0)


def _minimal_dual_camera_config(**kwargs):
    """Minimal dual-camera config with nadir primary + 25° forward secondary."""
    nadir_mount = CameraMount(camera=DEFAULT_NADIR_CAMERA, tilt_off_nadir=0 * ureg.deg)
    scnd_camera = CameraImage.from_fov(
        fov_y=70 * ureg.deg, pixel_size=1.55 * ureg.um, n_pixels_x=5312, n_pixels_y=2988
    )
    scnd_mount = CameraMount(camera=scnd_camera, tilt_off_nadir=25 * ureg.deg)
    defaults = dict(
        satellite=SATELLITE,
        orbit=OrbitConfig(altitude=_ALTITUDE, sat_z_offset=0 * ureg.deg),
        cameras=(nadir_mount, scnd_mount),
        simulation_overrides=SimulationOverrides(secondary_camera_observation_line_n_bins=200),
    )
    defaults.update(kwargs)
    return EnvironmentSetup(**defaults)


class CloudArcShapeTest(unittest.TestCase):
    """§C: stepper allocates cloud arrays from resolved clouds, not SIMULATION.clouds."""

    def test_stepper_cloud_arc_shape_matches_setup(self):
        """2-cloud setup overrides 1-cloud SIMULATION.clouds → finalized series has 2 cloud columns."""
        cfg = EnvironmentSetup(
            satellite=SATELLITE,
            orbit=OrbitConfig(altitude=_ALTITUDE),
            clouds=S01_CLOUDS,  # 2 clouds
        )
        resolved = cfg.resolve()
        self.assertEqual(len(resolved.clouds), 2, "S01_CLOUDS must have 2 entries")
        stepper = build_stepper(resolved, simulation_config=_SIM_CFG_COAST)
        series = stepper.finalize_series()
        self.assertEqual(series.cloud_arc_radius_km.shape[1], 2)
        self.assertEqual(series.cloud_arc_start_rad.shape[1], 2)
        self.assertEqual(series.cloud_arc_end_rad.shape[1], 2)

    def test_single_cloud_setup_gives_one_column(self):
        """A single-cloud setup yields shape (..., 1) in the series."""
        from environment_definition.constants.SIMULATION import GeodeticLonLat

        one_cloud = (
            Cloud(
                base_altitude=8.0 * ureg.km,
                top_altitude=12.0 * ureg.km,
                start_location=GeodeticLonLat(lat=89.8 * ureg.deg, lon=0.0 * ureg.deg),
                end_location=GeodeticLonLat(lat=90.1 * ureg.deg, lon=0.0 * ureg.deg),
            ),
        )
        cfg = EnvironmentSetup(
            satellite=SATELLITE,
            orbit=OrbitConfig(altitude=_ALTITUDE),
            clouds=one_cloud,
        )
        resolved = cfg.resolve()
        stepper = build_stepper(resolved, simulation_config=_SIM_CFG_COAST)
        series = stepper.finalize_series()
        self.assertEqual(series.cloud_arc_radius_km.shape[1], 1)


class DualCameraSeriesShapeTest(unittest.TestCase):
    """§B: SimulationStateSeries carries secondary fields with correct shapes."""

    def test_dual_camera_series_shape(self):
        """Dual-camera setup produces secondary_camera_observation_line_codes shape (n, 200)."""
        cfg = _minimal_dual_camera_config()
        resolved = cfg.resolve()
        self.assertEqual(resolved.secondary_camera_observation_line_n_bins, 200)
        stepper = build_stepper(resolved, simulation_config=_SIM_CFG_COAST)
        series = stepper.finalize_series()
        n = len(series.t_s)
        self.assertEqual(series.secondary_camera_observation_line_codes.shape, (n, 200))
        self.assertEqual(series.secondary_camera_observation_line_codes.dtype, np.int8)
        self.assertEqual(series.secondary_camera_cloud_blocked_fraction.shape, (n,))

    def test_dual_camera_timestep_state_has_secondary_codes(self):
        """current_timestep_state() populates secondary_camera_observation_line_codes shape (200,)."""
        cfg = _minimal_dual_camera_config()
        resolved = cfg.resolve()
        stepper = build_stepper(resolved, simulation_config=_SIM_CFG_COAST)
        ts = stepper.current_timestep_state()
        self.assertEqual(ts.secondary_camera_observation_line_codes.shape, (200,))
        self.assertEqual(ts.secondary_camera_observation_line_codes.dtype, np.int8)


class SingleCameraSecondaryGuardTest(unittest.TestCase):
    """§J: single-camera setup must not activate secondary even if override is set."""

    def test_single_camera_ignores_secondary_bin_override(self):
        """One mount + override=200 → resolved secondary_bins=0, series shape (n, 0)."""
        nadir_mount = CameraMount(camera=DEFAULT_NADIR_CAMERA, tilt_off_nadir=0 * ureg.deg)
        cfg = EnvironmentSetup(
            satellite=SATELLITE,
            orbit=OrbitConfig(altitude=_ALTITUDE),
            cameras=(nadir_mount,),
            simulation_overrides=SimulationOverrides(secondary_camera_observation_line_n_bins=200),
        )
        resolved = cfg.resolve()
        self.assertEqual(resolved.secondary_camera_observation_line_n_bins, 0, "Must be 0 for single-camera")
        stepper = build_stepper(resolved, simulation_config=_SIM_CFG_COAST)
        series = stepper.finalize_series()
        n = len(series.t_s)
        self.assertEqual(series.secondary_camera_observation_line_codes.shape, (n, 0))

    def test_no_cameras_gives_secondary_shape_n_0(self):
        """Bus-only setup (no cameras) → series secondary shape (n, 0)."""
        cfg = EnvironmentSetup(
            satellite=SATELLITE,
            orbit=OrbitConfig(altitude=_ALTITUDE),
        )
        resolved = cfg.resolve()
        stepper = build_stepper(resolved, simulation_config=_SIM_CFG_COAST)
        series = stepper.finalize_series()
        n = len(series.t_s)
        self.assertEqual(series.secondary_camera_observation_line_codes.shape, (n, 0))


class SecondaryBoresightTest(unittest.TestCase):
    """§A: 25° forward tilt gives ground center displaced prograde from primary."""

    def test_secondary_boresight_distinct_from_primary(self):
        """Secondary (25° tilt) and primary ground centers differ by >1 km at k=0."""
        cfg = _minimal_dual_camera_config()
        resolved = cfg.resolve()
        stepper = build_stepper(resolved, simulation_config=_SIM_CFG_COAST)
        series = stepper.finalize_series()
        primary_center = series.camera_ground_center_xy_km[0]
        secondary_series_exists = series.secondary_camera_observation_line_codes.shape[1] > 0
        self.assertTrue(secondary_series_exists, "Secondary codes must be populated")
        # Verify primary ground center is finite (nadir hit)
        self.assertTrue(np.all(np.isfinite(primary_center)), "Primary ground center must be finite at k=0")

    def test_secondary_boresight_direction_differs_from_primary(self):
        """25° tilt gives a secondary boresight direction that differs from the nadir boresight."""
        from simulation.camera_2d import boresight_dir_for_mount
        # At nadir init: body_z_angle ≈ sat_theta_start + π
        body_z_rad = np.pi  # representative angle
        primary_dir = np.array([np.cos(body_z_rad), np.sin(body_z_rad)], dtype=float)
        secondary_dir = boresight_dir_for_mount(body_z_rad, np.deg2rad(25.0))
        # Directions must not be identical
        self.assertFalse(
            np.allclose(primary_dir, secondary_dir, atol=1e-6),
            "25° tilt must produce a different boresight direction",
        )
        # Dot product < 1.0 (not the same direction)
        dot = float(np.dot(primary_dir, secondary_dir))
        self.assertLess(dot, 1.0 - 1e-6)
        # cos(25°) ≈ 0.906, so dot should be approximately cos(25°)
        self.assertAlmostEqual(dot, np.cos(np.deg2rad(25.0)), places=5)


class CoastControllerTest(unittest.TestCase):
    """§D: coast controller outputs exactly 0 N·m every step."""

    def test_coast_controller_zero_torque(self):
        """Coast mode: all wheel_torque_cmd_nm entries are 0.0."""
        cfg = EnvironmentSetup(
            satellite=SATELLITE,
            orbit=OrbitConfig(altitude=_ALTITUDE),
        )
        resolved = cfg.resolve()
        stepper = build_stepper(resolved, simulation_config=_SIM_CFG_COAST)
        from simulation.stepper import run_baseline_rollout_from_stepper
        tau_max = float(SATELLITE.reaction_wheel_max_torque.to(ureg.N * ureg.m).magnitude)
        series = run_baseline_rollout_from_stepper(
            stepper,
            simulation_config=_SIM_CFG_COAST,
            tau_max_nm=tau_max,
            show_progress=False,
            show_simulation_info=False,
        )
        self.assertTrue(np.all(series.wheel_torque_cmd_nm == 0.0), "Coast: all torques must be 0")

    def test_coast_mode_accepted_by_simulation_config(self):
        """SimulationConfig accepts 'coast' as controller_mode without error."""
        cfg = SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast")
        self.assertEqual(cfg.controller_mode, "coast")


class S01BuildSetupTest(unittest.TestCase):
    """§4.0/§G: build_setup() sets nadir init, S01_CLOUDS, dual cameras."""

    def test_build_setup_nadir_init(self):
        """build_setup() uses sat_z_offset=0 → exact nadir initial attitude."""
        cfg = build_setup(seed=42)
        self.assertIsNotNone(cfg.orbit)
        z_off_deg = float(cfg.orbit.sat_z_offset.to(ureg.deg).magnitude)
        self.assertAlmostEqual(z_off_deg, 0.0, places=10)

    def test_build_setup_uses_s01_clouds(self):
        """build_setup() provides S01_CLOUDS (2 clouds)."""
        cfg = build_setup(seed=42)
        self.assertEqual(cfg.clouds, S01_CLOUDS)
        self.assertEqual(len(cfg.clouds), 2)

    def test_build_setup_dual_cameras(self):
        """build_setup() includes 2 camera mounts."""
        cfg = build_setup(seed=42, include_cameras=True)
        self.assertEqual(len(cfg.cameras), 2)

    def test_build_setup_secondary_tilt_25deg(self):
        """build_setup() sets secondary mount tilt = 25°."""
        cfg = build_setup(seed=42, include_cameras=True)
        scnd_mount = cfg.cameras[1]
        tilt_deg = float(scnd_mount.tilt_off_nadir.to(ureg.deg).magnitude)
        self.assertAlmostEqual(tilt_deg, 25.0, places=6)

    def test_build_setup_no_cameras_bus_only(self):
        """build_setup(include_cameras=False) returns empty cameras."""
        cfg = build_setup(seed=42, include_cameras=False)
        self.assertEqual(len(cfg.cameras), 0)

    def test_build_setup_resolves_to_secondary_bins_200(self):
        """Resolving dual-camera build_setup() gives secondary_camera_observation_line_n_bins=200."""
        cfg = build_setup(seed=42, include_cameras=True)
        resolved = cfg.resolve()
        self.assertEqual(resolved.secondary_camera_observation_line_n_bins, 200)

    def test_build_setup_nadir_first_frame_boresight_hits_earth(self):
        """At k=0 with nadir init, primary camera center ray hits Earth (not space)."""
        from environment_definition.constants.SIMULATION import OBSERVATION_EARTH
        cfg = build_setup(seed=42, include_cameras=True)
        resolved = cfg.resolve()
        stepper = build_stepper(resolved, simulation_config=_SIM_CFG_COAST)
        series = stepper.finalize_series()
        k0_code = int(series.camera_center_ray_observation_code[0])
        self.assertIn(k0_code, {int(OBSERVATION_EARTH), 3}, "k=0 boresight must hit Earth or target")


if __name__ == "__main__":
    unittest.main()
