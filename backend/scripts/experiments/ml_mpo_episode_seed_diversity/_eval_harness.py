"""Paired eval: baseline + treatment on identical held-out episode seeds."""

from __future__ import annotations

import time
from typing import Any

from _env_setup_fork import build_exp15_eval_setup, eval_env_indices, eval_episode_seeds
from _episode_loop_fork import run_exp14_episode
from _mission_score import aggregate_eval_scores
from _exp14_runner_common import EXPERIMENT_ID, RESULTS_DIR, append_log, write_hypothesis_result
from _paired_baseline import run_baseline_score_on_setup
from _training_setup import Exp14TrainingContext


def run_paired_eval(
    ctx: Exp14TrainingContext,
    *,
    show_progress: bool = False,
) -> dict[str, Any]:
    """Always run baseline then treatment on the same setup per eval seed."""
    per_seed: list[dict[str, Any]] = []
    baseline_scores: list[float] = []
    treatment_scores: list[float] = []
    deltas: list[float] = []
    returns: list[float] = []

    for eval_index in eval_env_indices():
        seeds = eval_episode_seeds(eval_index)
        setup = build_exp15_eval_setup(eval_index)
        baseline = run_baseline_score_on_setup(
            setup,
            show_progress=show_progress and eval_index == 0,
        )
        result = run_exp14_episode(
            setup,
            ctx.agent,
            mode="eval",
            feature_config=ctx.feature_config,
            observation_layout=ctx.observation_layout,
            reward_config=ctx.reward_config,
            show_progress=show_progress and eval_index == 0,
        )
        b = float(baseline["score_ep"])
        t = float(result.mission_score)
        d = t - b
        baseline_scores.append(b)
        treatment_scores.append(t)
        deltas.append(d)
        returns.append(float(result.episode_return))
        per_seed.append(
            {
                "eval_index": int(eval_index),
                "mission_seed": seeds["mission_seed"],
                "cloud_seed": seeds["cloud_seed"],
                "baseline_score": b,
                "treatment_score": t,
                "delta_score": d,
                "eval_return": float(result.episode_return),
            }
        )
        append_log(
            f"eval seed={eval_index} baseline={b:.4f} treatment={t:.4f} delta={d:.4f}"
        )

    b_agg = aggregate_eval_scores(baseline_scores)
    t_agg = aggregate_eval_scores(treatment_scores)
    delta_mean = float(sum(deltas) / len(deltas)) if deltas else 0.0
    return {
        "experiment_id": EXPERIMENT_ID,
        "cohort": "paired",
        "score_mean_baseline": b_agg["score_mean"],
        "score_mean_treatment": t_agg["score_mean"],
        "delta_score_mean": delta_mean,
        "score_std_baseline": b_agg.get("score_std"),
        "score_std_treatment": t_agg.get("score_std"),
        "eval_return_mean": float(sum(returns) / len(returns)) if returns else 0.0,
        "per_seed": per_seed,
        "baseline": {"cohort": "baseline", **b_agg, "per_seed": [
            {"eval_index": r["eval_index"], "score_ep": r["baseline_score"]} for r in per_seed
        ]},
        "treatment": {"cohort": "treatment", **t_agg, "per_seed": [
            {"eval_index": r["eval_index"], "score_ep": r["treatment_score"], "eval_return": r["eval_return"]}
            for r in per_seed
        ]},
    }


def run_eval_comparison(
    ctx: Exp14TrainingContext,
    *,
    show_progress: bool = False,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    paired = run_paired_eval(ctx, show_progress=show_progress)
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "eval_comparison",
        "wall_s": time.perf_counter() - t0,
        **paired,
    }
    out_path = RESULTS_DIR / "eval_comparison.json"
    write_hypothesis_result(out_path, **payload)
    append_log(f"eval comparison delta_score_mean={payload['delta_score_mean']:.4f}")
    return payload


# Legacy names used by copied modules
def run_baseline_eval(*, show_progress: bool = False) -> dict[str, Any]:
    from _training_setup import build_training_context
    from _env_setup_fork import build_exp15_warmup_setup

    ctx = build_training_context(build_exp15_warmup_setup())
    paired = run_paired_eval(ctx, show_progress=show_progress)
    payload = {"experiment_id": EXPERIMENT_ID, **paired["baseline"]}
    write_hypothesis_result(RESULTS_DIR / "eval_baseline.json", **payload)
    return payload


def run_treatment_eval(ctx: Exp14TrainingContext, *, show_progress: bool = False) -> dict[str, Any]:
    paired = run_paired_eval(ctx, show_progress=show_progress)
    return {"experiment_id": EXPERIMENT_ID, **paired["treatment"]}


def run_eval_on_setup(setup, ctx, **kwargs) -> dict[str, Any]:
    result = run_exp14_episode(
        setup,
        ctx.agent,
        mode="eval",
        feature_config=ctx.feature_config,
        observation_layout=ctx.observation_layout,
        reward_config=ctx.reward_config,
        show_progress=kwargs.get("show_progress", False),
    )
    return {
        "score_ep": float(result.mission_score),
        "score_mean": float(result.mission_score),
        "eval_return": float(result.episode_return),
    }


__all__ = [
    "run_baseline_eval",
    "run_eval_comparison",
    "run_eval_on_setup",
    "run_paired_eval",
    "run_treatment_eval",
]
