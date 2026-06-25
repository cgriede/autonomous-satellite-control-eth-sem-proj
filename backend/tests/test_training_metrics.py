"""Tests for episode-level MPO metrics aggregation."""

from __future__ import annotations

import unittest

from autonomous_control.training_metrics import (
    MetricsSliceStart,
    collect_episode_learning_stats,
    learning_stats_to_row,
    snapshot_metrics_start,
)
from simulation.simulation_info import exploration_status_for_rollout


class _FakeAgent:
    def __init__(self) -> None:
        self.metrics = {
            "qloss": [1.0, 2.0],
            "piloss": [0.5],
            "kl": [0.1, 0.2, 0.3],
            "kl_mu": [0.08, 0.09],
            "kl_sigma": [0.01, 0.02],
            "eta": [1.0, 1.1],
        }
        self.step_counter = 500
        self.exploration_steps = 100
        self.buffer = list(range(12))


class TrainingMetricsTest(unittest.TestCase):
    def test_exploration_status_train_uses_policy_sample(self):
        label, active = exploration_status_for_rollout(mode="train")
        self.assertEqual(label, "active (policy sample)")
        self.assertTrue(active)

    def test_snapshot_and_collect_slice_means(self):
        agent = _FakeAgent()
        start = snapshot_metrics_start(agent)
        assert start is not None
        agent.metrics["qloss"].extend([4.0, 6.0])
        agent.metrics["piloss"].append(1.5)
        agent.metrics["kl"].append(0.4)
        agent.metrics["kl_mu"].append(0.10)

        stats = collect_episode_learning_stats(
            agent,
            phase="train",
            episode_idx=2,
            episode_return=-100.0,
            steps=50,
            mode="train",
            metrics_start=start,
        )
        assert stats is not None
        self.assertEqual(stats.n_train_updates, 2)
        self.assertAlmostEqual(stats.q_loss_mean, 5.0)
        self.assertAlmostEqual(stats.pi_loss_mean, 1.5)
        self.assertAlmostEqual(stats.kl_mean, 0.4)
        self.assertAlmostEqual(stats.kl_mu_mean, 0.10)
        self.assertAlmostEqual(stats.buffer_size, 12)
        self.assertTrue(stats.in_exploration)

    def test_warmup_returns_none(self):
        agent = _FakeAgent()
        start = MetricsSliceStart(lengths={"qloss": 0})
        self.assertIsNone(
            collect_episode_learning_stats(
                agent,
                phase="warmup",
                episode_idx=0,
                episode_return=0.0,
                steps=1,
                mode="warmup",
                metrics_start=start,
            )
        )

    def test_learning_stats_to_row_defaults(self):
        row = learning_stats_to_row(None)
        self.assertTrue(row["n_train_updates"] == 0)
        self.assertTrue(row["q_loss_mean"] != row["q_loss_mean"])  # nan


if __name__ == "__main__":
    unittest.main()
