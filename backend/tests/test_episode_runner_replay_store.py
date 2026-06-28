"""Replay buffer writes align with pilot/controller ticks only."""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from autonomous_control.episode_runner import EpisodeRunner
from autonomous_control.reward import RewardConfig
from simulation.setup_types import SimulationOverrides

BACKEND = Path(__file__).resolve().parents[1]
S01 = BACKEND / "notebooks" / "s01"
if str(S01) not in sys.path:
    sys.path.insert(0, str(S01))

from s01_utils import take_picture_verification as tpv  # noqa: E402
from s01_utils.baseline_overflight import build_baseline_overflight_setup  # noqa: E402


def _expected_pilot_store_count(steps: int, interval: int) -> int:
    interval = max(1, int(interval))
    return (int(steps) + interval - 1) // interval


class _StoreCountAgent:
    def __init__(self) -> None:
        self.store_calls = 0
        self.last_stored_action: np.ndarray | None = None

    def get_action(self, obs, train: bool) -> np.ndarray:
        _ = obs, train
        return np.array([0.0, 0.9], dtype=np.float64)

    def store(self, transition) -> None:
        self.store_calls += 1
        _obs, action, _reward, _next_obs, _done = transition
        self.last_stored_action = np.asarray(action, dtype=np.float32).copy()

    def train(self) -> None:
        pass


class ReplayStoreOnPilotTickTest(unittest.TestCase):
    def _capture_runner(self) -> EpisodeRunner:
        reward = RewardConfig(enable_distance_reward=False, enable_image_quality_capture=True)
        setup = replace(
            tpv.build_take_picture_verification_setup(seed=0),
            simulation_overrides=SimulationOverrides(reward_config=reward),
        )
        return EpisodeRunner(setup)

    def test_train_store_count_matches_controller_updates_not_sim_steps(self) -> None:
        runner = self._capture_runner()
        agent = _StoreCountAgent()
        result = runner.run_serial(
            agent,
            mode="train",
            early_stop_on_budget_exhausted=False,
            verbose_print=1,
        )
        interval = result.effective_controller_update_interval_steps
        expected = _expected_pilot_store_count(result.steps, interval)
        self.assertEqual(agent.store_calls, expected)
        self.assertLess(agent.store_calls, result.steps)

    def test_warmup_baseline_store_count_matches_controller_updates(self) -> None:
        setup = build_baseline_overflight_setup(n_targets=3, cloud_seed=0)
        agent = _StoreCountAgent()
        result = EpisodeRunner(setup).run_serial(
            agent,
            mode="warmup",
            early_stop_on_budget_exhausted=False,
            verbose_print=1,
        )
        interval = result.effective_controller_update_interval_steps
        expected = _expected_pilot_store_count(result.steps, interval)
        self.assertEqual(agent.store_calls, expected)


class EarlyStopDefaultTest(unittest.TestCase):
    def test_default_early_stop_false_runs_longer_than_explicit_budget_stop(self) -> None:
        runner = ReplayStoreOnPilotTickTest()._capture_runner()
        default = runner.run_serial(_StoreCountAgent(), mode="train", verbose_print=1)
        early = runner.run_serial(
            _StoreCountAgent(),
            mode="train",
            early_stop_on_budget_exhausted=True,
            verbose_print=1,
        )
        self.assertGreater(default.steps, early.steps)


if __name__ == "__main__":
    unittest.main()
