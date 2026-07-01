"""Duck-type workflow + shared MPO knobs from profile.json."""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

_OVERNIGHT = Path(__file__).resolve().parents[1] / "ml_algo_overnight"
_BACKEND = Path(__file__).resolve().parents[3]
_S01 = _BACKEND / "notebooks" / "s01"
for path in (_BACKEND, _S01, _OVERNIGHT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from s01_utils.training_workflow import TrainingWorkflowConfig  # noqa: E402

_PROFILE_PATH = Path(__file__).resolve().parent / "profile.json"
_PROFILE = json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
_WORKFLOW_KEYS = {f.name for f in fields(TrainingWorkflowConfig)}

_spec = importlib.util.spec_from_file_location(
    "ml_overnight_frozen_baseline_mpo_safe_mode_penalty",
    _OVERNIGHT / "_frozen_baseline.py",
)
assert _spec and _spec.loader
_parent_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parent_mod)
_parent_frozen_training_config = _parent_mod.frozen_training_config
EXPERIMENT_SEED = _parent_mod.EXPERIMENT_SEED


def profile() -> dict[str, Any]:
    return dict(_PROFILE)


def shared_mpo_overrides() -> dict[str, Any]:
    return dict(_PROFILE.get("mpo") or {})


def safe_mode_penalty_knobs() -> dict[str, Any]:
    return dict(_PROFILE.get("safe_mode_penalty") or {})


def baseline_comparison() -> dict[str, Any]:
    return dict(_PROFILE.get("baseline_comparison") or {})


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
    if train_episodes is not None:
        overrides["train_episodes"] = int(train_episodes)
    return replace(cfg, **overrides)


__all__ = [
    "EXPERIMENT_SEED",
    "baseline_comparison",
    "frozen_training_config",
    "profile",
    "safe_mode_penalty_knobs",
    "shared_mpo_overrides",
]
