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
from autonomous_control.controller_observation import ControllerObservationLayout
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.training_runtime import make_attitude_control_env, run_episode
from paths import RUNS_ROOT

CACHE_VERSION = 2


def default_cache_dir() -> Path:
	"""Return the canonical cache directory for warmup replay data."""
	out = RUNS_ROOT / "cached_warmup"
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
	layout: ControllerObservationLayout,
	action_size: int,
) -> None:
	"""Validate that a cache payload matches the current agent layout."""
	required = ("scalars", "next_scalars", "actions", "rewards", "done", "cache_version")
	missing = [k for k in required if k not in cache]
	if missing:
		raise ValueError(f"Warmup cache missing keys: {missing}")

	scalars = np.asarray(cache["scalars"])
	next_scalars = np.asarray(cache["next_scalars"])
	actions = np.asarray(cache["actions"])
	rewards = np.asarray(cache["rewards"])
	done = np.asarray(cache["done"])

	if scalars.ndim != 2 or scalars.shape[1] != layout.scalar_dim:
		raise ValueError(
			f"Expected scalars shape (N,{layout.scalar_dim}), got {scalars.shape}."
		)
	if next_scalars.shape != scalars.shape:
		raise ValueError(f"next_scalars shape {next_scalars.shape} != scalars {scalars.shape}.")
	if actions.ndim != 2 or actions.shape[1] != int(action_size):
		raise ValueError(f"Expected actions shape (N,{action_size}), got {actions.shape}.")

	n = scalars.shape[0]
	if next_scalars.shape[0] != n or actions.shape[0] != n or rewards.shape[0] != n or done.shape[0] != n:
		raise ValueError("Warmup cache arrays must have identical first dimension N.")

	for key, seq_len in zip(layout.vision_keys, layout.vision_seq_lens):
		cache_key = layout.vision_cache_key(key)
		next_key = f"next_{cache_key}"
		if cache_key not in cache or next_key not in cache:
			raise ValueError(f"Warmup cache missing vision arrays for {key!r}.")
		vision = np.asarray(cache[cache_key])
		next_vision = np.asarray(cache[next_key])
		if vision.shape != (n, seq_len) or next_vision.shape != (n, seq_len):
			raise ValueError(
				f"Expected vision arrays shape (N,{seq_len}) for {key!r}, "
				f"got {vision.shape} and {next_vision.shape}."
			)

	if int(np.asarray(cache["cache_version"]).reshape(-1)[0]) != CACHE_VERSION:
		raise ValueError(
			f"Warmup cache version mismatch: expected {CACHE_VERSION}, rebuild the cache."
		)


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
		layout=agent.layout,
		action_size=int(agent.action_size),
	)

	scalars = np.asarray(cache["scalars"], dtype=np.float32)
	next_scalars = np.asarray(cache["next_scalars"], dtype=np.float32)
	actions = np.asarray(cache["actions"], dtype=np.float32)
	rewards = np.asarray(cache["rewards"], dtype=np.float32)
	done = np.asarray(cache["done"], dtype=np.float32)

	n = int(scalars.shape[0])
	n = min(n, int(agent.buffer.size))
	if max_samples is not None:
		n = min(n, int(max_samples))
	if n <= 0:
		return 0

	buf = agent.buffer
	buf.scalars[:n] = scalars[:n]
	buf.next_scalars[:n] = next_scalars[:n]
	for key in agent.layout.vision_keys:
		cache_key = agent.layout.vision_cache_key(key)
		buf.vision[cache_key][:n] = np.asarray(cache[cache_key], dtype=np.int8)[:n]
		buf.next_vision[cache_key][:n] = np.asarray(cache[f"next_{cache_key}"], dtype=np.int8)[:n]
	buf.actions[:n] = actions[:n]
	buf.rewards[:n] = rewards[:n]
	buf.done[:n] = done[:n]
	buf.count = n
	buf.ptr = n % int(buf.size)

	agent.step_counter = max(int(agent.step_counter), n)
	return n


def _cache_payload_from_agent(agent: MPOAgent, *, count: int) -> dict[str, np.ndarray]:
	buf = agent.buffer
	payload: dict[str, np.ndarray] = {
		"scalars": buf.scalars[:count].copy(),
		"next_scalars": buf.next_scalars[:count].copy(),
		"actions": buf.actions[:count].copy(),
		"rewards": buf.rewards[:count].copy(),
		"done": buf.done[:count].copy(),
		"cache_version": np.asarray([int(CACHE_VERSION)], dtype=np.int64),
		"scalar_dim": np.asarray([int(agent.layout.scalar_dim)], dtype=np.int64),
		"action_size": np.asarray([int(agent.action_size)], dtype=np.int64),
		"buffer_size": np.asarray([int(agent.buffer.size)], dtype=np.int64),
	}
	for key in agent.layout.vision_keys:
		cache_key = agent.layout.vision_cache_key(key)
		payload[cache_key] = buf.vision[cache_key][:count].copy()
		payload[f"next_{cache_key}"] = buf.next_vision[cache_key][:count].copy()
	return payload


def build_warmup_cache(
	*,
	path: Path,
	seed: int,
	episode_count: int,
	satellite_altitude: Any,
	warmup_controller: str = "baseline",
) -> dict[str, Any]:
	"""Run warmup episodes and save replay transitions to ``path``.

	This creates a temporary environment + agent dedicated to cache generation.
	"""
	if episode_count <= 0:
		raise ValueError("episode_count must be > 0.")

	env = make_attitude_control_env()
	cfg = MPOConfig(warmup_episodes=0)
	agent = MPOAgent(env, config=cfg)

	import sys
	from pathlib import Path

	s01 = Path(__file__).resolve().parents[1] / "notebooks" / "s01"
	if str(s01) not in sys.path:
		sys.path.insert(0, str(s01))
	from s01_utils.baseline_overflight import build_baseline_overflight_setup

	mission_setup = build_baseline_overflight_setup(seed=int(seed), n_targets=3)

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
			setup=mission_setup,
			np_rng=np.random.default_rng(derive_seed(seed, "warmup_cache", ep)),
		)
		episode_returns.append(float(result.episode_return))
		episode_steps.append(int(result.steps))

	count = int(len(agent.buffer))
	payload = _cache_payload_from_agent(agent, count=count)
	payload["episode_returns"] = np.asarray(episode_returns, dtype=np.float32)
	payload["episode_steps"] = np.asarray(episode_steps, dtype=np.int32)
	payload["seed"] = np.asarray([int(seed)], dtype=np.int64)
	payload["episode_count"] = np.asarray([int(episode_count)], dtype=np.int64)
	save_warmup_cache(path, payload=payload)

	return {
		"path": str(path),
		"seed": int(seed),
		"episodes": int(episode_count),
		"samples": int(count),
		"scalar_dim": int(agent.layout.scalar_dim),
		"action_size": int(agent.action_size),
	}


def load_or_build_warmup_cache(
	*,
	path: Path,
	seed: int,
	episode_count: int,
	satellite_altitude: Any,
	rebuild: bool = False,
	warmup_controller: str = "baseline",
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
