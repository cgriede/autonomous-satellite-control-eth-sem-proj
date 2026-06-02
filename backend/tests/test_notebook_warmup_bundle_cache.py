"""Tests for notebook warmup episode bundle cache (fingerprint + gzip pickle)."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch
from gymnasium import spaces

from environment_definition.constants import SIMULATION

from autonomous_control.feature_selection import ControllerFeatureConfig
from autonomous_control.notebook_warmup_bundle_cache import (
    NB_WARMUP_BUNDLE_VERSION,
    bundle_dir_for_digest,
    digest_for_warmup_fingerprint,
    load_or_build_notebook_random_warmup_episodes,
    preload_warmup_buffer_from_episodes,
    reset_agent_replay_counters,
    save_warmup_episode_bundle,
    satellite_altitude_m_to_float,
    try_load_warmup_episode_bundle,
    warmup_fingerprint_payload,
)
from autonomous_control.training_runtime import EpisodeResult, ReplayBuffer
from simulation.state_types import SimulationMetadata, SimulationStateSeries


def _minimal_state_series(*, n_frames: int, n_bins: int) -> SimulationStateSeries:
    n = int(n_frames)
    n_clouds = len(SIMULATION.clouds)
    t_s = np.linspace(0.0, float(n - 1), n, dtype=float)
    meta = SimulationMetadata(
        orbit_period_s=1.0,
        omega_rad_s=0.1,
        sim_total_s=float(n - 1),
        sim_dt_s=1.0,
        theta_start_rad=0.0,
        theta_end_rad=1.0,
        sat_theta_start_rad=0.0,
        sat_theta_span_rad=1.0,
        start_angle_deg=0.0,
        end_angle_deg=1.0,
        controller_mode="random",
        render_mode="headless",
    )
    sim_reward = np.zeros(n, dtype=float)
    sim_reward[1:] = np.arange(1, n, dtype=float) * 0.1
    torque = np.zeros(n, dtype=float)
    torque[1:] = np.linspace(0.1, 0.1 * (n - 1), n - 1)
    line_codes = np.zeros((n, n_bins), dtype=np.int8)
    return SimulationStateSeries(
        t_s=t_s,
        theta_orbit_rad=np.zeros(n, dtype=float),
        radius_km=np.ones(n, dtype=float),
        body_z_angle_rad=np.zeros(n, dtype=float),
        simulation_reward=sim_reward,
        wheel_torque_cmd_nm=torque,
        camera_gsd_m=np.ones(n, dtype=float),
        camera_vertical_fov_rad=0.5,
        camera_ground_left_xy_km=np.zeros((n, 2), dtype=float),
        camera_ground_right_xy_km=np.zeros((n, 2), dtype=float),
        camera_ground_center_xy_km=np.zeros((n, 2), dtype=float),
        camera_center_first_hit_xy_km=np.full((n, 2), np.nan, dtype=float),
        camera_center_first_hit_is_cloud=np.zeros(n, dtype=bool),
        camera_center_ray_observation_code=np.zeros(n, dtype=np.int8),
        camera_cloud_blocked_fraction=np.zeros(n, dtype=float),
        camera_observation_line_codes=line_codes,
        sat_subpoint_lat_deg=np.zeros(n, dtype=float),
        sat_subpoint_lon_deg=np.zeros(n, dtype=float),
        sat_altitude_m=np.ones(n, dtype=float) * 400_000.0,
        camera_ground_left_lon_lat_deg=np.zeros((n, 2), dtype=float),
        camera_ground_right_lon_lat_deg=np.zeros((n, 2), dtype=float),
        camera_ground_center_lon_lat_deg=np.zeros((n, 2), dtype=float),
        target_area_intersection_ratio=np.zeros(n, dtype=float),
        target_area_novelty_ratio=np.zeros(n, dtype=float),
        cloud_arc_radius_km=np.full((n, n_clouds), np.nan, dtype=float),
        cloud_arc_start_rad=np.full((n, n_clouds), np.nan, dtype=float),
        cloud_arc_end_rad=np.full((n, n_clouds), np.nan, dtype=float),
        metadata=meta,
    )


def _synthetic_episode(*, obs_dim: int, n_frames: int, n_bins: int) -> EpisodeResult:
    series = _minimal_state_series(n_frames=n_frames, n_bins=n_bins)
    steps = n_frames - 1
    states = [np.full((obs_dim,), float(i), dtype=np.float32) for i in range(n_frames)]
    ep_ret = float(np.sum(series.simulation_reward[1:]))
    return EpisodeResult(
        episode_return=ep_ret,
        steps=steps,
        states=states,
        simulation_series=series,
        configured_controller_update_interval_s=1.0,
        effective_controller_update_interval_s=1.0,
        effective_controller_update_interval_steps=1,
    )


class _RecordingAgent:
    """Minimal ``MPOAgent.store`` stand-in for buffer hydration tests."""

    def __init__(self, *, obs_size: int, action_size: int) -> None:
        self.buffer = ReplayBuffer(
            500, obs_size, action_size, torch.device("cpu")
        )
        self.step_counter = 0
        self.current_ep_return = 0.0
        self.episode_returns: list[float] = []

    def store(self, transition: tuple[np.ndarray, np.ndarray, float, np.ndarray, bool]) -> None:
        obs, action, reward, next_obs, done = transition
        self.current_ep_return += float(reward)
        self.step_counter += 1
        if done:
            self.episode_returns.append(self.current_ep_return)
            self.current_ep_return = 0.0
        self.buffer.store(obs, next_obs, action, reward, done)


def _fake_env(*, obs_dim: int, max_episode_steps: int = 10_000) -> SimpleNamespace:
    high = np.ones((obs_dim,), dtype=np.float32)
    return SimpleNamespace(
        observation_space=spaces.Box(-high, high, dtype=np.float32),
        action_space=spaces.Box(
            low=np.array([-1.0], dtype=np.float32),
            high=np.array([1.0], dtype=np.float32),
            shape=(1,),
            dtype=np.float32,
        ),
        max_episode_steps=max_episode_steps,
    )


class NotebookWarmupBundleCacheTest(unittest.TestCase):
    def test_digest_stable_and_seed_sensitive(self):
        fp1 = warmup_fingerprint_payload(
            obs_dim=11,
            action_dim=1,
            max_episode_steps=100,
            camera_observation_line_n_bins=int(SIMULATION.camera_observation_line_n_bins),
            satellite_altitude_m=400_000.0,
            base_seed=7,
            episode_count=16,
            warmup_controller="random",
            feature_config=None,
        )
        fp2 = dict(fp1)
        fp2["base_seed"] = 8
        self.assertEqual(digest_for_warmup_fingerprint(fp1), digest_for_warmup_fingerprint(fp1))
        self.assertNotEqual(digest_for_warmup_fingerprint(fp1), digest_for_warmup_fingerprint(fp2))

        fp3 = dict(fp1)
        fp3["episode_count"] = 17
        self.assertNotEqual(digest_for_warmup_fingerprint(fp1), digest_for_warmup_fingerprint(fp3))

    def test_satellite_altitude_magnitude_pint_like(self):
        try:
            from environment_definition.constants import UREG as ureg
        except Exception:
            self.skipTest("UNIT_REGISTRY unavailable")
        q = 500_000 * ureg.meter
        self.assertEqual(satellite_altitude_m_to_float(q), 500_000.0)

    def test_save_load_roundtrip(self):
        import tempfile
        from pathlib import Path

        obs_dim = 5
        n_bins = int(SIMULATION.camera_observation_line_n_bins)
        ep = _synthetic_episode(obs_dim=obs_dim, n_frames=5, n_bins=n_bins)
        env = _fake_env(obs_dim=obs_dim)

        fp = warmup_fingerprint_payload(
            obs_dim=obs_dim,
            action_dim=1,
            max_episode_steps=int(env.max_episode_steps),
            camera_observation_line_n_bins=n_bins,
            satellite_altitude_m=400_000.0,
            base_seed=0,
            episode_count=1,
            warmup_controller="random",
            feature_config=None,
        )
        digest = digest_for_warmup_fingerprint(fp)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bdir = bundle_dir_for_digest(digest, cache_root=root)
            save_warmup_episode_bundle(bdir, digest_hex=digest, fingerprint=fp, episodes=[ep])

            meta = json.loads((bdir / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["digest_sha256_hex"], digest)
            self.assertEqual(meta["nb_warmup_bundle_version"], NB_WARMUP_BUNDLE_VERSION)

            loaded = try_load_warmup_episode_bundle(
                bdir,
                expected_fingerprint=fp,
                expected_digest_hex=digest,
                env=env,
            )
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(len(loaded), 1)
            self.assertAlmostEqual(float(loaded[0].episode_return), float(ep.episode_return))
            np.testing.assert_array_equal(loaded[0].simulation_series.t_s, ep.simulation_series.t_s)

    def test_preload_buffer_torques_match_series(self):
        obs_dim = 4
        n_bins = int(SIMULATION.camera_observation_line_n_bins)
        ep = _synthetic_episode(obs_dim=obs_dim, n_frames=6, n_bins=n_bins)
        agent = _RecordingAgent(obs_size=obs_dim, action_size=1)
        n = preload_warmup_buffer_from_episodes(agent, [ep])
        self.assertEqual(n, ep.steps)
        self.assertEqual(agent.buffer.count, ep.steps)
        for i in range(ep.steps):
            torque = float(ep.simulation_series.wheel_torque_cmd_nm[i + 1])
            self.assertAlmostEqual(float(agent.buffer.actions[i, 0]), torque)
            self.assertAlmostEqual(float(agent.buffer.rewards[i]), float(ep.simulation_series.simulation_reward[i + 1]))

    def test_reset_agent_replay_counters(self):
        obs_dim = 3
        agent = _RecordingAgent(obs_size=obs_dim, action_size=1)
        ep = _synthetic_episode(obs_dim=obs_dim, n_frames=4, n_bins=int(SIMULATION.camera_observation_line_n_bins))
        preload_warmup_buffer_from_episodes(agent, [ep])
        self.assertGreater(agent.buffer.count, 0)
        reset_agent_replay_counters(agent)
        self.assertEqual(agent.buffer.count, 0)
        self.assertEqual(agent.step_counter, 0)

    def test_rebuild_deletes_and_reinvokes_run_episode(self):
        import tempfile
        from pathlib import Path

        obs_dim = 4
        n_bins = int(SIMULATION.camera_observation_line_n_bins)
        ep = _synthetic_episode(obs_dim=obs_dim, n_frames=4, n_bins=n_bins)
        env = _fake_env(obs_dim=obs_dim)
        fake_agent = _RecordingAgent(obs_size=obs_dim, action_size=1)

        fp = warmup_fingerprint_payload(
            obs_dim=obs_dim,
            action_dim=1,
            max_episode_steps=int(env.max_episode_steps),
            camera_observation_line_n_bins=n_bins,
            satellite_altitude_m=400_000.0,
            base_seed=99,
            episode_count=2,
            warmup_controller="random",
            feature_config=None,
        )
        digest = digest_for_warmup_fingerprint(fp)

        calls: list[int] = []

        def _fake_run(ep_env, ep_agent, **kwargs):
            calls.append(len(calls))
            self.assertIs(ep_env, env)
            self.assertIs(ep_agent, fake_agent)
            return ep

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bdir_old = bundle_dir_for_digest(digest, cache_root=root)
            save_warmup_episode_bundle(bdir_old, digest_hex=digest, fingerprint=fp, episodes=[ep, ep])

            with patch(
                "autonomous_control.notebook_warmup_bundle_cache.run_episode",
                side_effect=_fake_run,
            ):
                out = load_or_build_notebook_random_warmup_episodes(
                    env=env,
                    agent=fake_agent,
                    base_seed=99,
                    episode_count=2,
                    satellite_altitude=400_000.0,
                    rebuild=True,
                    cache_root=root,
                    train_updates_per_step=0,
                )
                self.assertEqual(len(out), 2)
                self.assertEqual(len(calls), 2)

            meta_path = bundle_dir_for_digest(digest, cache_root=root) / "meta.json"
            self.assertTrue(meta_path.exists())


if __name__ == "__main__":
    unittest.main()
