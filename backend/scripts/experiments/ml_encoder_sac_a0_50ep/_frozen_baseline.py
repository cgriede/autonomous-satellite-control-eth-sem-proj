"""Duck-type sac_a0 TrainingWorkflowConfig from profile.json + modular encoder baseline."""

from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import fields, replace
from pathlib import Path

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
    "ml_algo_overnight_frozen_baseline_parent",
    _OVERNIGHT / "_frozen_baseline.py",
)
assert _spec and _spec.loader
_parent_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parent_mod)
_parent_frozen_training_config = _parent_mod.frozen_training_config


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


__all__ = ["frozen_training_config"]
