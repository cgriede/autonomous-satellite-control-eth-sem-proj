"""Stage B multi-env trainer (10 envs × warmup + train curriculum)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _env_setup_fork import build_exp14_env_setup, train_env_seeds
from _eval_harness import run_eval_on_setup
from _mission_score import aggregate_eval_scores
from _profile_baseline import (
    SCREEN_ARMS,
    SCREEN_TRAIN_EP,
    STAGE_B_ENV_COUNT,
    STAGE_B_TRAIN_PER_ENV,
    STAGE_B_WARMUP_PER_ENV,
    ScreenArmSpec,
)
from _run_guard import acquire_experiment_run_lock
from _exp14_runner_common import EXPERIMENT_ID, RESULTS_DIR, append_log, write_hypothesis_result
from _exp14_sim_constants import DT_15, apply_dt_profile, apply_experiment_dt_profile, write_dt_profile
from _exp14_checkpoints import load_agent_checkpoint, resolve_screen_checkpoint, save_agent_checkpoint
from _training_setup import build_training_context
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra
from _exp14_progress import make_progress_display, print_environment_banner, run_phase_episodes
from _exp14_reward_fork import reward_mode_contract
from tqdm.auto import tqdm


def _load_winner_arm(arm_id: str | None) -> ScreenArmSpec:
    if arm_id is not None:
        for spec in SCREEN_ARMS:
            if spec.arm_id == arm_id:
                return spec
        raise ValueError(f"Unknown arm_id {arm_id!r}")
    summary_path = RESULTS_DIR / "screen_summary.json"
    if summary_path.is_file():
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        winner = str(payload.get("winner_arm_id", "hp_default"))
        return _load_winner_arm(winner)
    return SCREEN_ARMS[0]


def _resolve_resume_checkpoint(arm: ScreenArmSpec) -> Path | None:
    summary_path = RESULTS_DIR / "screen_summary.json"
    if summary_path.is_file():
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        winner_path = payload.get("winner_checkpoint_path")
        if winner_path and Path(winner_path).is_file():
            return Path(winner_path)
    ckpt = resolve_screen_checkpoint(arm.arm_id)
    return ckpt if ckpt.is_file() else None


def run_stage_b(
    *,
    arm_id: str | None = None,
    show_progress: bool = False,
    resume_from_screen: bool = True,
) -> dict[str, Any]:
    acquire_experiment_run_lock(script="stage_b_full")
    arm = _load_winner_arm(arm_id)
    append_log(f"START stage_b arm={arm.arm_id} resume_from_screen={resume_from_screen}")
    total_train = STAGE_B_ENV_COUNT * STAGE_B_TRAIN_PER_ENV
    write_dt_profile(train_episodes=total_train)
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

    setup = build_exp14_env_setup(0)
    ctx = build_training_context(setup, arm=arm)
    resume_meta: dict[str, Any] | None = None
    screen_train_completed = 0
    if resume_from_screen:
        ckpt_path = _resolve_resume_checkpoint(arm)
        if ckpt_path is None:
            raise FileNotFoundError(
                f"No screen checkpoint for arm={arm.arm_id!r}. "
                f"Run `python run.py --screen` first, or pass --from-scratch."
            )
        resume_meta = load_agent_checkpoint(ctx.agent, ckpt_path)
        screen_train_completed = int(resume_meta.get("train_episodes_completed", SCREEN_TRAIN_EP))
        append_log(
            f"RESUME stage_b from {ckpt_path} "
            f"(screen_train_episodes={screen_train_completed})"
        )
        if show_progress:
            tqdm.write(
                f"Resumed winner weights from screen ({screen_train_completed} train ep already done)"
            )

    progress_display = make_progress_display(ctx.agent, show_progress=show_progress)
    train_returns: list[float] = []
    if resume_meta and resume_meta.get("train_returns"):
        train_returns.extend(float(x) for x in resume_meta["train_returns"])
    eval_score_history: list[dict[str, Any]] = []
    best_score_mean = float("-inf")
    best_checkpoint: dict[str, Any] | None = None
    t0 = time.perf_counter()

    for env_i in range(STAGE_B_ENV_COUNT):
        setup = build_exp14_env_setup(env_i)
        seeds = train_env_seeds(env_i)
        print_environment_banner(
            env_index=env_i,
            mission_seed=seeds["mission_seed"],
            cloud_seed=seeds["cloud_seed"],
        )
        tqdm.write(f"--- stage_b env {env_i + 1}/{STAGE_B_ENV_COUNT} arm={arm.arm_id} ---")
        ctx.agent.clear_buffer()
        run_phase_episodes(
            setup,
            ctx,
            mode="warmup",
            episode_count=STAGE_B_WARMUP_PER_ENV,
            progress_display=progress_display,
            show_progress=show_progress,
            phase_bar_desc=f"Warmup env{env_i + 1}",
            experiment_name=f"{EXPERIMENT_ID}:stage_b:env{env_i}",
        )
        train_results = run_phase_episodes(
            setup,
            ctx,
            mode="train",
            episode_count=STAGE_B_TRAIN_PER_ENV,
            progress_display=progress_display,
            show_progress=show_progress,
            phase_bar_desc=f"Train env{env_i + 1}",
            experiment_name=f"{EXPERIMENT_ID}:stage_b:env{env_i}",
        )
        for result in train_results:
            train_returns.append(float(result.episode_return))

        eval_payload = run_eval_on_setup(
            setup,
            ctx,
            show_progress=show_progress,
            progress_display=progress_display,
            phase_bar_desc=f"Eval env{env_i + 1}",
            experiment_name=f"{EXPERIMENT_ID}:stage_b:env{env_i}:eval",
        )
        score_mean = float(eval_payload["score_mean"])
        eval_score_history.append({"env_index": env_i, **eval_payload})
        if score_mean > best_score_mean:
            best_score_mean = score_mean
            best_checkpoint = {
                "env_index": env_i,
                "score_mean": score_mean,
                "score_ep": eval_payload.get("score_ep", []),
            }

        save_agent_checkpoint(
            ctx.agent,
            arm_id=arm.arm_id,
            tag=f"stage_b_env{env_i}",
            phase="stage_b",
            metadata={
                "reward_mode": arm.reward_mode,
                "env_index": env_i,
                "screen_train_episodes_completed": screen_train_completed,
                "stage_b_train_episodes_completed": len(train_returns) - screen_train_completed,
                "total_train_episodes_completed": len(train_returns),
                "eval_score_mean": score_mean,
            },
        )

    stage_b_final_path = save_agent_checkpoint(
        ctx.agent,
        arm_id=arm.arm_id,
        tag="stage_b_final",
        phase="stage_b",
        metadata={
            "reward_mode": arm.reward_mode,
            "screen_train_episodes_completed": screen_train_completed,
            "stage_b_train_episodes_completed": len(train_returns) - screen_train_completed,
            "total_train_episodes_completed": len(train_returns),
            "best_eval_score_mean": best_score_mean,
            "best_checkpoint": best_checkpoint,
        },
    )

    wall_s = time.perf_counter() - t0
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "stage_b",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "arm_id": arm.arm_id,
        "reward_mode": arm.reward_mode,
        "reward_mode_contract": reward_mode_contract(arm.reward_mode),
        "resumed_from_screen": bool(resume_from_screen and resume_meta),
        "resume_checkpoint": str(_resolve_resume_checkpoint(arm)) if resume_meta else None,
        "screen_train_episodes_completed": screen_train_completed,
        "stage_b_train_episodes_completed": len(train_returns) - screen_train_completed,
        "total_train_episodes_completed": len(train_returns),
        "wall_s": wall_s,
        "train_episodes_total": STAGE_B_ENV_COUNT * (STAGE_B_WARMUP_PER_ENV + STAGE_B_TRAIN_PER_ENV),
        "train_returns": train_returns,
        "eval_score_history": eval_score_history,
        "best_eval_score_mean": best_score_mean,
        "best_checkpoint": best_checkpoint,
        "score_aggregate": aggregate_eval_scores(
            [float(row["score_mean"]) for row in eval_score_history]
        ),
        "checkpoint_path": str(stage_b_final_path),
    }
    out_path = RESULTS_DIR / "stage_b_summary.json"
    write_hypothesis_result(out_path, **summary)
    append_log(
        f"DONE stage_b best_score_mean={best_score_mean:.4f} "
        f"total_train_ep={len(train_returns)}"
    )
    return summary


__all__ = ["run_stage_b"]
