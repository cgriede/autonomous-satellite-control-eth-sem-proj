"""TDD: EpisodeRunner.run_serial — stepper parity via factory, EpisodeResult artifact."""
from __future__ import annotations

import unittest

import numpy as np

from autonomous_control.episode_runner import EpisodeRunner
from environment_definition.constants import RenderMode, SimulationConfig, UREG as ureg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import (
    SATELLITE,
    build_setup,
    sample_satellite_altitude,
)
from simulation.setup_types import OrbitConfig, EnvironmentSetup
from simulation.state_types import SimulationStateSeries
from autonomous_control.training_runtime import EpisodeResult


class _MetricsAgent:
    def __init__(self) -> None:
        self.metrics = {
            "qloss": [],
            "piloss": [],
            "kl": [],
            "kl_mu": [],
            "kl_sigma": [],
            "eta": [],
        }
        self.step_counter = 10_000
        self.exploration_steps = 0
        self.buffer = []

    def get_action(self, obs: np.ndarray, train: bool) -> np.ndarray:
        _ = obs
        _ = train
        return np.array([0.0], dtype=np.float64)

    def store(self, transition) -> None:
        pass

    def train(self) -> dict[str, float]:
        self.metrics["qloss"].append(1.0)
        self.metrics["piloss"].append(0.5)
        self.metrics["kl"].append(0.1)
        self.metrics["kl_mu"].append(0.08)
        self.metrics["kl_sigma"].append(0.02)
        self.metrics["eta"].append(1.0)
        return {"q_loss": 1.0, "pi_loss": 0.5, "kl": 0.1}


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
    """Factory-built stepper must produce same horizon as direct construction from resolved setup."""

    def _build_direct_stepper(self, resolved, *, simulation_config):
        from simulation.stepper import SimulationStepper

        return SimulationStepper(
            simulation_config=simulation_config,
            earth_radius=resolved.earth_radius,
            earth_gravitational_parameter=resolved.earth_gravitational_parameter,
            satellite=resolved.satellite,
            satellite_altitude=resolved.altitude,
            theta_center_rad=resolved.theta_center_rad,
            start_angle_deg=resolved.start_angle_deg,
            end_angle_deg=resolved.end_angle_deg,
            sat_motion_span_scale=resolved.sat_motion_span_scale,
            sat_z_offset_deg=resolved.sat_z_offset_deg,
            ureg=resolved.ureg,
            camera_pixel_ray_samples=resolved.camera_pixel_ray_samples,
            camera_observation_line_n_bins=resolved.camera_observation_line_n_bins,
            reward_config=resolved.reward_config,
            clouds=resolved.clouds,
            cameras=resolved.cameras,
            camera_kernel_backend=resolved.camera_kernel_backend,
            secondary_camera_observation_line_n_bins=resolved.secondary_camera_observation_line_n_bins,
            target_areas=resolved.target_areas,
        )

    def test_factory_stepper_total_steps_matches_direct_construction(self):
        altitude = sample_satellite_altitude(seed=0)
        cfg = EnvironmentSetup(
            satellite=SATELLITE,
            orbit=OrbitConfig(altitude=altitude),
        )
        resolved = cfg.resolve()
        simulation_config = SimulationConfig(
            render_mode=RenderMode.HEADLESS,
            torque_command_source="builtin",
            builtin_torque_policy="random",
        )
        from simulation.stepper_factory import build_stepper

        factory_stepper = build_stepper(resolved, simulation_config=simulation_config)
        direct_stepper = self._build_direct_stepper(
            resolved,
            simulation_config=simulation_config,
        )
        self.assertEqual(factory_stepper.total_steps, direct_stepper.total_steps)


class EpisodeRunnerRunSerialTest(unittest.TestCase):
    def setUp(self):
        altitude = sample_satellite_altitude(seed=1)
        self.cfg = EnvironmentSetup(
            satellite=SATELLITE,
            orbit=OrbitConfig(altitude=altitude),
        )
        self.agent = _ZeroTorqueAgent()

    def test_run_serial_enables_attitude_safety_controller(self):
        runner = EpisodeRunner(self.cfg)
        result = runner.run_serial(self.agent, mode="train")
        self.assertTrue(
            result.simulation_series.metadata.attitude_controller_enabled,
            "MPO training episodes must run with AttitudeSafetyController enabled",
        )

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

    def test_train_mode_populates_learning_stats(self):
        runner = EpisodeRunner(self.cfg)
        result = runner.run_serial(
            _MetricsAgent(),
            mode="train",
            train_updates_per_step=1,
            verbose_print=1,
        )
        self.assertIsNotNone(result.learning_stats)
        assert result.learning_stats is not None
        self.assertGreater(result.learning_stats.n_train_updates, 0)
        self.assertAlmostEqual(result.learning_stats.q_loss_mean, 1.0)


if __name__ == "__main__":
    unittest.main()
