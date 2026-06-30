"""Frozen S01 training knobs for ml_sac_vector_budget_penalty (dt 1.5s, 50 train eps)."""

from __future__ import annotations

import importlib.util
from dataclasses import replace
from pathlib import Path

from autonomous_control.mpo_config import MPOConfig
from s01_utils.training_workflow import TrainingWorkflowConfig

_OVERNIGHT = Path(__file__).resolve().parents[1] / "ml_algo_overnight"
_spec = importlib.util.spec_from_file_location(
    "ml_overnight_frozen_baseline_budget",
    _OVERNIGHT / "_frozen_baseline.py",
)
assert _spec and _spec.loader
_overnight_fb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_overnight_fb)

BASELINE_WARMUP_RETURN_MEAN = _overnight_fb.BASELINE_WARMUP_RETURN_MEAN
EVAL_EPISODES = _overnight_fb.EVAL_EPISODES
EXPERIMENT_SEED = _overnight_fb.EXPERIMENT_SEED
WARMUP_EPISODES = _overnight_fb.WARMUP_EPISODES
TRAIN_EPISODES = 50
TRAIN_EPISODES_DEFAULT = TRAIN_EPISODES

SAC_LEARNING_RATE_PI = 4.5e-4
SAC_LEARNING_RATE_Q = 1.0e-3
SAC_ACTOR_DROPOUT = 0.0

# Exp 4 Ref1 canonical run — read-only baseline for Phase 2 comparison (no re-run).
EXP4_REF1_BASELINE_RUN_DIR = (
    "9998217182442815_ml_ref_ref1_vector_11-05-57"
)


def frozen_training_config(
    *,
    run_id: str | None = None,
    train_episodes: int | None = None,
    rebuild_warmup_bundle_cache: bool = False,
    experiment_name: str | None = None,
) -> TrainingWorkflowConfig:
    cfg = _overnight_fb.frozen_training_config(
        run_id=run_id,
        train_episodes=int(train_episodes if train_episodes is not None else TRAIN_EPISODES),
        rebuild_warmup_bundle_cache=rebuild_warmup_bundle_cache,
    )
    if experiment_name is not None:
        cfg = replace(cfg, experiment_name=experiment_name)
    return replace(cfg, attitude_request_mode="vector")  # type: ignore[arg-type]


def sac_mpo_config_overrides(base: MPOConfig | None = None) -> MPOConfig:
    cfg = base if base is not None else MPOConfig()
    return replace(
        cfg,
        learning_rate_pi=SAC_LEARNING_RATE_PI,
        learning_rate_q=SAC_LEARNING_RATE_Q,
        actor_dropout=SAC_ACTOR_DROPOUT,
    )


__all__ = [
    "BASELINE_WARMUP_RETURN_MEAN",
    "EVAL_EPISODES",
    "EXPERIMENT_SEED",
    "EXP4_REF1_BASELINE_RUN_DIR",
    "SAC_ACTOR_DROPOUT",
    "SAC_LEARNING_RATE_PI",
    "SAC_LEARNING_RATE_Q",
    "TRAIN_EPISODES",
    "TRAIN_EPISODES_DEFAULT",
    "WARMUP_EPISODES",
    "frozen_training_config",
    "sac_mpo_config_overrides",
]
