"""TDD: EpisodeRunner.run_serial — stepper parity via factory, EpisodeResult artifact."""
from __future__ import annotations

import unittest

import numpy as np

from autonomous_control.episode_runner import EpisodeRunner
from environment_definition.constants import SIMULATION, UREG as ureg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import (
    SATELLITE,
    build_setup,
    sample_satellite_altitude,
)
from simulation.setup_types import OrbitConfig, EnvironmentSetup
from simulation.state_types import SimulationStateSeries
from autonomous_control.training_runtime import EpisodeResult


class _ZeroTorqueAgent:
    def get_action(self, obs: np.ndarray, train: bool) -> np.ndarray:
        _ = obs
        _ = train
        return np.array([0.0], dtype=np.float64)

    def store(self, transition) -> None:
        pass

    def train(self) -> None:
        pass


class EpisodeRunnerStepperParityTest(unittest.TestCase):
    """Factory-built stepper must produce same horizon as direct construction."""

    def _build_direct_stepper(self, altitude):
        from environment_definition.constants import (
            EARTH_GRAVITATIONAL_PARAMETER,
            EARTH_RADIUS,
            RenderMode,
            SIMULATION,
            SimulationConfig,
            UREG as ureg,
        )
        from environment_definition.constants.MISSION import los_theta_offsets_deg
        from simulation.stepper import SimulationStepper

        theta_center_rad = float(SIMULATION.theta_center.to(ureg.rad).magnitude)
        start_deg, end_deg = los_theta_offsets_deg(
            orbit_height=altitude,
            margin_deg=float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude),
        )
        return SimulationStepper(
            simulation_config=SimulationConfig(
                render_mode=RenderMode.HEADLESS,
                controller_mode="random",
            ),
            earth_radius=EARTH_RADIUS,
            earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
            satellite=SATELLITE,
            satellite_altitude=altitude,
            theta_center_rad=theta_center_rad,
            start_angle_deg=float(start_deg),
            end_angle_deg=float(end_deg),
            sat_motion_span_scale=float(SIMULATION.sat_motion_span_scale),
            sat_z_offset_deg=float(SIMULATION.sat_z_offset.to(ureg.deg).magnitude),
            ureg=ureg,
            camera_pixel_ray_samples=int(SIMULATION.camera_pixel_ray_samples),
        )

    def test_factory_stepper_total_steps_matches_direct_construction(self):
        altitude = sample_satellite_altitude(seed=0)
        cfg = EnvironmentSetup(
            satellite=SATELLITE,
            orbit=OrbitConfig(altitude=altitude),
        )
        runner = EpisodeRunner(cfg)
        # Compare total_steps between factory-built stepper and direct stepper.
        from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig
        from simulation.stepper_factory import build_stepper

        resolved = cfg.resolve()
        factory_stepper = build_stepper(
            resolved,
            simulation_config=SimulationConfig(
                render_mode=RenderMode.HEADLESS,
                controller_mode="random",
            ),
        )
        direct_stepper = self._build_direct_stepper(altitude)
        self.assertEqual(factory_stepper.total_steps, direct_stepper.total_steps)


class EpisodeRunnerRunSerialTest(unittest.TestCase):
    def setUp(self):
        altitude = sample_satellite_altitude(seed=1)
        self.cfg = EnvironmentSetup(
            satellite=SATELLITE,
            orbit=OrbitConfig(altitude=altitude),
        )
        self.agent = _ZeroTorqueAgent()

    def test_run_serial_returns_episode_result(self):
        runner = EpisodeRunner(self.cfg)
        result = runner.run_serial(self.agent, mode="train")
        self.assertIsInstance(result, EpisodeResult)

    def test_run_serial_result_has_simulation_series(self):
        runner = EpisodeRunner(self.cfg)
        result = runner.run_serial(self.agent, mode="train")
        self.assertIsInstance(result.simulation_series, SimulationStateSeries)

    def test_run_serial_result_steps_positive(self):
        runner = EpisodeRunner(self.cfg)
        result = runner.run_serial(self.agent, mode="train")
        self.assertGreater(result.steps, 0)

    def test_run_serial_steps_equals_simulation_series_length_minus_one(self):
        runner = EpisodeRunner(self.cfg)
        result = runner.run_serial(self.agent, mode="train")
        self.assertEqual(result.steps, len(result.simulation_series.t_s) - 1)

    def test_run_serial_warmup_random_returns_episode_result(self):
        runner = EpisodeRunner(self.cfg)
        result = runner.run_serial(self.agent, mode="warmup", warmup_controller="random")
        self.assertIsInstance(result, EpisodeResult)
        self.assertGreater(result.steps, 0)

    def test_run_serial_effective_controller_interval_positive(self):
        runner = EpisodeRunner(self.cfg)
        result = runner.run_serial(self.agent, mode="train")
        self.assertGreater(result.effective_controller_update_interval_steps, 0)
        self.assertGreater(result.effective_controller_update_interval_s, 0.0)

    def test_build_setup_produces_runnable_config(self):
        setup = build_setup(seed=99)
        runner = EpisodeRunner(setup)
        result = runner.run_serial(self.agent, mode="train")
        self.assertIsInstance(result.simulation_series, SimulationStateSeries)


if __name__ == "__main__":
    unittest.main()
