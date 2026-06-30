"""Frozen S01 training knobs for ml_modular_encoder (dt 1.5s SAC sparse slice)."""

from __future__ import annotations

import sys
from pathlib import Path

_OVERNIGHT = Path(__file__).resolve().parents[1] / "ml_algo_overnight"
if str(_OVERNIGHT) not in sys.path:
    sys.path.insert(0, str(_OVERNIGHT))

from _frozen_baseline import (  # noqa: E402
    BASELINE_WARMUP_RETURN_MEAN,
    EVAL_EPISODES,
    EXPERIMENT_SEED,
    TRAIN_EPISODES,
    TRAIN_EPISODES_DEFAULT,
    WARMUP_EPISODES,
    frozen_training_config,
)

__all__ = [
    "BASELINE_WARMUP_RETURN_MEAN",
    "EVAL_EPISODES",
    "EXPERIMENT_SEED",
    "TRAIN_EPISODES",
    "TRAIN_EPISODES_DEFAULT",
    "WARMUP_EPISODES",
    "frozen_training_config",
]
