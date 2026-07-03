"""5-seed eval harness: baseline vs treatment mission score."""

from __future__ import annotations

import time
from typing import Any

from _env_setup_fork import build_exp14_eval_setup, eval_env_indices
from _episode_loop_fork import run_exp14_episode
from _mission_score import aggregate_eval_scores, compute_episode_mission_score
from _profile_baseline import FEATURE_CONFIG
from _exp14_runner_common import EXPERIMENT_ID, RESULTS_DIR, append_log, write_hypothesis_result
from _training_setup import Exp14TrainingContext, build_training_context

from s01_utils.baseline_overflight import run_baseline_overflight_rollout


def run_baseline_eval(*, show_progress: bool = False) -> dict[str, Any]:
    scores: list[float] = []
    per_seed: list[dict[str, Any]] = []
    for eval_index in eval_env_indices():
        setup = build_exp14_eval_setup(eval_index)
        rollout = run_baseline_overflight_rollout(
            setup,
            show_progress=show_progress and eval_index == 0,
            attitude_request_mode="torque",
        )
        score = compute_episode_mission_score(rollout.series, rollout.cmd_steps)
        scores.append(float(score))
        per_seed.append(
            {
                "eval_index": int(eval_index),
                "score_ep": float(score),
                "n_cmd_steps": len(rollout.cmd_steps),
            }
        )
    agg = aggregate_eval_scores(scores)
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "cohort": "baseline",
        **agg,
        "per_seed": per_seed,
    }
    out_path = RESULTS_DIR / "eval_baseline.json"
    write_hypothesis_result(out_path, **payload)
    append_log(f"baseline eval score_mean={agg['score_mean']:.4f}")
    return payload


def run_eval_on_setup(
    setup,
    ctx: Exp14TrainingContext,
    *,
    show_progress: bool = False,
    progress_display: Any | None = None,
    phase_bar_desc: str = "Eval",
    experiment_name: str | None = None,
) -> dict[str, Any]:
    from _exp14_progress import run_phase_episodes

    results = run_phase_episodes(
        setup,
        ctx,
        mode="eval",
        episode_count=1,
        progress_display=progress_display,
        show_progress=show_progress,
        phase_bar_desc=phase_bar_desc,
        experiment_name=experiment_name,
    )
    result = results[0]
    return {
        "score_ep": float(result.mission_score),
        "score_mean": float(result.mission_score),
        "eval_return": float(result.episode_return),
    }


def run_treatment_eval(
    ctx: Exp14TrainingContext,
    *,
    show_progress: bool = False,
) -> dict[str, Any]:
    scores: list[float] = []
    returns: list[float] = []
    per_seed: list[dict[str, Any]] = []
    for eval_index in eval_env_indices():
        setup = build_exp14_eval_setup(eval_index)
        result = run_exp14_episode(
            setup,
            ctx.agent,
            mode="eval",
            feature_config=ctx.feature_config,
            observation_layout=ctx.observation_layout,
            reward_config=ctx.reward_config,
            show_progress=show_progress and eval_index == 0,
        )
        scores.append(float(result.mission_score))
        returns.append(float(result.episode_return))
        per_seed.append(
            {
                "eval_index": int(eval_index),
                "score_ep": float(result.mission_score),
                "eval_return": float(result.episode_return),
            }
        )
    agg = aggregate_eval_scores(scores)
    return {
        "experiment_id": EXPERIMENT_ID,
        "cohort": "treatment",
        **agg,
        "eval_return_mean": float(sum(returns) / len(returns)) if returns else 0.0,
        "per_seed": per_seed,
    }


def run_eval_comparison(
    ctx: Exp14TrainingContext,
    *,
    show_progress: bool = False,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    baseline = run_baseline_eval(show_progress=show_progress)
    treatment = run_treatment_eval(ctx, show_progress=show_progress)
    delta = float(treatment["score_mean"]) - float(baseline["score_mean"])
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "eval_comparison",
        "wall_s": time.perf_counter() - t0,
        "score_mean_baseline": baseline["score_mean"],
        "score_mean_treatment": treatment["score_mean"],
        "delta_score_mean": delta,
        "baseline": baseline,
        "treatment": treatment,
    }
    out_path = RESULTS_DIR / "eval_comparison.json"
    write_hypothesis_result(out_path, **payload)
    append_log(f"eval comparison delta_score_mean={delta:.4f}")
    return payload


__all__ = [
    "run_baseline_eval",
    "run_eval_comparison",
    "run_eval_on_setup",
    "run_treatment_eval",
]
