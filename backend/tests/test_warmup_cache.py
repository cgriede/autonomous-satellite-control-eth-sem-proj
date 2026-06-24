"""Tests for warmup replay cache helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from autonomous_control.controller_agent import MPOAgent
from autonomous_control.controller_observation import build_controller_observation_from_timestep
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.training_preflight import _minimal_timestep
from autonomous_control.training_runtime import make_attitude_control_env
from autonomous_control.warmup_cache import (
    CACHE_VERSION,
    load_warmup_cache,
    preload_agent_replay_buffer,
    save_warmup_cache,
    validate_warmup_cache,
)


class WarmupCacheTest(unittest.TestCase):
    def _synthetic_cache(self, *, layout, action_size: int, n: int) -> dict[str, np.ndarray]:
        obs = build_controller_observation_from_timestep(timestep=_minimal_timestep())
        cache: dict[str, np.ndarray] = {
            "scalars": np.stack([obs.scalars + float(i) for i in range(n)], axis=0),
            "next_scalars": np.stack([obs.scalars + float(i + 1) for i in range(n)], axis=0),
            "actions": np.zeros((n, action_size), dtype=np.float32),
            "rewards": np.linspace(0.1, 0.2, n, dtype=np.float32),
            "done": np.array([0.0] * (n - 1) + [1.0], dtype=np.float32),
            "cache_version": np.asarray([CACHE_VERSION], dtype=np.int64),
        }
        for key, seq_len in zip(layout.vision_keys, layout.vision_seq_lens):
            cache_key = layout.vision_cache_key(key)
            cache[cache_key] = np.zeros((n, seq_len), dtype=np.int8)
            cache[f"next_{cache_key}"] = np.zeros((n, seq_len), dtype=np.int8)
        return cache

    def test_validate_rejects_mismatched_scalar_dim(self):
        env = make_attitude_control_env()
        layout = env.observation_layout
        cache = self._synthetic_cache(layout=layout, action_size=1, n=3)
        cache["scalars"] = np.zeros((3, layout.scalar_dim + 1), dtype=np.float32)
        with self.assertRaises(ValueError):
            validate_warmup_cache(cache, layout=layout, action_size=1)

    def test_save_load_roundtrip(self):
        env = make_attitude_control_env()
        layout = env.observation_layout
        cache = self._synthetic_cache(layout=layout, action_size=1, n=4)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "cache.npz"
            save_warmup_cache(path, payload=cache)
            loaded = load_warmup_cache(path)
        np.testing.assert_array_equal(loaded["scalars"], cache["scalars"])
        np.testing.assert_array_equal(loaded["rewards"], cache["rewards"])

    def test_preload_respects_max_samples(self):
        env = make_attitude_control_env()
        agent = MPOAgent(env, config=MPOConfig(warmup_episodes=0, buffer_size=128))
        cache = self._synthetic_cache(
            layout=agent.layout,
            action_size=agent.action_size,
            n=20,
        )
        loaded = preload_agent_replay_buffer(agent=agent, cache=cache, max_samples=7)
        self.assertEqual(loaded, 7)
        self.assertEqual(agent.buffer.count, 7)


if __name__ == "__main__":
    unittest.main()
