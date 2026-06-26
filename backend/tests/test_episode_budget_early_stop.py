"""Train/warmup early stop when capture budget exhausted; eval keeps full horizon."""

from __future__ import annotations

import unittest

import numpy as np

from autonomous_control.episode_runner import EpisodeRunner
from autonomous_control.reward import RewardConfig
from dataclasses import replace

from simulation.setup_types import SimulationOverrides
from s01_utils import take_picture_verification as tpv


class _ShutterEveryStepAgent:
    """Always command take-picture to exhaust budget quickly."""

    def get_action(self, obs, train: bool) -> np.ndarray:
        _ = obs, train
        return np.array([0.0, 1.0], dtype=np.float64)

    def store(self, transition) -> None:
        pass

    def train(self) -> None:
        pass


class EpisodeBudgetEarlyStopTest(unittest.TestCase):
    def _training_setup(self, *, distance_reward: bool = False):
        reward = RewardConfig(
            enable_distance_reward=distance_reward,
            enable_image_quality_capture=True,
        )
        return replace(
            tpv.build_take_picture_verification_setup(seed=0),
            simulation_overrides=SimulationOverrides(reward_config=reward),
        )

    def test_train_stops_before_full_horizon_when_budget_exhausted(self) -> None:
        setup = self._training_setup()
        resolved = setup.resolve(require_camera=True)
        runner = EpisodeRunner(setup)
        full_horizon = runner.run_serial(
            _ShutterEveryStepAgent(),
            mode="eval",
            early_stop_on_budget_exhausted=False,
            verbose_print=1,
        ).steps
        train_result = runner.run_serial(
            _ShutterEveryStepAgent(),
            mode="train",
            early_stop_on_budget_exhausted=True,
            verbose_print=1,
        )
        self.assertLess(train_result.steps, full_horizon)
        self.assertTrue(train_result.ended_early_on_budget)
        self.assertEqual(train_result.configured_episode_steps, full_horizon)
        self.assertEqual(
            len(train_result.simulation_series.t_s) - 1,
            train_result.steps,
        )

    def test_capture_only_early_stop_same_return_as_full_horizon(self) -> None:
        setup = self._training_setup(distance_reward=False)
        runner = EpisodeRunner(setup)
        full = runner.run_serial(
            _ShutterEveryStepAgent(),
            mode="train",
            early_stop_on_budget_exhausted=False,
            verbose_print=1,
        )
        early = runner.run_serial(
            _ShutterEveryStepAgent(),
            mode="train",
            early_stop_on_budget_exhausted=True,
            verbose_print=1,
        )
        self.assertLess(early.steps, full.steps)
        self.assertAlmostEqual(early.episode_return, full.episode_return, places=4)

    def test_eval_runs_full_horizon_with_budget_enabled(self) -> None:
        setup = self._training_setup()
        runner = EpisodeRunner(setup)
        eval_result = runner.run_serial(
            _ShutterEveryStepAgent(),
            mode="eval",
            early_stop_on_budget_exhausted=False,
            verbose_print=1,
        )
        train_result = runner.run_serial(
            _ShutterEveryStepAgent(),
            mode="train",
            early_stop_on_budget_exhausted=True,
            verbose_print=1,
        )
        self.assertGreater(eval_result.steps, train_result.steps)


if __name__ == "__main__":
    unittest.main()
