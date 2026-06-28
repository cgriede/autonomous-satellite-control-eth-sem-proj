"""Shared training slice runner + fixed-contract JSON for ML learning-signal experiments."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import _cpu_budget  # noqa: F401  # before numpy/torch — caps per-process CPU threads

import numpy as np

from _run_guard import acquire_experiment_run_lock  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[3]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
EXPERIMENT_ROOT = Path(__file__).resolve().parent
for path in (BACKEND_DIR, S01_DIR, str(EXPERIMENT_ROOT)):
    p = Path(path)
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from autonomous_control.controller_agent import MPOAgent  # noqa: E402
from autonomous_control.mpo_config import MPOConfig  # noqa: E402
from autonomous_control.training_runtime import EpisodeResult  # noqa: E402
from s01_utils import training_workflow as tw  # noqa: E402

from _frozen_baseline import (  # noqa: E402
    BASELINE_WARMUP_RETURN_MEAN,
    TRAIN_EPISODES,
    frozen_training_config,
)

RESULTS_DIR = EXPERIMENT_ROOT / "results"


def write_hypothesis_result(path: Path, **payload: Any) -> None:
    out = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, default=_json_default), encoding="utf-8")


def _json_default(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Not JSON serializable: {type(obj)!r}")


def evaluate_increasing_signal(train_returns: list[float]) -> dict[str, Any]:
    """Success bar: ep1-3 all non-zero; ep2 or ep3 strictly above ep1."""
    eps = [float(r) for r in train_returns[:TRAIN_EPISODES]]
    while len(eps) < TRAIN_EPISODES:
        eps.append(0.0)
    all_nonzero = all(r > 0.0 for r in eps)
    monotonic_hint = eps[2] > eps[0] or eps[1] > eps[0]
    strictly_increasing = eps[0] < eps[1] < eps[2]
    return {
        "train_returns_ep1_ep3": eps,
        "all_nonzero": all_nonzero,
        "ep2_or_ep3_above_ep1": monotonic_hint,
        "strictly_increasing_ep1_ep3": strictly_increasing,
        "strong_lead": all_nonzero and monotonic_hint,
    }


def _episode_debug_row(result: EpisodeResult, *, episode_idx: int) -> dict[str, Any]:
    series = result.simulation_series
    meta = series.metadata
    shutter_steps = list(getattr(meta, "take_picture_cmd_steps", ()) or ())
    rewards = np.asarray(series.simulation_reward[1 : result.steps + 1], dtype=float)
    positive_reward_steps = int(np.sum(rewards > 0.0))
    return {
        "episode_idx": episode_idx,
        "episode_return": float(result.episode_return),
        "steps": int(result.steps),
        "n_shutter_cmds": len(shutter_steps),
        "positive_reward_steps": positive_reward_steps,
        "max_step_reward": float(np.max(rewards)) if rewards.size else 0.0,
        "learning_stats": result.learning_stats,
    }


def _rebuild_agent(setup: tw.TrainingWorkflowSetup, mpo_config: MPOConfig) -> tw.TrainingWorkflowSetup:
    n_targets = len(setup.mission_setup.resolve(require_camera=True).target_areas or ())
    env = tw.make_attitude_control_env(
        secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
        reward_config=mpo_config.reward,
        feature_config=setup.feature_config,
        n_mission_targets=n_targets,
        observation_layout=setup.observation_layout,
    )
    agent = MPOAgent(env, config=mpo_config)
    return replace(setup, agent=agent, mpo_config=mpo_config)


def run_training_slice(
    *,
    run_id: str,
    mpo_overrides: dict[str, Any] | None = None,
    workflow_overrides: dict[str, Any] | None = None,
    agent_setup_hook: Any | None = None,
    show_progress: bool = False,
) -> dict[str, Any]:
    """Warmup from cache + train episodes; returns KPI dict."""
    acquire_experiment_run_lock(script=f"run_training_slice:{run_id}")
    cfg_kwargs = workflow_overrides or {}
    cfg = frozen_training_config(run_id=run_id)
    if cfg_kwargs:
        cfg = replace(cfg, **cfg_kwargs)
    # Avoid colliding with prior partial runs under models/.
    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = replace(cfg, run_id=f"{run_id}_{stamp}")

    setup = tw.build_training_workflow_setup(cfg)
    if mpo_overrides:
        setup = _rebuild_agent(setup, replace(setup.mpo_config, **mpo_overrides))
    if agent_setup_hook is not None:
        agent_setup_hook(setup)

    result = tw.run_training_workflow(setup, show_progress=show_progress)
    train_returns = [float(ep.episode_return) for ep in result.train_results]
    warmup_returns = [float(ep.episode_return) for ep in result.warmup_results]
    signal = evaluate_increasing_signal(train_returns)
    debug_eps = [
        _episode_debug_row(ep, episode_idx=i) for i, ep in enumerate(result.train_results)
    ]
    return {
        "run_id": run_id,
        "run_dir": str(setup.run_dir),
        "warmup_from_cache": cfg.use_warmup_bundle_cache,
        "warmup_returns": warmup_returns,
        "warmup_return_mean": float(np.mean(warmup_returns)) if warmup_returns else 0.0,
        "train_returns": train_returns,
        "train_return_mean": float(np.mean(train_returns)) if train_returns else 0.0,
        "train_return_best": float(max(train_returns)) if train_returns else 0.0,
        "baseline_warmup_reference_mean": BASELINE_WARMUP_RETURN_MEAN,
        "increasing_signal": signal,
        "debug_episodes": debug_eps,
        "last_train_learning": result.train_kpis,
    }


def run_baseline_deterministic_warmup_only(*, run_id: str = "baseline_warmup_ref") -> dict[str, Any]:
    """Reference: cached baseline overflight warmup (no train)."""
    cfg = replace(
        frozen_training_config(run_id=run_id),
        train_episodes=0,
        eval_episodes=0,
    )
    setup = tw.build_training_workflow_setup(cfg)
    result = tw.run_training_workflow(setup, show_progress=False)
    returns = [float(ep.episode_return) for ep in result.warmup_results]
    return {
        "run_id": run_id,
        "warmup_returns": returns,
        "warmup_return_mean": float(np.mean(returns)) if returns else 0.0,
    }


def write_analysis_card(path: Path, *, hypothesis_id: str, json_path: Path, sections: dict[str, str]) -> None:
    template = [
        f"# Analysis — {hypothesis_id}",
        "",
        f"Source JSON: `{json_path.name}`",
        "",
    ]
    for title, body in sections.items():
        template.extend([f"## {title}", "", body.strip(), ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(template), encoding="utf-8")


__all__ = [
    "evaluate_increasing_signal",
    "run_baseline_deterministic_warmup_only",
    "run_training_slice",
    "write_analysis_card",
    "write_hypothesis_result",
    "apply_cpu_thread_budget",
]

from _cpu_budget import apply_cpu_thread_budget  # noqa: E402
