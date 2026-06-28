"""Frozen S01 training knobs for ml_algo_overnight hypothesis cycle."""

from __future__ import annotations

from dataclasses import replace

from s01_utils.training_workflow import S01_TRAINING_FEATURE_CONFIG, TrainingWorkflowConfig

EXPERIMENT_SEED = 7
WARMUP_EPISODES = 5
TRAIN_EPISODES_DEFAULT = 7
TRAIN_EPISODES_FAST = 10
EVAL_EPISODES = 2
BASELINE_WARMUP_RETURN_MEAN = 89.0

# Set by H0 via dt_profile.json; fallback before H0 runs.
TRAIN_EPISODES = TRAIN_EPISODES_DEFAULT


def frozen_training_config(
    *,
    run_id: str | None = None,
    train_episodes: int | None = None,
    rebuild_warmup_bundle_cache: bool = False,
) -> TrainingWorkflowConfig:
    n_train = int(train_episodes if train_episodes is not None else TRAIN_EPISODES)
    return replace(
        TrainingWorkflowConfig(),
        seed=EXPERIMENT_SEED,
        warmup_episodes=WARMUP_EPISODES,
        train_episodes=n_train,
        eval_episodes=EVAL_EPISODES,
        use_warmup_bundle_cache=True,
        rebuild_warmup_bundle_cache=rebuild_warmup_bundle_cache,
        background_artifacts=True,
        collect_states=False,
        feature_config=S01_TRAINING_FEATURE_CONFIG,
        run_id=run_id,
    )


__all__ = [
    "BASELINE_WARMUP_RETURN_MEAN",
    "EVAL_EPISODES",
    "EXPERIMENT_SEED",
    "TRAIN_EPISODES",
    "TRAIN_EPISODES_DEFAULT",
    "TRAIN_EPISODES_FAST",
    "WARMUP_EPISODES",
    "frozen_training_config",
]
