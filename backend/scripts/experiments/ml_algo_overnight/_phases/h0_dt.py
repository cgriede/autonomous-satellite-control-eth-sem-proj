"""H0: dt / controller profile sweep → results/dt_profile.json."""

from __future__ import annotations

import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import _cpu_budget  # noqa: F401

import numpy as np

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from autonomous_control.config.randomness import derive_seed
from s01_utils import training_workflow as tw
from utils.ml_training.ml_training_utils import remove_run_dirs_for_slug

import _frozen_baseline as fb
from _frozen_baseline import EXPERIMENT_SEED, TRAIN_EPISODES_DEFAULT, TRAIN_EPISODES_FAST, frozen_training_config
from _reward_fork import activate_reward_fork
from _runner_common import DT_PROFILE_PATH, RESULTS_DIR, append_overnight_log, write_hypothesis_result
from _sim_constants_fork import DT_CANDIDATES, DtProfile, apply_dt_profile
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra


def _warmup_metrics(result: Any) -> dict[str, float | int]:
    series = result.simulation_series
    meta = series.metadata
    shutter_steps = list(getattr(meta, "take_picture_cmd_steps", ()) or ())
    return {
        "episode_return": float(result.episode_return),
        "steps": int(result.steps),
        "n_shutter_cmds": len(shutter_steps),
    }


def _run_warmup_episode(setup: tw.TrainingWorkflowSetup) -> Any:
    return setup.runner.run_serial(
        setup.agent,
        mode="warmup",
        episode_idx=0,
        collect_states=False,
        show_training_context=False,
        train_updates_per_step=0,
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "h0/warmup", 0)),
    )


def _run_train_speed_episode(setup: tw.TrainingWorkflowSetup, warmup: Any) -> dict[str, float | int]:
    buffer_size = len(setup.agent.buffer) if hasattr(setup.agent, "buffer") else 0
    if buffer_size == 0:
        raise RuntimeError(
            "Warmup produced an empty replay buffer; cannot benchmark train episode."
        )
    t0 = time.perf_counter()
    result = setup.runner.run_serial(
        setup.agent,
        mode="train",
        episode_idx=0,
        collect_states=False,
        show_training_context=False,
        train_updates_per_step=1,
        train_every_n_steps=1,
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "h0/train", 0)),
    )
    wall_s = time.perf_counter() - t0
    stats = result.learning_stats or {}
    if hasattr(stats, "n_train_updates"):
        n_updates = int(stats.n_train_updates)
    elif isinstance(stats, dict):
        n_updates = int(stats.get("n_train_updates", 0))
    else:
        n_updates = 0
    steps = int(result.steps)
    return {
        "wall_s": wall_s,
        "steps": steps,
        "n_train_updates": n_updates,
        "steps_per_s": steps / wall_s if wall_s > 0 else 0.0,
        "episode_return": float(result.episode_return),
    }


def _build_h0_setup(profile: DtProfile) -> tw.TrainingWorkflowSetup:
    apply_dt_profile(profile)
    set_warmup_fingerprint_extra(
        sim_dt_s=profile.sim_dt_s,
        controller_interval_s=profile.controller_interval_s,
        reward_mode="sparse",
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("sparse")
    cfg = frozen_training_config(
        run_id=f"ml_overnight_h0_{profile.label}",
        train_episodes=0,
        rebuild_warmup_bundle_cache=True,
    )
    cfg = replace(cfg, warmup_episodes=1, use_warmup_bundle_cache=False, eval_episodes=0, background_artifacts=False)
    remove_run_dirs_for_slug(f"ml_overnight_h0_{profile.label}")
    return tw.build_training_workflow_setup(cfg)


def _parity_passes(candidate: dict[str, Any], reference: dict[str, Any]) -> bool:
    if int(candidate["n_shutter_cmds"]) <= 0:
        return False
    ref_ret = float(reference["episode_return"])
    cand_ret = float(candidate["episode_return"])
    if ref_ret > 0:
        return cand_ret >= 0.5 * ref_ret
    return cand_ret > 0


def phase_h0_dt() -> dict[str, Any]:
    """Sweep dt candidates; write dt_profile.json with chosen profile + train episode count."""
    append_overnight_log("START H0 dt sweep")
    ref_profile = DT_CANDIDATES[0]
    ref_setup = _build_h0_setup(ref_profile)
    ref_warmup = _run_warmup_episode(ref_setup)
    reference = _warmup_metrics(ref_warmup)
    ref_speed = _run_train_speed_episode(ref_setup, ref_warmup)
    ref_wall_s = float(ref_speed["wall_s"])

    candidates: list[dict[str, Any]] = []
    for profile in DT_CANDIDATES:
        setup = _build_h0_setup(profile)
        warmup = _run_warmup_episode(setup)
        parity = _warmup_metrics(warmup)
        speed = _run_train_speed_episode(setup, warmup)
        passed = _parity_passes(parity, reference)
        candidates.append(
            {
                "label": profile.label,
                "sim_dt_s": profile.sim_dt_s,
                "controller_interval_s": profile.controller_interval_s,
                "effective_controller_interval_s": profile.effective_controller_interval_s,
                "parity": parity,
                "speed": speed,
                "parity_passed": passed,
                "speed_ratio_vs_ref": ref_wall_s / float(speed["wall_s"]) if speed["wall_s"] > 0 else 0.0,
            }
        )

    passing = [c for c in candidates if c["parity_passed"]]
    if not passing:
        payload = {
            "aborted": True,
            "reason": "no dt candidate passed parity gate",
            "reference": {"profile": ref_profile.label, **reference, "speed": ref_speed},
            "candidates": candidates,
            "train_episodes": None,
        }
        write_hypothesis_result(DT_PROFILE_PATH, phase="H0", hypothesis_id="dt_profile", **payload)
        append_overnight_log("H0 ABORT: no parity-passing dt")
        fb.TRAIN_EPISODES = TRAIN_EPISODES_DEFAULT
        return payload

    chosen = max(passing, key=lambda c: (c["sim_dt_s"], -c["speed"]["wall_s"]))
    speed_ratio = float(chosen["speed_ratio_vs_ref"])
    train_eps = TRAIN_EPISODES_FAST if speed_ratio >= 2.0 else TRAIN_EPISODES_DEFAULT
    fb.TRAIN_EPISODES = train_eps

    apply_dt_profile(
        DtProfile(
            sim_dt_s=float(chosen["sim_dt_s"]),
            controller_interval_s=float(chosen["controller_interval_s"]),
            effective_controller_interval_s=float(chosen["effective_controller_interval_s"]),
            label=str(chosen["label"]),
        )
    )
    set_warmup_fingerprint_extra(
        sim_dt_s=chosen["sim_dt_s"],
        controller_interval_s=chosen["controller_interval_s"],
        reward_mode="sparse",
    )
    activate_warmup_fingerprint_patch()

    payload = {
        "aborted": False,
        "sim_dt_s": chosen["sim_dt_s"],
        "controller_interval_s": chosen["controller_interval_s"],
        "effective_controller_interval_s": chosen["effective_controller_interval_s"],
        "label": chosen["label"],
        "train_episodes": train_eps,
        "speed_ratio_vs_ref": speed_ratio,
        "reference": {"profile": ref_profile.label, **reference, "speed": ref_speed},
        "candidates": candidates,
        "chosen": chosen,
    }
    write_hypothesis_result(DT_PROFILE_PATH, phase="H0", hypothesis_id="dt_profile", **payload)
    append_overnight_log(
        f"H0 DONE label={chosen['label']} train_episodes={train_eps} speed_ratio={speed_ratio:.2f}"
    )
    return payload
