"""Tests for training run CSV/JSON and matplotlib artifact writers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from simulation.state_types import SimulationMetadata, SimulationStateSeries
from utils.ml_training.training_run_artifacts import (
    artifact_paths_map,
    episode_row_from_result,
    export_run_plots,
    finalize_episodes_csv,
    plot_episode_reward_timeline,
    write_config_snapshot,
    write_summary_metrics_json,
)


def _minimal_series(n: int = 5) -> SimulationStateSeries:
    t = np.linspace(0.0, 4.0, n)
    reward = np.ones(n, dtype=float) * -1.0
    zeros = np.zeros(n, dtype=float)
    return SimulationStateSeries(
        t_s=t,
        theta_orbit_rad=zeros,
        radius_km=np.full(n, 7000.0),
        body_z_angle_rad=zeros,
        simulation_reward=reward,
        wheel_torque_cmd_nm=zeros,
        camera_gsd_m=np.full(n, 1.5),
        camera_vertical_fov_rad=0.02,
        camera_ground_left_xy_km=np.zeros((n, 2)),
        camera_ground_right_xy_km=np.zeros((n, 2)),
        camera_ground_center_xy_km=np.zeros((n, 2)),
        camera_center_first_hit_xy_km=np.zeros((n, 2)),
        camera_center_first_hit_is_cloud=np.zeros(n, dtype=bool),
        camera_center_ray_observation_code=np.zeros(n, dtype=np.int8),
        camera_cloud_blocked_fraction=np.zeros(n),
        camera_observation_line_codes=np.zeros((n, 4), dtype=np.int8),
        sat_subpoint_lat_deg=zeros,
        sat_subpoint_lon_deg=zeros,
        sat_altitude_m=np.full(n, 528_000.0),
        camera_ground_left_lon_lat_deg=np.zeros((n, 2)),
        camera_ground_right_lon_lat_deg=np.zeros((n, 2)),
        camera_ground_center_lon_lat_deg=np.zeros((n, 2)),
        target_area_intersection_ratio=zeros,
        target_area_novelty_ratio=zeros,
        cloud_arc_radius_km=np.full((n, 1), np.nan),
        cloud_arc_start_rad=np.full((n, 1), np.nan),
        cloud_arc_end_rad=np.full((n, 1), np.nan),
        metadata=SimulationMetadata(
            orbit_period_s=5700.0,
            omega_rad_s=0.001,
            sim_total_s=4.0,
            sim_dt_s=1.0,
            theta_start_rad=0.0,
            theta_end_rad=0.1,
            sat_theta_start_rad=0.0,
            sat_theta_span_rad=0.1,
            start_angle_deg=-1.0,
            end_angle_deg=1.0,
        ),
    )


class TrainingRunArtifactsTest(unittest.TestCase):
    def test_csv_json_and_plots_written(self):
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            paths = artifact_paths_map(run_dir)
            rows = [
                episode_row_from_result(
                    global_idx=0,
                    phase="train",
                    episode_idx=0,
                    episode_return=-10.0,
                    steps=5,
                    learning_row={
                        "n_train_updates": 3,
                        "q_loss_mean": 1.2,
                        "pi_loss_mean": 0.3,
                        "kl_mean": 0.05,
                        "kl_mu_mean": 0.04,
                        "kl_sigma_mean": 0.01,
                        "eta_mean": 1.0,
                        "buffer_size": 10,
                        "in_exploration": False,
                    },
                )
            ]
            write_config_snapshot(run_dir, {"seed": 1})
            finalize_episodes_csv(run_dir, rows)
            write_summary_metrics_json(run_dir, rows)
            export_run_plots(run_dir, rows)
            plot_episode_reward_timeline(
                _minimal_series(),
                label="test",
                out_path=paths["train_last_reward_plot"],
            )

            self.assertTrue((run_dir / "config.json").exists())
            self.assertTrue((run_dir / "episodes.csv").exists())
            summary = json.loads((run_dir / "summary_metrics.json").read_text(encoding="utf-8"))
            self.assertIn("train", summary)
            self.assertTrue(paths["returns_plot"].exists())
            self.assertTrue(paths["learning_curves_plot"].exists())
            self.assertTrue(paths["train_last_reward_plot"].exists())


if __name__ == "__main__":
    unittest.main()
