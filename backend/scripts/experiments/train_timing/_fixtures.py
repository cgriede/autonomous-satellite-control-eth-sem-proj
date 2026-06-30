"""Build S01 training setup for train-timing profiles."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import _cpu_budget  # noqa: F401

EXPERIMENT_ROOT = Path(__file__).resolve().parent
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT, OVERNIGHT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from autonomous_control.config.randomness import derive_seed  # noqa: E402
from s01_utils import training_workflow as tw  # noqa: E402
from utils.ml_training.ml_training_utils import remove_run_dirs_for_slug  # noqa: E402

_overnight_spec = importlib.util.spec_from_file_location(
    "ml_overnight_frozen_train_timing",
    OVERNIGHT_ROOT / "_frozen_baseline.py",
)
assert _overnight_spec and _overnight_spec.loader
_overnight_frozen = importlib.util.module_from_spec(_overnight_spec)
sys.modules[_overnight_spec.name] = _overnight_frozen
_overnight_spec.loader.exec_module(_overnight_frozen)

_sim_spec = importlib.util.spec_from_file_location(
    "ml_overnight_sim_train_timing",
    OVERNIGHT_ROOT / "_sim_constants_fork.py",
)
assert _sim_spec and _sim_spec.loader
_overnight_sim = importlib.util.module_from_spec(_sim_spec)
sys.modules[_sim_spec.name] = _overnight_sim
_sim_spec.loader.exec_module(_overnight_sim)

_reward_spec = importlib.util.spec_from_file_location(
    "ml_overnight_reward_train_timing",
    OVERNIGHT_ROOT / "_reward_fork.py",
)
assert _reward_spec and _reward_spec.loader
_overnight_reward = importlib.util.module_from_spec(_reward_spec)
sys.modules[_reward_spec.name] = _overnight_reward
_reward_spec.loader.exec_module(_overnight_reward)

_warmup_spec = importlib.util.spec_from_file_location(
    "ml_overnight_warmup_train_timing",
    OVERNIGHT_ROOT / "_warmup_fingerprint_patch.py",
)
assert _warmup_spec and _warmup_spec.loader
_overnight_warmup = importlib.util.module_from_spec(_warmup_spec)
sys.modules[_warmup_spec.name] = _overnight_warmup
_warmup_spec.loader.exec_module(_overnight_warmup)

EXPERIMENT_SEED = int(_overnight_frozen.EXPERIMENT_SEED)
DT_CANDIDATES = _overnight_sim.DT_CANDIDATES
apply_dt_profile = _overnight_sim.apply_dt_profile
get_applied_dt_profile = _overnight_sim.get_applied_dt_profile
activate_reward_fork = _overnight_reward.activate_reward_fork
activate_warmup_fingerprint_patch = _overnight_warmup.activate_warmup_fingerprint_patch
set_warmup_fingerprint_extra = _overnight_warmup.set_warmup_fingerprint_extra
frozen_training_config = _overnight_frozen.frozen_training_config


def dt_profile_by_label(label: str) -> Any:
    for profile in DT_CANDIDATES:
        if profile.label == label:
            return profile
    raise ValueError(f"Unknown dt profile label: {label!r}")


def build_profile_setup(
    *,
    run_slug: str,
    dt_label: str = "dt_1.5s",
    updates_per_step: int = 1,
    train_every_n_steps: int = 1,
    batch_size: int | None = None,
    rebuild_warmup_bundle_cache: bool = False,
) -> tw.TrainingWorkflowSetup:
    profile = dt_profile_by_label(dt_label)
    apply_dt_profile(profile)
    set_warmup_fingerprint_extra(
        sim_dt_s=profile.sim_dt_s,
        controller_interval_s=profile.controller_interval_s,
        reward_mode="sparse",
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("sparse")

    cfg = frozen_training_config(
        run_id=run_slug,
        train_episodes=0,
        rebuild_warmup_bundle_cache=rebuild_warmup_bundle_cache,
    )
    cfg = replace(
        cfg,
        warmup_episodes=1,
        eval_episodes=0,
        use_warmup_bundle_cache=not rebuild_warmup_bundle_cache,
        background_artifacts=False,
        updates_per_step=int(updates_per_step),
        train_every_n_steps=int(train_every_n_steps),
    )
    remove_run_dirs_for_slug(run_slug)
    setup = tw.build_training_workflow_setup(cfg)
    if batch_size is not None:
        setup = replace(
            setup,
            mpo_config=replace(setup.mpo_config, batch_size=int(batch_size)),
        )
        setup.agent.config = setup.mpo_config
    return setup


def warmup_seed(episode_idx: int = 0) -> Any:
    import numpy as np

    return np.random.default_rng(derive_seed(EXPERIMENT_SEED, "train_timing/warmup", episode_idx))


def train_seed(episode_idx: int = 0) -> Any:
    import numpy as np

    return np.random.default_rng(derive_seed(EXPERIMENT_SEED, "train_timing/train", episode_idx))
