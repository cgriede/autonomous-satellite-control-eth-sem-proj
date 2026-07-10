"""Exp 15 full trainer: new env seed every episode + paired baseline each ep."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from tqdm.auto import tqdm

from _env_setup_fork import (
    build_exp15_episode_setup,
    build_exp15_warmup_setup,
    episode_seeds,
)
from _episode_loop_fork import run_exp14_episode
from _eval_harness import run_paired_eval
from _exp14_checkpoints import save_agent_checkpoint
from _exp14_progress import make_progress_display, print_environment_banner
from _exp14_reward_fork import reward_mode_contract
from _exp14_runner_common import EXPERIMENT_ID, RESULTS_DIR, append_log, write_hypothesis_result
from _exp14_sim_constants import DT_15, apply_dt_profile, apply_experiment_dt_profile, write_dt_profile
from _paired_baseline import run_baseline_score_on_setup
from _profile_baseline import SCREEN_ARMS, ScreenArmSpec
from _run_guard import acquire_experiment_run_lock
from _training_setup import build_training_context
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra

DEFAULT_WARMUP_EP = 5
DEFAULT_TRAIN_EP = 50  # trimmed vs Exp 14 350: paired baseline ≈ 2× wall time


def _arm_hp_explore() -> ScreenArmSpec:
    for spec in SCREEN_ARMS:
        if spec.arm_id == "hp_explore":
            return spec
    return SCREEN_ARMS[0]


def run_full(
    *,
    train_episodes: int = DEFAULT_TRAIN_EP,
    warmup_episodes: int = DEFAULT_WARMUP_EP,
    pair_baseline_train: bool = True,
    show_progress: bool = False,
    arm_id: str = "hp_explore",
) -> dict[str, Any]:
    acquire_experiment_run_lock(script="episode_seed_full")
    arm = next((a for a in SCREEN_ARMS if a.arm_id == arm_id), _arm_hp_explore())
    append_log(
        f"START episode_seed_full arm={arm.arm_id} train_ep={train_episodes} "
        f"warmup_ep={warmup_episodes} pair_baseline_train={pair_baseline_train}"
    )
    write_dt_profile(train_episodes=int(train_episodes))
    dt_profile = apply_experiment_dt_profile()
    apply_dt_profile(DT_15)

    set_warmup_fingerprint_extra(
        sim_dt_s=dt_profile.get("sim_dt_s"),
        controller_interval_s=dt_profile.get("controller_interval_s"),
        reward_mode=arm.reward_mode,
        hparam_arm=arm.arm_id,
        attitude_request_mode="vector",
        experiment_id=EXPERIMENT_ID,
    )
    activate_warmup_fingerprint_patch()

    warmup_setup = build_exp15_warmup_setup()
    ctx = build_training_context(warmup_setup, arm=arm)
    progress_display = make_progress_display(ctx.agent, show_progress=show_progress)

    t0 = time.perf_counter()
    print_environment_banner(
        env_index=0,
        mission_seed=7,
        cloud_seed=7,
    )
    if show_progress:
        tqdm.write(f"=== WARMUP fixed seed (mission=7 cloud=7) × {warmup_episodes} ===")

    for wi in range(int(warmup_episodes)):
        run_exp14_episode(
            warmup_setup,
            ctx.agent,
            mode="warmup",
            feature_config=ctx.feature_config,
            observation_layout=ctx.observation_layout,
            reward_config=ctx.reward_config,
            episode_idx=wi,
            show_progress=show_progress and wi == 0,
            progress_display=progress_display,
            experiment_name=f"{EXPERIMENT_ID}:warmup",
        )

    train_rows: list[dict[str, Any]] = []
    train_returns: list[float] = []
    deltas: list[float] = []

    for ep_i in range(int(train_episodes)):
        seeds = episode_seeds(ep_i)
        setup = build_exp15_episode_setup(ep_i)
        print_environment_banner(
            env_index=ep_i,
            mission_seed=seeds["mission_seed"],
            cloud_seed=seeds["cloud_seed"],
        )
        if show_progress:
            tqdm.write(
                f"--- train ep {ep_i + 1}/{train_episodes} "
                f"mission={seeds['mission_seed']} cloud={seeds['cloud_seed']} ---"
            )

        baseline_score = None
        if pair_baseline_train:
            baseline_payload = run_baseline_score_on_setup(
                setup,
                show_progress=False,
            )
            baseline_score = float(baseline_payload["score_ep"])

        result = run_exp14_episode(
            setup,
            ctx.agent,
            mode="train",
            feature_config=ctx.feature_config,
            observation_layout=ctx.observation_layout,
            reward_config=ctx.reward_config,
            episode_idx=ep_i,
            show_progress=show_progress,
            progress_display=progress_display,
            experiment_name=f"{EXPERIMENT_ID}:train",
        )
        agent_score = float(result.mission_score)
        agent_return = float(result.episode_return)
        train_returns.append(agent_return)
        delta = None if baseline_score is None else agent_score - baseline_score
        if delta is not None:
            deltas.append(float(delta))
        row = {
            "episode_index": ep_i,
            "mission_seed": seeds["mission_seed"],
            "cloud_seed": seeds["cloud_seed"],
            "baseline_score": baseline_score,
            "agent_score": agent_score,
            "delta_score": delta,
            "agent_return": agent_return,
        }
        train_rows.append(row)
        append_log(
            f"train ep={ep_i} score={agent_score:.3f} "
            f"baseline={baseline_score} delta={delta} return={agent_return:.1f}"
        )

    eval_payload = run_paired_eval(ctx, show_progress=show_progress)
    ckpt = save_agent_checkpoint(
        ctx.agent,
        arm_id=arm.arm_id,
        tag="episode_seed_final",
        phase="full",
        metadata={
            "train_episodes": int(train_episodes),
            "pair_baseline_train": bool(pair_baseline_train),
            "eval_delta_score_mean": eval_payload.get("delta_score_mean"),
        },
    )

    wall_s = time.perf_counter() - t0
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "full",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "arm_id": arm.arm_id,
        "reward_mode": arm.reward_mode,
        "reward_mode_contract": reward_mode_contract(arm.reward_mode),
        "train_episodes": int(train_episodes),
        "warmup_episodes": int(warmup_episodes),
        "pair_baseline_train": bool(pair_baseline_train),
        "wall_s": wall_s,
        "train_returns": train_returns,
        "train_rows": train_rows,
        "train_delta_score_mean": float(sum(deltas) / len(deltas)) if deltas else None,
        "eval": eval_payload,
        "checkpoint_path": str(ckpt),
    }
    out = RESULTS_DIR / "full_summary.json"
    write_hypothesis_result(out, **summary)
    append_log(
        f"DONE full wall_s={wall_s:.1f} "
        f"eval_delta={eval_payload.get('delta_score_mean')} → {out}"
    )
    return summary


__all__ = ["DEFAULT_TRAIN_EP", "DEFAULT_WARMUP_EP", "run_full"]
