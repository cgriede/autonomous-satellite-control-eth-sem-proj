"""Frozen S01 notebook-08 training knobs for ML learning-signal hypothesis cycle."""

from __future__ import annotations

from dataclasses import replace

from s01_utils.training_workflow import S01_TRAINING_FEATURE_CONFIG, TrainingWorkflowConfig

EXPERIMENT_SEED = 7
WARMUP_EPISODES = 5
TRAIN_EPISODES = 3
EVAL_EPISODES = 0
MAX_BRANCH_RUNS = 3

# Baseline deterministic warmup mean return from today's cached bundle (reference KPI).
BASELINE_WARMUP_RETURN_MEAN = 89.0


def frozen_training_config(*, run_id: str | None = None) -> TrainingWorkflowConfig:
    """Production-aligned config: cached warmup + 3 train episodes, no eval."""
    return replace(
        TrainingWorkflowConfig(),
        seed=EXPERIMENT_SEED,
        warmup_episodes=WARMUP_EPISODES,
        train_episodes=TRAIN_EPISODES,
        eval_episodes=EVAL_EPISODES,
        use_warmup_bundle_cache=True,
        rebuild_warmup_bundle_cache=False,
        background_artifacts=False,
        collect_states=False,
        feature_config=S01_TRAINING_FEATURE_CONFIG,
        run_id=run_id,
    )


__all__ = [
    "BASELINE_WARMUP_RETURN_MEAN",
    "EVAL_EPISODES",
    "EXPERIMENT_SEED",
    "MAX_BRANCH_RUNS",
    "TRAIN_EPISODES",
    "WARMUP_EPISODES",
    "frozen_training_config",
]
