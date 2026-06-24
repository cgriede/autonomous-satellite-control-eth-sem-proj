"""Preflight checks for every feature used by MPO train/eval scripts.

When adding a new training-facing feature, register a check in
``TRAINING_FEATURE_CHECKS`` and add coverage in ``backend/tests/test_mpo_training_features.py``
or ``backend/tests/test_training_preflight.py``.

Main entry points (``scripts/train_sat_agent.py``, ``scripts/eval_sat_agent.py``) call
``run_training_preflight()`` before training unless ``--skip-preflight`` is set.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch

from environment_definition.constants import SIMULATION

from .config.randomness import RandomnessConfig, apply_global_seed, derive_seed
from .controller_agent import MPOAgent
from .controller_baselines import MaxTorqueSweepPolicy, RandomTorquePolicy
from paths import MODELS_ROOT

from .feature_selection import ControllerFeatureConfig, select_controller_inputs_from_timestep
from .notebook_warmup_bundle_cache import encode_feature_config_snapshot
from .mpo_config import MPOConfig
from .controller_observation import (
    ControllerObservation,
    build_controller_observation_from_timestep,
    controller_observation_layout,
)
from .training_runtime import (
    ReplayBuffer,
    build_state_vector_from_timestep,
    controller_observation_dim,
    make_attitude_control_env,
)
from .warmup_cache import preload_agent_replay_buffer, validate_warmup_cache
from simulation.state_types import SimulationTimestepState

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Pytest modules that must pass before main ML training scripts run.
PREFLIGHT_CACHE_VERSION = 1

# Source modules exercised by inline checks; invalidate cache when these change.
PREFLIGHT_SOURCE_PATHS: tuple[str, ...] = (
    "backend/autonomous_control/training_preflight.py",
    "backend/autonomous_control/training_runtime.py",
    "backend/autonomous_control/mpo_config.py",
    "backend/autonomous_control/controller_agent.py",
    "backend/autonomous_control/warmup_cache.py",
    "backend/autonomous_control/feature_selection.py",
    "backend/autonomous_control/controller_observation.py",
    "backend/autonomous_control/controller_baselines.py",
    "backend/autonomous_control/config/randomness.py",
    "backend/environment_definition/constants/SIMULATION.py",
)

TRAINING_TEST_PATHS: tuple[str, ...] = (
    "backend/tests/test_training_preflight.py",
    "backend/tests/test_mpo_training_features.py",
    "backend/tests/test_feature_selection.py",
    "backend/tests/test_linear_dummy_policy.py",
    "backend/tests/test_action_adapter.py",
    "backend/tests/test_warmup_cache.py",
    "backend/tests/test_notebook_warmup_bundle_cache.py",
    "backend/tests/test_training_runtime_episode_artifact.py",
    "backend/tests/test_episode_runner.py",
)


class TrainingPreflightError(RuntimeError):
    """Raised when one or more training feature checks fail."""


@dataclass(frozen=True)
class TrainingFeatureCheck:
    name: str
    description: str
    check: Callable[[], None]


def _minimal_timestep(*, n_bins: int | None = None) -> SimulationTimestepState:
    bins = int(n_bins if n_bins is not None else SIMULATION.camera_observation_line_n_bins)
    return SimulationTimestepState(
        step_idx=0,
        sim_time_s=0.0,
        sat_pos_xy_km=np.array([7000.0, 0.0], dtype=float),
        body_z_angle_rad=0.1,
        theta_orbit_rad=0.2,
        radius_km=7000.0,
        omega_sat_rad_s=0.01,
        omega_wheel_rad_s=0.0,
        reward=0.0,
        camera_observation_line_codes=np.zeros(bins, dtype=np.int8),
        camera_center_ray_observation_code=np.int8(0),
        secondary_camera_observation_line_codes=np.empty(0, dtype=np.int8),
    )


def check_mpo_config_loads() -> None:
    cfg = MPOConfig(warmup_episodes=0)
    if cfg.batch_size <= 0:
        raise AssertionError("MPOConfig.batch_size must be positive.")


def check_randomness_seeding() -> None:
    apply_global_seed(RandomnessConfig(seed=123))
    a = derive_seed(123, "preflight", 0)
    b = derive_seed(123, "preflight", 0)
    c = derive_seed(123, "preflight", 1)
    if a != b:
        raise AssertionError("derive_seed must be stable for identical inputs.")
    if a == c:
        raise AssertionError("derive_seed must differ across indices.")


def check_env_spaces() -> None:
    env = make_attitude_control_env()
    obs_shape = tuple(env.observation_space.shape)
    act_shape = tuple(env.action_space.shape)
    if len(obs_shape) != 1 or obs_shape[0] <= 0:
        raise AssertionError(f"Invalid observation space shape: {obs_shape}.")
    if act_shape != (2,):
        raise AssertionError(f"Expected action shape (2,), got {act_shape}.")


def check_controller_observation_dim_matches_env() -> None:
    env = make_attitude_control_env()
    expected = controller_observation_dim()
    actual = int(np.prod(env.observation_space.shape))
    if expected != actual:
        raise AssertionError(
            f"controller_observation_dim ({expected}) != env obs dim ({actual})."
        )


def check_feature_selection_from_timestep() -> None:
    ts = _minimal_timestep()
    selected = select_controller_inputs_from_timestep(timestep=ts)
    cfg = ControllerFeatureConfig()
    for key in cfg.selected_keys:
        if key not in selected:
            raise AssertionError(f"Missing selected feature key: {key}.")


def check_build_state_vector_from_timestep() -> None:
    ts = _minimal_timestep()
    vec = build_state_vector_from_timestep(timestep=ts)
    expected_dim = controller_observation_dim()
    if vec.shape != (expected_dim,):
        raise AssertionError(f"State vector shape {vec.shape} != ({expected_dim},).")
    if vec.dtype != np.float32:
        raise AssertionError(f"State vector dtype must be float32, got {vec.dtype}.")


def check_replay_buffer_store_sample() -> None:
    device = torch.device("cpu")
    env = make_attitude_control_env()
    layout = env.observation_layout
    action_size = int(np.prod(env.action_space.shape))
    batch_size = 4
    buf = ReplayBuffer(32, layout, action_size, device)
    obs = build_controller_observation_from_timestep(timestep=_minimal_timestep())
    for i in range(10):
        tagged = ControllerObservation(
            scalars=obs.scalars + float(i),
            vision=obs.vision,
        )
        act = np.array([0.1, -1.0], dtype=np.float32)
        buf.store(tagged, tagged, act, 1.0, False)
    if len(buf) != 10:
        raise AssertionError(f"Expected buffer count 10, got {len(buf)}.")
    (scalars, vision), act_t, (next_scalars, next_vision), done_t, rew_t = buf.sample(
        batch_size
    )
    if scalars.shape != (batch_size, layout.scalar_dim):
        raise AssertionError(f"Unexpected sample scalars shape: {scalars.shape}.")
    if act_t.shape != (batch_size, action_size):
        raise AssertionError(f"Unexpected sample action shape: {act_t.shape}.")
    _ = next_scalars, next_vision, done_t, rew_t


def check_mpo_agent_store_get_action_train() -> None:
    env = make_attitude_control_env()
    cfg = MPOConfig(
        batch_size=4,
        warmup_episodes=0,
        buffer_size=64,
        num_samples_q=4,
        num_samples_pi=4,
    )
    agent = MPOAgent(env, config=cfg)
    obs = build_controller_observation_from_timestep(timestep=_minimal_timestep())
    for _ in range(12):
        action = np.array([0.0, -1.0], dtype=np.float32)
        agent.store((obs, action, 0.5, obs, False))
    agent.step_counter = max(agent.step_counter, cfg.batch_size)
    action = agent.get_action(obs, train=True)
    if action.shape != (2,):
        raise AssertionError(f"get_action shape must be (2,), got {action.shape}.")
    metrics = agent.train()
    if metrics is None:
        raise AssertionError("MPOAgent.train() returned None after buffer fill.")
    for key in ("q_loss", "pi_loss", "eta", "kl"):
        if key not in metrics:
            raise AssertionError(f"Missing train metric: {key}.")


def check_warmup_cache_preload() -> None:
    env = make_attitude_control_env()
    cfg = MPOConfig(warmup_episodes=0, buffer_size=64)
    agent = MPOAgent(env, config=cfg)
    layout = agent.layout
    action_size = agent.action_size
    obs = build_controller_observation_from_timestep(timestep=_minimal_timestep())
    n = 6
    cache = {
        "scalars": np.stack([obs.scalars + float(i) for i in range(n)], axis=0),
        "next_scalars": np.stack([obs.scalars + float(i + 1) for i in range(n)], axis=0),
        "actions": np.zeros((n, action_size), dtype=np.float32),
        "rewards": np.ones(n, dtype=np.float32),
        "done": np.array([0, 0, 0, 0, 0, 1], dtype=np.float32),
        "cache_version": np.asarray([2], dtype=np.int64),
    }
    for key, seq_len in zip(layout.vision_keys, layout.vision_seq_lens):
        cache_key = layout.vision_cache_key(key)
        cache[cache_key] = np.zeros((n, seq_len), dtype=np.int8)
        cache[f"next_{cache_key}"] = np.zeros((n, seq_len), dtype=np.int8)
    validate_warmup_cache(cache, layout=layout, action_size=action_size)
    loaded = preload_agent_replay_buffer(agent=agent, cache=cache, max_samples=4)
    if loaded != 4:
        raise AssertionError(f"Expected 4 preloaded samples, got {loaded}.")


def check_baseline_policies() -> None:
    env = make_attitude_control_env()
    obs = np.zeros(int(np.prod(env.observation_space.shape)), dtype=np.float32)
    random_policy = RandomTorquePolicy(env, rng=np.random.default_rng(0))
    sweep_policy = MaxTorqueSweepPolicy(env, period_s=10.0)
    for policy in (random_policy, sweep_policy):
        action = policy.get_action(obs, train=False)
        if action.shape != (1,):
            raise AssertionError(f"Baseline action shape must be (1,), got {action.shape}.")


def check_checkpoint_payload_keys() -> None:
    """Verify checkpoint dict contract used by train/eval scripts."""
    env = make_attitude_control_env()
    agent = MPOAgent(env, config=MPOConfig(warmup_episodes=0))
    payload: dict[str, Any] = {
        "pi": agent.pi.state_dict(),
        "pi_target": agent.pi_target.state_dict(),
        "q1": agent.q1.state_dict(),
        "q2": agent.q2.state_dict(),
        "q1_target": agent.q1_target.state_dict(),
        "q2_target": agent.q2_target.state_dict(),
        "q_optimizer": agent.q_optimizer.state_dict(),
        "pi_optimizer": agent.pi_optimizer.state_dict(),
        "eta_optimizer": agent.eta_optimizer.state_dict(),
        "log_eta": float(agent.log_eta.detach().cpu().item()),
        "step_counter": agent.step_counter,
        "episode_returns": agent.episode_returns,
    }
    required = (
        "pi",
        "pi_target",
        "q1",
        "q2",
        "q1_target",
        "q2_target",
        "q_optimizer",
        "pi_optimizer",
        "eta_optimizer",
        "log_eta",
    )
    missing = [k for k in required if k not in payload]
    if missing:
        raise AssertionError(f"Checkpoint payload missing keys: {missing}.")


TRAINING_FEATURE_CHECKS: tuple[TrainingFeatureCheck, ...] = (
    TrainingFeatureCheck("mpo_config", "MPOConfig defaults load", check_mpo_config_loads),
    TrainingFeatureCheck(
        "randomness",
        "RandomnessConfig seeding and derive_seed",
        check_randomness_seeding,
    ),
    TrainingFeatureCheck(
        "env_spaces",
        "make_attitude_control_env observation/action spaces",
        check_env_spaces,
    ),
    TrainingFeatureCheck(
        "observation_dim",
        "controller_observation_dim matches env",
        check_controller_observation_dim_matches_env,
    ),
    TrainingFeatureCheck(
        "feature_selection",
        "select_controller_inputs_from_timestep",
        check_feature_selection_from_timestep,
    ),
    TrainingFeatureCheck(
        "state_vector",
        "build_state_vector_from_timestep",
        check_build_state_vector_from_timestep,
    ),
    TrainingFeatureCheck(
        "replay_buffer",
        "ReplayBuffer store and sample",
        check_replay_buffer_store_sample,
    ),
    TrainingFeatureCheck(
        "mpo_agent",
        "MPOAgent store, get_action, train",
        check_mpo_agent_store_get_action_train,
    ),
    TrainingFeatureCheck(
        "warmup_cache",
        "warmup cache validate and preload",
        check_warmup_cache_preload,
    ),
    TrainingFeatureCheck(
        "baseline_policies",
        "RandomTorquePolicy and MaxTorqueSweepPolicy",
        check_baseline_policies,
    ),
    TrainingFeatureCheck(
        "checkpoint_contract",
        "train/eval checkpoint payload keys",
        check_checkpoint_payload_keys,
    ),
)


def run_training_preflight(
    *,
    checks: tuple[TrainingFeatureCheck, ...] | None = None,
) -> None:
    """Run all registered training feature checks; raise on first batch of failures."""
    selected = checks if checks is not None else TRAINING_FEATURE_CHECKS
    failures: list[str] = []
    for item in selected:
        try:
            item.check()
        except Exception as exc:  # noqa: BLE001 — collect all failures for one report
            failures.append(f"{item.name}: {exc}")
    if failures:
        detail = "\n".join(f"  - {line}" for line in failures)
        raise TrainingPreflightError(
            f"Training preflight failed ({len(failures)} check(s)):\n{detail}"
        )


def run_training_pytest_suite(
    *,
    test_paths: tuple[str, ...] | None = None,
    repo_root: Path | None = None,
) -> None:
    """Run the training pytest modules; raise TrainingPreflightError on failure."""
    root = repo_root if repo_root is not None else BACKEND_DIR.parent
    paths = test_paths if test_paths is not None else TRAINING_TEST_PATHS
    cmd = [sys.executable, "-m", "pytest", *paths, "-q", "--tb=short"]
    result = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True)
    if result.returncode != 0:
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        combined = "\n".join(part for part in (stdout, stderr) if part)
        raise TrainingPreflightError(
            f"Training pytest suite failed (exit {result.returncode}).\n{combined}"
        )


def _repo_root() -> Path:
    return BACKEND_DIR.parent


def _file_stat_signature(path: Path) -> dict[str, int] | None:
    if not path.is_file():
        return None
    stat = path.stat()
    return {"mtime_ns": int(stat.st_mtime_ns), "size": int(stat.st_size)}


def training_preflight_fingerprint_payload(
    *,
    feature_config: ControllerFeatureConfig | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root if repo_root is not None else _repo_root()
    rel_paths = sorted(set(TRAINING_TEST_PATHS) | set(PREFLIGHT_SOURCE_PATHS))
    files: dict[str, dict[str, int]] = {}
    for rel in rel_paths:
        sig = _file_stat_signature(root / rel)
        if sig is not None:
            files[rel] = sig
    return {
        "check_names": tuple(item.name for item in TRAINING_FEATURE_CHECKS),
        "feature_config": encode_feature_config_snapshot(feature_config),
        "files": files,
        "preflight_cache_version": int(PREFLIGHT_CACHE_VERSION),
    }


def digest_for_training_preflight_fingerprint(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def default_training_preflight_cache_path() -> Path:
    cache_dir = MODELS_ROOT / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "training_preflight_gate.json"


def _load_preflight_cache_entry(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _save_preflight_cache_entry(path: Path, *, digest: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "digest": digest,
        "passed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_training_gate(
    *,
    skip_pytest: bool = False,
    use_cache: bool = False,
    force: bool = False,
    feature_config: ControllerFeatureConfig | None = None,
    cache_path: Path | None = None,
) -> bool:
    """Inline preflight checks plus optional full pytest suite.

    When ``use_cache`` is True and the fingerprint matches a prior successful run,
    skip all checks and return False. Otherwise run checks, update the cache, and
    return True. CLI entry points leave ``use_cache`` at its default (False).
    """
    cache_file = cache_path if cache_path is not None else default_training_preflight_cache_path()
    fingerprint = training_preflight_fingerprint_payload(feature_config=feature_config)
    digest = digest_for_training_preflight_fingerprint(fingerprint)

    if use_cache and not force:
        cached = _load_preflight_cache_entry(cache_file)
        if cached is not None and cached.get("digest") == digest:
            passed_at = cached.get("passed_at_utc", "unknown time")
            print(
                f"Training preflight gate skipped (config unchanged; cached pass from {passed_at})."
            )
            return False

    run_training_preflight()
    if not skip_pytest:
        run_training_pytest_suite()

    if use_cache:
        _save_preflight_cache_entry(cache_file, digest=digest)
    return True


__all__ = [
    "PREFLIGHT_SOURCE_PATHS",
    "TRAINING_FEATURE_CHECKS",
    "TRAINING_TEST_PATHS",
    "TrainingFeatureCheck",
    "TrainingPreflightError",
    "default_training_preflight_cache_path",
    "digest_for_training_preflight_fingerprint",
    "run_training_gate",
    "run_training_preflight",
    "run_training_pytest_suite",
    "training_preflight_fingerprint_payload",
]
