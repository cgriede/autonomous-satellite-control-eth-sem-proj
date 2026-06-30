"""Frozen S01 training knobs for ml_sac_mpo_compare (dt 1.5s, up to 20 train eps)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_OVERNIGHT = Path(__file__).resolve().parents[1] / "ml_algo_overnight"
_spec = importlib.util.spec_from_file_location(
    "ml_overnight_frozen_baseline_compare",
    _OVERNIGHT / "_frozen_baseline.py",
)
assert _spec and _spec.loader
_overnight_fb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_overnight_fb)

BASELINE_WARMUP_RETURN_MEAN = _overnight_fb.BASELINE_WARMUP_RETURN_MEAN
EVAL_EPISODES = _overnight_fb.EVAL_EPISODES
EXPERIMENT_SEED = _overnight_fb.EXPERIMENT_SEED
TRAIN_EPISODES = _overnight_fb.TRAIN_EPISODES
TRAIN_EPISODES_DEFAULT = _overnight_fb.TRAIN_EPISODES_DEFAULT
WARMUP_EPISODES = _overnight_fb.WARMUP_EPISODES
frozen_training_config = _overnight_fb.frozen_training_config

COMPARE_TRAIN_EPISODES_DEFAULT = 20
PATIENCE_EPISODES_DEFAULT = 10

__all__ = [
    "BASELINE_WARMUP_RETURN_MEAN",
    "COMPARE_TRAIN_EPISODES_DEFAULT",
    "EVAL_EPISODES",
    "EXPERIMENT_SEED",
    "PATIENCE_EPISODES_DEFAULT",
    "TRAIN_EPISODES",
    "TRAIN_EPISODES_DEFAULT",
    "WARMUP_EPISODES",
    "frozen_training_config",
]
