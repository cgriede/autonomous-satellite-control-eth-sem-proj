"""Stage A hparam screen runner (5 arms × warmup + train + eval)."""

from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Any

from tqdm.auto import tqdm

from _env_setup_fork import build_exp14_env_setup_fixed
from _mission_score import aggregate_eval_scores
from _profile_baseline import (
    SCREEN_ARMS,
    SCREEN_EVAL_EP,
    SCREEN_TRAIN_EP,
    SCREEN_WARMUP_EP,
    ScreenArmSpec,
    screen_env_seeds,
)
from _exp14_progress import (
    make_progress_display,
    print_environment_banner,
    run_phase_episodes,
)
from _run_guard import acquire_experiment_run_lock
from _exp14_runner_common import (
    EXPERIMENT_ID,
    RESULTS_DIR,
    append_log,
    evaluate_learning_mode,
    write_hypothesis_result,
)
from _exp14_checkpoints import resolve_screen_checkpoint, save_agent_checkpoint
from _exp14_artifacts import export_screen_arm_artifacts
from _exp14_sim_constants import DT_15, apply_dt_profile, apply_experiment_dt_profile, get_applied_dt_profile, require_dt_profile, write_dt_profile
from _warmup_baseline_quality import assess_warmup_baseline_quality, require_warmup_baseline_quality
from _profile_baseline import profile
from _training_setup import build_training_context
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra
from _exp14_reward_fork import reward_mode_contract


def default_arms() -> tuple[ScreenArmSpec, ...]:
    return SCREEN_ARMS


def _target_entropy_from_indices(indices: list[int]) -> float:
    """Shannon entropy (bits) of the target index distribution observed during eval."""
    if not indices:
        return 0.0
    import numpy as np

    arr = np.asarray(indices, dtype=int)
    _, counts = np.unique(arr, return_counts=True)
    probs = counts / counts.sum()
    return float(-(probs * np.log2(probs + 1e-12)).sum())


def run_screen_arm(
    spec: ScreenArmSpec,
    *,
    show_progress: bool = False,
    trim_artifacts: bool = True,
    export_artifacts: bool = False,
    export_warmup_only: bool = False,
) -> dict[str, Any]:
    acquire_experiment_run_lock(script=f"screen:{spec.arm_id}")
    append_log(f"START screen arm={spec.arm_id}")
    write_dt_profile(train_episodes=SCREEN_TRAIN_EP)
    dt_profile = apply_experiment_dt_profile()
    apply_dt_profile(DT_15)
    require_dt_profile(DT_15, context=f"exp14_screen:{spec.arm_id}")

    set_warmup_fingerprint_extra(
        sim_dt_s=dt_profile.get("sim_dt_s"),
        controller_interval_s=dt_profile.get("controller_interval_s"),
        reward_mode=spec.reward_mode,
        hparam_arm=spec.arm_id,
        attitude_request_mode="vector",
        experiment_id=EXPERIMENT_ID,
    )
    activate_warmup_fingerprint_patch()

    setup = build_exp14_env_setup_fixed()
    ctx = build_training_context(setup, arm=spec)
    mission_seed, cloud_seed = screen_env_seeds()
    progress_display = make_progress_display(ctx.agent, show_progress=show_progress)
    print_environment_banner(
        env_index=None,
        mission_seed=mission_seed,
        cloud_seed=cloud_seed,
        label="ENV screen-fixed",
    )
    tqdm.write(
        f"--- screen arm={spec.arm_id} lr_pi={spec.learning_rate_pi} "
        f"batch={spec.batch_size} reward={spec.reward_mode} ---"
    )

    train_returns: list[float] = []
    eval_returns: list[float] = []
    eval_scores: list[float] = []
    eval_target_indices: list[int] = []
    t0 = time.perf_counter()

    warmup_results = run_phase_episodes(
        setup,
        ctx,
        mode="warmup",
        episode_count=SCREEN_WARMUP_EP,
        progress_display=progress_display,
        show_progress=show_progress,
        phase_bar_desc=f"Warmup [{spec.arm_id}]",
        experiment_name=f"{EXPERIMENT_ID}:{spec.arm_id}",
    )

    warmup_quality = assess_warmup_baseline_quality(warmup_results)
    if show_progress:
        tqdm.write(
            f"[warmup quality] passed={warmup_quality['passed']} "
            f"score_mean={warmup_quality['mission_score_mean']:.2f} "
            f"peak_eff={warmup_quality['mean_peak_efficiency_mean']:.2f} "
            f"captures={warmup_quality['capture_count_mean']:.0f}"
        )
    require_warmup_baseline_quality(
        warmup_results,
        context=f"screen:{spec.arm_id}",
    )

    workflow = profile().get("workflow") or {}
    should_export = export_artifacts or (not trim_artifacts)
    if should_export and warmup_results and (export_warmup_only or export_artifacts):
        export_screen_arm_artifacts(
            arm_id=spec.arm_id,
            warmup_results=warmup_results,
            train_results=None if export_warmup_only else [],
            eval_results=None if export_warmup_only else [],
            train_episode_videos=0 if export_warmup_only else int(workflow.get("train_episode_videos", 3)),
            eval_episode_videos=0 if export_warmup_only else int(workflow.get("eval_episode_videos", 2)),
            warmup_episode_videos=1,
            export_episode_reward_plots=bool(workflow.get("export_episode_reward_plots", True)),
            show_progress=show_progress,
        )
    if export_warmup_only:
        kpis = {
            "arm_id": spec.arm_id,
            "experiment_id": EXPERIMENT_ID,
            "phase": "warmup_preview",
            "warmup_returns": [float(r.episode_return) for r in warmup_results],
            "warmup_mission_scores": [float(r.mission_score) for r in warmup_results],
            "warmup_quality": warmup_quality,
        }
        append_log(f"DONE warmup preview arm={spec.arm_id}")
        return kpis

    train_results = run_phase_episodes(
        setup,
        ctx,
        mode="train",
        episode_count=SCREEN_TRAIN_EP,
        progress_display=progress_display,
        show_progress=show_progress,
        phase_bar_desc=f"Train [{spec.arm_id}]",
        experiment_name=f"{EXPERIMENT_ID}:{spec.arm_id}",
    )
    train_returns = [float(r.episode_return) for r in train_results]

    eval_results = run_phase_episodes(
        setup,
        ctx,
        mode="eval",
        episode_count=SCREEN_EVAL_EP,
        progress_display=progress_display,
        show_progress=show_progress,
        phase_bar_desc=f"Eval [{spec.arm_id}]",
        experiment_name=f"{EXPERIMENT_ID}:{spec.arm_id}",
    )
    for result in eval_results:
        eval_returns.append(float(result.episode_return))
        eval_scores.append(float(result.mission_score))
        eval_target_indices.extend(result.selected_target_indices)

    if should_export and not export_warmup_only:
        artifact_payload = export_screen_arm_artifacts(
            arm_id=spec.arm_id,
            warmup_results=warmup_results,
            train_results=train_results,
            eval_results=eval_results,
            train_episode_videos=int(workflow.get("train_episode_videos", 3)),
            eval_episode_videos=int(workflow.get("eval_episode_videos", 2)),
            warmup_episode_videos=0,
            export_episode_reward_plots=bool(workflow.get("export_episode_reward_plots", True)),
            show_progress=show_progress,
        )
    else:
        artifact_payload = None

    wall_s = time.perf_counter() - t0
    train_metrics = ctx.agent.train() if len(ctx.agent.buffer) >= ctx.mpo_config.batch_size else None
    learning_signal = evaluate_learning_mode(
        train_returns,
        eval_returns,
        learning_stats={"train_metrics_last": train_metrics},
        agent_kind="mpo",
    )
    score_agg = aggregate_eval_scores(eval_scores)
    policy_entropy = _target_entropy_from_indices(eval_target_indices)

    ckpt_path = save_agent_checkpoint(
        ctx.agent,
        arm_id=spec.arm_id,
        tag="screen_final",
        phase="screen",
        metadata={
            "reward_mode": spec.reward_mode,
            "warmup_episodes": SCREEN_WARMUP_EP,
            "train_episodes_completed": len(train_returns),
            "train_returns": train_returns,
            "eval_returns": eval_returns,
            "train_return_ep20": float(train_returns[-1]) if train_returns else 0.0,
            "eval_return_mean": float(sum(eval_returns) / len(eval_returns)) if eval_returns else 0.0,
            "mission_score_eval": score_agg,
            "learning_metrics_last": train_metrics,
            "learning_signal": learning_signal,
        },
    )

    ctx.agent.clear_buffer()

    kpis = {
        "arm_id": spec.arm_id,
        "experiment_id": EXPERIMENT_ID,
        "phase": "screen",
        "reward_mode_contract": reward_mode_contract(spec.reward_mode),
        "wall_s": wall_s,
        "dt_profile": get_applied_dt_profile(),
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "train_return_ep20": float(train_returns[-1]) if train_returns else 0.0,
        "eval_return_mean": float(sum(eval_returns) / len(eval_returns)) if eval_returns else 0.0,
        "mission_score_eval": score_agg,
        "learning_signal": learning_signal,
        "policy_target_entropy_bits": policy_entropy,
        "mpo_overrides": {
            "learning_rate_pi": spec.learning_rate_pi,
            "learning_rate_q": spec.learning_rate_q,
            "batch_size": spec.batch_size,
            "entropy_coef": spec.entropy_coef,
            "reward_mode": spec.reward_mode,
        },
        "trim_artifacts": trim_artifacts,
        "warmup_quality": warmup_quality,
        "artifacts": artifact_payload,
        "checkpoint_path": str(ckpt_path),
    }
    out_path = RESULTS_DIR / "arm_kpis" / f"{spec.arm_id}.json"
    write_hypothesis_result(out_path, **kpis)
    append_log(f"DONE screen arm={spec.arm_id} train_ep20={kpis['train_return_ep20']:.2f}")
    return kpis


def pick_screen_winner(results: dict[str, dict[str, Any]]) -> str:
    def _key(arm_id: str) -> tuple[float, float, float]:
        row = results[arm_id]
        train_ep20 = float(row.get("train_return_ep20", float("-inf")))
        eval_mean = float(row.get("eval_return_mean", float("-inf")))
        entropy = float(row.get("policy_target_entropy_bits", 0.0))
        return (train_ep20, eval_mean, entropy)

    return max(results.keys(), key=_key)


def run_screen(
    arms: tuple[ScreenArmSpec, ...] | None = None,
    *,
    show_progress: bool = False,
    trim_artifacts: bool = True,
    export_artifacts: bool = False,
    export_warmup_only: bool = False,
) -> dict[str, Any]:
    selected = arms or SCREEN_ARMS
    results: dict[str, dict[str, Any]] = {}
    n_arms = len(selected)
    for arm_i, spec in enumerate(selected):
        if show_progress:
            tqdm.write(f"=== Screen arm {arm_i + 1}/{n_arms}: {spec.arm_id} ===")
        results[spec.arm_id] = run_screen_arm(
            spec,
            show_progress=show_progress,
            trim_artifacts=trim_artifacts,
            export_artifacts=export_artifacts,
            export_warmup_only=export_warmup_only,
        )
    winner = pick_screen_winner(results)
    winner_ckpt = resolve_screen_checkpoint(winner)
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "screen",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "winner_arm_id": winner,
        "winner_checkpoint_path": str(winner_ckpt) if winner_ckpt.is_file() else None,
        "arms": list(results.keys()),
        "results": results,
    }
    summary_path = RESULTS_DIR / "screen_summary.json"
    write_hypothesis_result(summary_path, **summary)
    return summary


__all__ = ["default_arms", "pick_screen_winner", "run_screen", "run_screen_arm"]
