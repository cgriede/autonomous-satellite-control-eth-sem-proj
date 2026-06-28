"""Warmup buffer stores 2-D baseline overflight actions; parity with nb07 rollout."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parents[1]
S01 = BACKEND / "notebooks" / "s01"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(S01) not in sys.path:
    sys.path.insert(0, str(S01))

from autonomous_control.config.randomness import derive_seed
from autonomous_control.episode_runner import EpisodeRunner
from s01_utils.baseline_overflight import build_baseline_overflight_setup, run_baseline_overflight_rollout


class _BufferAgent:
    def __init__(self) -> None:
        self.buffer: list[tuple] = []

    def get_action(self, obs, train: bool) -> np.ndarray:
        _ = obs
        _ = train
        return np.array([0.0, -1.0], dtype=np.float64)

    def store(self, transition) -> None:
        self.buffer.append(transition)


class WarmupBaselineIntegrationTest(unittest.TestCase):
    def test_warmup_episode_stores_2d_actions_with_shutter_dim(self):
        setup = build_baseline_overflight_setup(n_targets=3, cloud_seed=0)
        agent = _BufferAgent()
        result = EpisodeRunner(setup).run_serial(agent, mode="warmup", collect_states=True)
        self.assertGreater(result.steps, 0)
        interval = result.effective_controller_update_interval_steps
        expected_stores = (result.steps + interval - 1) // interval
        self.assertEqual(len(agent.buffer), expected_stores)
        shutter_plus = sum(1 for _obs, action, _r, _n, _d in agent.buffer if float(action[1]) > 0.0)
        for _obs, action, _r, _n, _d in agent.buffer:
            self.assertEqual(action.shape, (2,))
        self.assertGreater(shutter_plus, 0)

    def test_nb07_rollout_and_warmup_share_torque_request_stack(self):
        seed = 0
        setup = build_baseline_overflight_setup(n_targets=3, cloud_seed=seed)
        rollout = run_baseline_overflight_rollout(setup, show_progress=False)
        warmup = EpisodeRunner(setup).run_serial(
            _BufferAgent(),
            mode="warmup",
            collect_states=False,
            np_rng=np.random.default_rng(derive_seed(seed, "warmup_episode", 0)),
        )
        self.assertEqual(
            rollout.series.metadata.torque_policy_label,
            warmup.simulation_series.metadata.torque_policy_label,
        )
        self.assertGreater(warmup.steps, 0)
        self.assertLessEqual(warmup.steps, rollout.series.t_s.shape[0] - 1)


if __name__ == "__main__":
    unittest.main()
