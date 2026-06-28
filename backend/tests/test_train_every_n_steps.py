"""EpisodeRunner train_every_n_steps gating (counts controller stores, not sim steps)."""

from __future__ import annotations

import unittest

import numpy as np

from autonomous_control.episode_runner import EpisodeRunner
from autonomous_control.reward import RewardConfig
from dataclasses import replace

from simulation.setup_types import SimulationOverrides
from s01_utils import take_picture_verification as tpv


class _TrainCountAgent:
    def __init__(self) -> None:
        self.train_calls = 0

    def get_action(self, obs, train: bool) -> np.ndarray:
        _ = obs, train
        return np.array([0.0, -1.0], dtype=np.float64)

    def store(self, transition) -> None:
        pass

    def train(self) -> None:
        self.train_calls += 1


class TrainEveryNStepsTest(unittest.TestCase):
    def _setup(self):
        reward = RewardConfig(enable_distance_reward=True, enable_image_quality_capture=False)
        return replace(
            tpv.build_take_picture_verification_setup(seed=0),
            simulation_overrides=SimulationOverrides(reward_config=reward),
        )

    def test_stride_reduces_train_calls(self) -> None:
        setup = self._setup()
        runner = EpisodeRunner(setup)
        agent_every = _TrainCountAgent()
        agent_stride = _TrainCountAgent()
        every_result = runner.run_serial(
            agent_every,
            mode="train",
            train_every_n_steps=1,
            early_stop_on_budget_exhausted=False,
            verbose_print=1,
        )
        stride_result = runner.run_serial(
            agent_stride,
            mode="train",
            train_every_n_steps=4,
            early_stop_on_budget_exhausted=False,
            verbose_print=1,
        )
        self.assertEqual(every_result.steps, stride_result.steps)
        self.assertGreater(agent_every.train_calls, agent_stride.train_calls)
        self.assertAlmostEqual(
            agent_every.train_calls / max(agent_stride.train_calls, 1),
            4.0,
            delta=1.5,
        )


if __name__ == "__main__":
    unittest.main()
