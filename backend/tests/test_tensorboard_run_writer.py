"""Tests for TensorBoardRunWriter episode logging."""

from __future__ import annotations

import math
import unittest
from pathlib import Path

from utils.ml_training.tensorboard_run_writer import (
    TensorBoardLogProfile,
    TensorBoardRunWriter,
    build_hparams_from_config_snapshot,
    verify_train_return_parity,
)
from utils.ml_training.training_run_artifacts import finalize_episodes_csv, episode_row_from_result


def _learning_row(
    *,
    q_loss_mean: float = 1.0,
    pi_loss_mean: float = -0.5,
    kl_mean: float = 0.2,
    eta_mean: float = 3.0,
) -> dict[str, float | int | bool]:
    return {
        "n_train_updates": 10,
        "q_loss_mean": q_loss_mean,
        "pi_loss_mean": pi_loss_mean,
        "kl_mean": kl_mean,
        "kl_mu_mean": float("nan"),
        "kl_sigma_mean": float("nan"),
        "eta_mean": eta_mean,
        "buffer_size": 100,
        "in_exploration": False,
    }


def _scalar_tags(log_dir: Path) -> dict[str, list[tuple[int, float]]]:
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    event_files = sorted(log_dir.glob("events.out.tfevents.*"))
    if not event_files:
        raise AssertionError(f"No TensorBoard event files under {log_dir}")

    acc = EventAccumulator(str(log_dir))
    acc.Reload()
    out: dict[str, list[tuple[int, float]]] = {}
    for tag in acc.Tags().get("scalars", []):
        events = acc.Scalars(tag)
        out[tag] = [(int(event.step), float(event.value)) for event in events]
    return out


class TensorBoardRunWriterTest(unittest.TestCase):
    def test_writer_smoke_and_scalar_parity(self) -> None:
        run_dir = Path(self._testMethodName) / "run"
        run_dir.mkdir(parents=True, exist_ok=True)

        writer = TensorBoardRunWriter(run_dir, TensorBoardLogProfile())
        writer.log_hparams(
            build_hparams_from_config_snapshot(
                {
                    "workflow": {"seed": 7, "train_episodes": 2},
                    "mpo": {"batch_size": 64, "gamma": 0.99},
                }
            )
        )
        writer.log_train_episode(0, -10.0, _learning_row(q_loss_mean=1.5, kl_mean=0.3))
        writer.log_train_episode(1, -5.0, _learning_row(q_loss_mean=2.0, kl_mean=0.4))
        writer.close()

        tb_dir = run_dir / "tensorboard"
        self.assertTrue(tb_dir.is_dir())
        self.assertTrue(any(tb_dir.glob("events.out.tfevents.*")))

        tags = _scalar_tags(tb_dir)
        expected_tags = {
            "train/episode_return",
            "train/q_loss_mean",
            "train/pi_loss_mean",
            "train/kl_mean",
            "train/eta_mean",
        }
        self.assertTrue(expected_tags.issubset(set(tags)))
        self.assertFalse(any(tag.startswith("warmup/") for tag in tags))
        self.assertFalse(any(tag.startswith("eval/") for tag in tags))

        returns = dict(tags["train/episode_return"])
        self.assertAlmostEqual(returns[0], -10.0)
        self.assertAlmostEqual(returns[1], -5.0)
        self.assertAlmostEqual(dict(tags["train/q_loss_mean"])[0], 1.5)
        self.assertAlmostEqual(dict(tags["train/kl_mean"])[1], 0.4)

    def test_profile_respects_disabled_train_return_and_losses(self) -> None:
        run_dir = Path(self._testMethodName) / "run_no_return"
        run_dir.mkdir(parents=True, exist_ok=True)

        profile = TensorBoardLogProfile(train_return=False, q_pi_loss=False, kl_mean=True)
        writer = TensorBoardRunWriter(run_dir, profile)
        writer.log_train_episode(0, -10.0, _learning_row())
        writer.close()

        tags = _scalar_tags(run_dir / "tensorboard")
        self.assertNotIn("train/episode_return", tags)
        self.assertNotIn("train/q_loss_mean", tags)
        self.assertNotIn("train/pi_loss_mean", tags)
        self.assertIn("train/kl_mean", tags)

    def test_build_hparams_from_config_snapshot(self) -> None:
        hparams = build_hparams_from_config_snapshot(
            {
                "workflow": {"seed": 7, "train_episodes": 20, "experiment_name": "ml_compare"},
                "mpo": {"learning_rate_q": 0.001, "batch_size": 128},
            }
        )
        self.assertEqual(hparams["workflow/seed"], 7)
        self.assertEqual(hparams["workflow/train_episodes"], 20)
        self.assertEqual(hparams["mpo/batch_size"], 128)
        self.assertAlmostEqual(float(hparams["mpo/learning_rate_q"]), 0.001)

    def test_skips_nan_losses(self) -> None:
        run_dir = Path(self._testMethodName) / "run_nan"
        run_dir.mkdir(parents=True, exist_ok=True)

        row = _learning_row()
        row["kl_mean"] = float("nan")
        writer = TensorBoardRunWriter(run_dir, TensorBoardLogProfile())
        writer.log_train_episode(0, 1.0, row)
        writer.close()

        tags = _scalar_tags(run_dir / "tensorboard")
        self.assertIn("train/episode_return", tags)
        self.assertNotIn("train/kl_mean", tags)

    def test_verify_train_return_parity(self) -> None:
        run_dir = Path(self._testMethodName) / "run_parity"
        run_dir.mkdir(parents=True, exist_ok=True)

        writer = TensorBoardRunWriter(run_dir, TensorBoardLogProfile(use_hparams=False))
        writer.log_train_episode(0, -12.5, _learning_row())
        writer.log_train_episode(1, 3.25, _learning_row())
        writer.close()

        rows = [
            episode_row_from_result(
                global_idx=1,
                phase="warmup",
                episode_idx=0,
                episode_return=50.0,
                steps=10,
                learning_row={},
            ),
            episode_row_from_result(
                global_idx=2,
                phase="train",
                episode_idx=0,
                episode_return=-12.5,
                steps=10,
                learning_row=_learning_row(),
            ),
            episode_row_from_result(
                global_idx=3,
                phase="train",
                episode_idx=1,
                episode_return=3.25,
                steps=10,
                learning_row=_learning_row(),
            ),
        ]
        finalize_episodes_csv(run_dir, rows)
        verify_train_return_parity(run_dir)


class TensorBoardOptOutTest(unittest.TestCase):
    def test_disabled_profile_writes_nothing_when_no_episodes(self) -> None:
        run_dir = Path(self._testMethodName) / "run_empty"
        run_dir.mkdir(parents=True, exist_ok=True)

        writer = TensorBoardRunWriter(run_dir, TensorBoardLogProfile(use_hparams=False))
        writer.close()

        tb_dir = run_dir / "tensorboard"
        self.assertFalse(tb_dir.exists() or (tb_dir.is_dir() and any(tb_dir.iterdir())))


if __name__ == "__main__":
    unittest.main()
