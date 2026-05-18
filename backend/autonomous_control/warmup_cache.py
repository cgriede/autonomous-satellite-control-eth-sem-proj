"""Warmup replay cache helpers for faster MPO iteration.

This module stores warmup transitions to disk and can preload them into an
``MPOAgent`` replay buffer so training tweaks do not require rerunning warmup.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from autonomous_control.config.randomness import derive_seed
from autonomous_control.controller_agent import MPOAgent
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.training_runtime import make_attitude_control_env, run_episode
from paths import MODELS_ROOT

CACHE_VERSION = 1


def default_cache_dir() -> Path:
	"""Return the canonical cache directory for warmup replay data."""
	out = MODELS_ROOT / "cached_warmup"
	out.mkdir(parents=True, exist_ok=True)
	return out


def default_cache_path(*, seed: int, tag: str | None = None, cache_dir: Path | None = None) -> Path:
	"""Return a default cache filename scoped by seed and optional tag."""
	root = cache_dir if cache_dir is not None else default_cache_dir()
	suffix = f"_{tag}" if tag else ""
	return root / f"warmup_cache_seed{int(seed)}{suffix}.npz"


def save_warmup_cache(path: Path, *, payload: dict[str, np.ndarray]) -> None:
	"""Persist warmup replay payload to compressed ``.npz``."""
	path.parent.mkdir(parents=True, exist_ok=True)
	np.savez_compressed(path, **payload)  # type: ignore[arg-type]


def load_warmup_cache(path: Path) -> dict[str, np.ndarray]:
	"""Load warmup replay payload from disk."""
	if not path.exists():
		raise FileNotFoundError(f"Warmup cache does not exist: {path}")
	with np.load(path) as data:
		return {name: data[name] for name in data.files}


def validate_warmup_cache(
	cache: dict[str, np.ndarray],
	*,
	obs_size: int,
	action_size: int,
) -> None:
	"""Validate that a cache payload matches the current agent dimensions."""
	required = ("obs", "actions", "rewards", "next_obs", "done")
	missing = [k for k in required if k not in cache]
	if missing:
		raise ValueError(f"Warmup cache missing keys: {missing}")

	obs = np.asarray(cache["obs"])
	actions = np.asarray(cache["actions"])
	rewards = np.asarray(cache["rewards"])
	next_obs = np.asarray(cache["next_obs"])
	done = np.asarray(cache["done"])

	if obs.ndim != 2 or obs.shape[1] != int(obs_size):
		raise ValueError(f"Expected obs shape (N,{obs_size}), got {obs.shape}.")
	if next_obs.ndim != 2 or next_obs.shape[1] != int(obs_size):
		raise ValueError(f"Expected next_obs shape (N,{obs_size}), got {next_obs.shape}.")
	if actions.ndim != 2 or actions.shape[1] != int(action_size):
		raise ValueError(f"Expected actions shape (N,{action_size}), got {actions.shape}.")

	n = obs.shape[0]
	if next_obs.shape[0] != n or actions.shape[0] != n or rewards.shape[0] != n or done.shape[0] != n:
		raise ValueError("Warmup cache arrays must have identical first dimension N.")


def preload_agent_replay_buffer(
	*,
	agent: MPOAgent,
	cache: dict[str, np.ndarray],
	max_samples: int | None = None,
) -> int:
	"""Copy cached transitions into an agent replay buffer.

	Returns the number of loaded transitions.
	"""
	validate_warmup_cache(
		cache,
		obs_size=int(agent.obs_size),
		action_size=int(agent.action_size),
	)

	obs = np.asarray(cache["obs"], dtype=np.float32)
	actions = np.asarray(cache["actions"], dtype=np.float32)
	rewards = np.asarray(cache["rewards"], dtype=np.float32)
	next_obs = np.asarray(cache["next_obs"], dtype=np.float32)
	done = np.asarray(cache["done"], dtype=np.float32)

	n = int(obs.shape[0])
	n = min(n, int(agent.buffer.size))
	if max_samples is not None:
		n = min(n, int(max_samples))
	if n <= 0:
		return 0

	agent.buffer.obs[:n] = obs[:n]
	agent.buffer.actions[:n] = actions[:n]
	agent.buffer.rewards[:n] = rewards[:n]
	agent.buffer.next_obs[:n] = next_obs[:n]
	agent.buffer.done[:n] = done[:n]
	agent.buffer.count = n
	agent.buffer.ptr = n % int(agent.buffer.size)

	# Ensure training is not blocked by exploration-step gating after preload.
	agent.step_counter = max(int(agent.step_counter), n)
	return n


def build_warmup_cache(
	*,
	path: Path,
	seed: int,
	episode_count: int,
	satellite_altitude: Any,
	warmup_controller: str = "random",
) -> dict[str, Any]:
	"""Run warmup episodes and save replay transitions to ``path``.

	This creates a temporary environment + agent dedicated to cache generation.
	"""
	if episode_count <= 0:
		raise ValueError("episode_count must be > 0.")

	env = make_attitude_control_env()
	cfg = MPOConfig(warmup_episodes=0)
	agent = MPOAgent(env, config=cfg)

	episode_returns: list[float] = []
	episode_steps: list[int] = []
	for ep in range(int(episode_count)):
		result = run_episode(
			env,
			agent,
			mode="warmup",
			train_updates_per_step=0,
			warmup_controller=warmup_controller,
			satellite_altitude=satellite_altitude,
			np_rng=np.random.default_rng(derive_seed(seed, "warmup_cache", ep)),
		)
		episode_returns.append(float(result.episode_return))
		episode_steps.append(int(result.steps))

	count = int(len(agent.buffer))
	payload: dict[str, np.ndarray] = {
		"obs": agent.buffer.obs[:count].copy(),
		"actions": agent.buffer.actions[:count].copy(),
		"rewards": agent.buffer.rewards[:count].copy(),
		"next_obs": agent.buffer.next_obs[:count].copy(),
		"done": agent.buffer.done[:count].copy(),
		"episode_returns": np.asarray(episode_returns, dtype=np.float32),
		"episode_steps": np.asarray(episode_steps, dtype=np.int32),
		"seed": np.asarray([int(seed)], dtype=np.int64),
		"episode_count": np.asarray([int(episode_count)], dtype=np.int64),
		"obs_size": np.asarray([int(agent.obs_size)], dtype=np.int64),
		"action_size": np.asarray([int(agent.action_size)], dtype=np.int64),
		"buffer_size": np.asarray([int(agent.buffer.size)], dtype=np.int64),
		"cache_version": np.asarray([int(CACHE_VERSION)], dtype=np.int64),
	}
	save_warmup_cache(path, payload=payload)

	return {
		"path": str(path),
		"seed": int(seed),
		"episodes": int(episode_count),
		"samples": int(count),
		"obs_size": int(agent.obs_size),
		"action_size": int(agent.action_size),
	}


def load_or_build_warmup_cache(
	*,
	path: Path,
	seed: int,
	episode_count: int,
	satellite_altitude: Any,
	rebuild: bool = False,
	warmup_controller: str = "random",
) -> dict[str, np.ndarray]:
	"""Load warmup cache if present, otherwise build and load it."""
	if rebuild or (not path.exists()):
		build_warmup_cache(
			path=path,
			seed=seed,
			episode_count=episode_count,
			satellite_altitude=satellite_altitude,
			warmup_controller=warmup_controller,
		)
	return load_warmup_cache(path)


__all__ = [
	"CACHE_VERSION",
	"build_warmup_cache",
	"default_cache_dir",
	"default_cache_path",
	"load_or_build_warmup_cache",
	"load_warmup_cache",
	"preload_agent_replay_buffer",
	"save_warmup_cache",
	"validate_warmup_cache",
]
