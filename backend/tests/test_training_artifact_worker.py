"""Tests for background artifact worker."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from tests.test_training_run_artifacts import _minimal_series
from utils.ml_training.training_artifact_worker import BackgroundArtifactWorker, run_artifacts_sync
from utils.ml_training.training_run_artifacts import artifact_paths_map, episode_row_from_result


class TrainingArtifactWorkerTest(unittest.TestCase):
    def test_background_worker_writes_reward_plot(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            paths = artifact_paths_map(run_dir)
            worker = BackgroundArtifactWorker(run_dir)
            series = _minimal_series()
            worker.submit_reward_plot(series, label="test", out_path=paths["train_last_reward_plot"])
            errors = worker.shutdown(wait=True)
            self.assertEqual(errors, [])
            self.assertTrue(paths["train_last_reward_plot"].exists())

    def test_background_worker_writes_video(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            paths = artifact_paths_map(run_dir)
            worker = BackgroundArtifactWorker(run_dir)
            worker.submit_video_export(_minimal_series(), paths["eval_best_video"])
            errors = worker.shutdown(wait=True)
            self.assertEqual(errors, [])
            self.assertTrue(paths["eval_best_video"].exists())

    def test_sync_fallback_writes_plot(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            paths = artifact_paths_map(run_dir)
            series = _minimal_series()
            rows = [
                episode_row_from_result(
                    global_idx=0,
                    phase="train",
                    episode_idx=0,
                    episode_return=-1.0,
                    steps=4,
                )
            ]
            errors = run_artifacts_sync(
                reward_jobs=[(series, "sync", paths["train_last_reward_plot"])],
                run_dir=run_dir,
                episode_rows=rows,
            )
            self.assertEqual(errors, [])
            self.assertTrue(paths["train_last_reward_plot"].exists())
            self.assertTrue(paths["returns_plot"].exists())


if __name__ == "__main__":
    unittest.main()
