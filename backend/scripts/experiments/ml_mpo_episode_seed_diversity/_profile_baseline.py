"""Exp 14 profile: hparam arms, feature config, episode counts."""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any

_OVERNIGHT = Path(__file__).resolve().parents[1] / "ml_algo_overnight"
_BACKEND = Path(__file__).resolve().parents[3]
_S01 = _BACKEND / "notebooks" / "s01"
for path in (_BACKEND, _S01):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from autonomous_control.feature_selection import ControllerFeatureConfig
from autonomous_control.mpo_config import MPOConfig
from s01_utils.training_workflow import TrainingWorkflowConfig

from _env_setup_fork import (
    SCREEN_CLOUD_SEED,
    SCREEN_MISSION_SEED,
    TRAIN_ENV_COUNT,
)
from _exp14_reward_fork import RewardForkMode

_PROFILE_PATH = Path(__file__).resolve().parent / "profile.json"
_PROFILE = json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
_WORKFLOW_KEYS = {f.name for f in fields(TrainingWorkflowConfig)}

_spec = importlib.util.spec_from_file_location(
    "ml_overnight_frozen_baseline_exp14",
    _OVERNIGHT / "_frozen_baseline.py",
)
assert _spec and _spec.loader
_parent_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parent_mod)
_parent_frozen_training_config = _parent_mod.frozen_training_config
EXPERIMENT_SEED = _parent_mod.EXPERIMENT_SEED

FEATURE_CONFIG = ControllerFeatureConfig(
    include_target_bearing_errors=True,
    include_captured_target_mask=True,
    include_capture_budget=True,
)

SCREEN_WARMUP_EP = 5
SCREEN_TRAIN_EP = 20
SCREEN_EVAL_EP = 1
STAGE_B_WARMUP_PER_ENV = 5
STAGE_B_TRAIN_PER_ENV = 30
STAGE_B_ENV_COUNT = TRAIN_ENV_COUNT


@dataclass(frozen=True)
class ScreenArmSpec:
    arm_id: str
    learning_rate_pi: float
    learning_rate_q: float
    batch_size: int
    entropy_coef: float
    reward_mode: RewardForkMode = "exp14_sparse"


SCREEN_ARMS: tuple[ScreenArmSpec, ...] = (
    ScreenArmSpec("hp_default", 1.5e-4, 4.5e-4, 256, 0.01),
    ScreenArmSpec(
        "hp_conservative",
        5e-5,
        1.5e-4,
        256,
        0.01,
        reward_mode="exp14_sparse_no_torque",
    ),
    ScreenArmSpec("hp_mid_batch", 1.5e-4, 4.5e-4, 512, 0.01),
    ScreenArmSpec("hp_aggressive", 4.5e-4, 1e-3, 512, 0.02),
    ScreenArmSpec(
        "hp_explore",
        1.5e-4,
        4.5e-4,
        256,
        0.05,
        reward_mode="exp14_capture_only",
    ),
)


def profile() -> dict[str, Any]:
    return dict(_PROFILE)


def shared_mpo_overrides() -> dict[str, Any]:
    base = dict(_PROFILE.get("mpo") or {})
    base.setdefault("decoupled_kl", True)
    base.setdefault("num_samples_q", 80)
    base.setdefault("num_samples_pi", 40)
    base.setdefault("max_target_index", 49)
    return base


def mpo_config_for_arm(spec: ScreenArmSpec) -> MPOConfig:
    overrides = shared_mpo_overrides()
    return replace(
        MPOConfig(),
        learning_rate_pi=float(spec.learning_rate_pi),
        learning_rate_q=float(spec.learning_rate_q),
        batch_size=int(spec.batch_size),
        decoupled_kl=bool(overrides.get("decoupled_kl", True)),
        num_samples_q=int(overrides.get("num_samples_q", 80)),
        num_samples_pi=int(overrides.get("num_samples_pi", 40)),
        max_target_index=int(overrides.get("max_target_index", 49)),
        actor_dropout=float(overrides.get("actor_dropout", 0.15)),
        warmup_episodes=int(overrides.get("warmup_episodes", 5)),
    )


def frozen_training_config(
    *,
    run_id: str | None = None,
    train_episodes: int | None = None,
    rebuild_warmup_bundle_cache: bool = False,
) -> TrainingWorkflowConfig:
    cfg = _parent_frozen_training_config(
        run_id=run_id,
        train_episodes=train_episodes,
        rebuild_warmup_bundle_cache=rebuild_warmup_bundle_cache,
    )
    overrides = {
        k: v for k, v in (_PROFILE.get("workflow") or {}).items() if k in _WORKFLOW_KEYS
    }
    overrides["attitude_request_mode"] = "vector"
    overrides["seed"] = int(_PROFILE.get("workflow", {}).get("seed", 7))
    if train_episodes is not None:
        overrides["train_episodes"] = int(train_episodes)
    return replace(cfg, **overrides)


def screen_env_seeds() -> tuple[int, int]:
    return SCREEN_MISSION_SEED, SCREEN_CLOUD_SEED


__all__ = [
    "EXPERIMENT_SEED",
    "FEATURE_CONFIG",
    "SCREEN_ARMS",
    "SCREEN_EVAL_EP",
    "SCREEN_TRAIN_EP",
    "SCREEN_WARMUP_EP",
    "STAGE_B_ENV_COUNT",
    "STAGE_B_TRAIN_PER_ENV",
    "STAGE_B_WARMUP_PER_ENV",
    "ScreenArmSpec",
    "frozen_training_config",
    "mpo_config_for_arm",
    "profile",
    "screen_env_seeds",
    "shared_mpo_overrides",
]
