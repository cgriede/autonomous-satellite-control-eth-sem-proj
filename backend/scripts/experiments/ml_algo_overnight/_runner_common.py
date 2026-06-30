"""Shared training runner, KPIs, videos, and fixed-contract JSON for ml_algo_overnight."""

from __future__ import annotations

import json
import sys
import time
import traceback
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

import _cpu_budget  # noqa: F401

import numpy as np

from _run_guard import acquire_experiment_run_lock

BACKEND_DIR = Path(__file__).resolve().parents[3]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
EXPERIMENT_ROOT = Path(__file__).resolve().parent
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    p = Path(path)
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from autonomous_control.config.randomness import derive_seed  # noqa: E402
from autonomous_control.controller_agent import MPOAgent  # noqa: E402
from autonomous_control.mpo_config import MPOConfig  # noqa: E402
from autonomous_control.training_runtime import EpisodeResult  # noqa: E402
from s01_utils import training_workflow as tw  # noqa: E402
from utils.ml_training.training_run_artifacts import (  # noqa: E402
    ensure_run_layout,
    export_training_episode_video_sync,
)

from _frozen_baseline import (  # noqa: E402
    BASELINE_WARMUP_RETURN_MEAN,
    EXPERIMENT_SEED,
    TRAIN_EPISODES,
    frozen_training_config,
)
from _reward_fork import RewardForkMode, activate_reward_fork, reward_fork_mode  # noqa: E402
from _sim_constants_fork import apply_dt_profile_from_dict, get_applied_dt_profile  # noqa: E402
from _warmup_fingerprint_patch import (  # noqa: E402
    activate_warmup_fingerprint_patch,
    set_warmup_fingerprint_extra,
)

RESULTS_DIR = EXPERIMENT_ROOT / "results"
DT_PROFILE_PATH = RESULTS_DIR / "dt_profile.json"
OVERNIGHT_LOG_PATH = RESULTS_DIR / "overnight.log"


def append_overnight_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with OVERNIGHT_LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


def write_hypothesis_result(path: Path, **payload: Any) -> None:
    out = {"run_at_utc": datetime.now(timezone.utc).isoformat(), **payload}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, default=_json_default), encoding="utf-8")


def _json_default(obj: Any) -> Any:
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Not JSON serializable: {type(obj)!r}")


def load_dt_profile() -> dict[str, Any]:
    if not DT_PROFILE_PATH.is_file():
        raise FileNotFoundError(f"Missing dt profile: {DT_PROFILE_PATH}")
    return json.loads(DT_PROFILE_PATH.read_text(encoding="utf-8"))


def apply_runtime_context_from_dt_profile() -> dict[str, Any]:
    profile = load_dt_profile()
    if profile.get("aborted"):
        raise RuntimeError("dt_profile.json marked aborted; cannot run hypothesis phases.")
    apply_dt_profile_from_dict(profile)
    dt = get_applied_dt_profile() or {}
    set_warmup_fingerprint_extra(
        sim_dt_s=dt.get("sim_dt_s"),
        controller_interval_s=dt.get("controller_interval_s"),
        reward_mode=reward_fork_mode(),
    )
    activate_warmup_fingerprint_patch()
    return profile


def evaluate_learning_mode(
    train_returns: list[float],
    eval_returns: list[float],
    *,
    learning_stats: dict[str, Any] | None = None,
    agent_kind: Literal["mpo", "sac"] = "mpo",
) -> dict[str, Any]:
    eps = [float(r) for r in train_returns]
    eval_f = [float(r) for r in eval_returns]
    n = len(eps)
    any_nonzero = any(r != 0.0 for r in eps) if eps else False
    improving = n >= 2 and (eps[-1] > eps[0] or (max(eps[1:]) > eps[0] if len(eps) > 1 else False))
    stats = learning_stats or {}
    kl_mean_last = float(stats.get("kl_mean_last", float("nan")))
    if agent_kind == "sac":
        kl_finite = True
    else:
        kl_finite = np.isfinite(kl_mean_last) and kl_mean_last < 1e4
    learning_mode = bool(any_nonzero and improving and kl_finite)
    strong_lead = bool(
        eps
        and all(r > 0 for r in eps)
        and improving
        and (float(np.mean(eval_f)) > 0.0 if eval_f else False)
    )
    beats_baseline = bool(
        eval_f and float(np.mean(eval_f)) > BASELINE_WARMUP_RETURN_MEAN
    )
    return {
        "learning_mode": learning_mode,
        "strong_lead": strong_lead,
        "beats_baseline": beats_baseline,
        "train_returns": eps,
        "eval_return_mean": float(np.mean(eval_f)) if eval_f else None,
        "kl_mean_last": kl_mean_last if agent_kind == "mpo" else None,
    }


def _episode_debug_row(result: EpisodeResult, *, episode_idx: int) -> dict[str, Any]:
    series = result.simulation_series
    meta = series.metadata
    shutter_steps = list(getattr(meta, "take_picture_cmd_steps", ()) or ())
    rewards = np.asarray(series.simulation_reward[1 : result.steps + 1], dtype=float)
    return {
        "episode_idx": episode_idx,
        "episode_return": float(result.episode_return),
        "steps": int(result.steps),
        "n_shutter_cmds": len(shutter_steps),
        "positive_reward_steps": int(np.sum(rewards > 0.0)),
        "max_step_reward": float(np.max(rewards)) if rewards.size else 0.0,
        "learning_stats": result.learning_stats,
    }


def _learning_stats_summary(agent: Any, train_results: list[EpisodeResult]) -> dict[str, Any]:
    from dataclasses import asdict, is_dataclass

    def _stat_val(stats: Any, key: str) -> float | None:
        if stats is None:
            return None
        if isinstance(stats, dict):
            val = stats.get(key)
        elif is_dataclass(stats):
            val = asdict(stats).get(key)
        else:
            val = getattr(stats, key, None)
        if val is None or not np.isfinite(float(val)):
            return None
        return float(val)

    kl_vals: list[float] = []
    eta_vals: list[float] = []
    for ep in train_results:
        stats = ep.learning_stats
        kl = _stat_val(stats, "kl_mean")
        if kl is not None:
            kl_vals.append(kl)
        eta = _stat_val(stats, "eta_mean")
        if eta is not None:
            eta_vals.append(eta)
    if hasattr(agent, "metrics"):
        kl_vals.extend(float(x) for x in agent.metrics.get("kl", [])[-50:])
        eta_vals.extend(float(x) for x in agent.metrics.get("eta", [])[-50:])
    return {
        "kl_mean_last": float(kl_vals[-1]) if kl_vals else float("nan"),
        "kl_mean_over_train": float(np.mean(kl_vals)) if kl_vals else float("nan"),
        "eta_mean_last": float(eta_vals[-1]) if eta_vals else float("nan"),
        "n_train_updates_last_ep": int(_stat_val(train_results[-1].learning_stats, "n_train_updates") or 0)
        if train_results
        else 0,
    }


def _rebuild_mpo_agent(setup: tw.TrainingWorkflowSetup, mpo_config: MPOConfig) -> tw.TrainingWorkflowSetup:
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


def _replace_agent(setup: tw.TrainingWorkflowSetup, agent: Any) -> tw.TrainingWorkflowSetup:
    return replace(setup, agent=agent)


def export_phase_videos(
    setup: tw.TrainingWorkflowSetup,
    *,
    phase_id: str,
    train_results: list[EpisodeResult],
    eval_results: list[EpisodeResult],
) -> list[dict[str, Any]]:
    """Legacy replay-based export; prefer workflow ``artifact_manifest`` (stored series)."""
    videos_dir = ensure_run_layout(setup.run_dir)["videos"]
    exported: list[dict[str, Any]] = []
    runner = setup.runner

    train_ranked = sorted(
        enumerate(train_results),
        key=lambda item: float(item[1].episode_return),
        reverse=True,
    )[:3]
    for rank, (ep_idx, _result) in enumerate(train_ranked, start=1):
        replay = runner.run_serial(
            setup.agent,
            mode="eval",
            feature_config=setup.feature_config,
            observation_layout=setup.observation_layout,
            episode_idx=ep_idx,
            collect_states=True,
            train_updates_per_step=0,
            np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, f"{phase_id}/train_replay", ep_idx)),
        )
        out_path = videos_dir / f"train_ep_{ep_idx}_rank{rank}.mp4"
        export_training_episode_video_sync(replay.simulation_series, out_path)
        exported.append({"kind": "train", "episode_idx": ep_idx, "rank": rank, "path": str(out_path)})

    for ep_idx in range(len(eval_results)):
        replay = runner.run_serial(
            setup.agent,
            mode="eval",
            feature_config=setup.feature_config,
            observation_layout=setup.observation_layout,
            episode_idx=ep_idx,
            collect_states=True,
            train_updates_per_step=0,
            early_stop_on_budget_exhausted=False,
            np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, f"{phase_id}/eval_replay", ep_idx)),
        )
        out_path = videos_dir / f"eval_ep_{ep_idx}.mp4"
        export_training_episode_video_sync(replay.simulation_series, out_path)
        exported.append({"kind": "eval", "episode_idx": ep_idx, "path": str(out_path)})

    return exported


@dataclass(frozen=True)
class PhaseSpec:
    phase_id: str
    hypothesis_id: str
    run_id: str
    reward_mode: RewardForkMode
    agent_kind: Literal["mpo", "sac"]
    mpo_overrides: dict[str, Any] | None = None
    rebuild_warmup_cache: bool = False
    agent_setup_hook: Callable[[tw.TrainingWorkflowSetup], tw.TrainingWorkflowSetup] | None = None


def run_hypothesis_phase(spec: PhaseSpec, *, show_progress: bool = False) -> dict[str, Any]:
    acquire_experiment_run_lock(script=f"phase:{spec.phase_id}")
    append_overnight_log(f"START {spec.phase_id} ({spec.hypothesis_id})")

    profile = apply_runtime_context_from_dt_profile()
    set_warmup_fingerprint_extra(reward_mode=spec.reward_mode)
    activate_reward_fork(spec.reward_mode)

    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = frozen_training_config(
        run_id=f"ml_overnight_{spec.run_id}_{stamp}",
        train_episodes=int(profile.get("train_episodes", TRAIN_EPISODES)),
        rebuild_warmup_bundle_cache=spec.rebuild_warmup_cache,
    )

    setup = tw.build_training_workflow_setup(cfg)
    if spec.mpo_overrides:
        setup = _rebuild_mpo_agent(setup, replace(setup.mpo_config, **spec.mpo_overrides))
    if spec.agent_kind == "sac":
        from agents.sac_agent_fork import SACAgent

        n_targets = len(setup.mission_setup.resolve(require_camera=True).target_areas or ())
        env = tw.make_attitude_control_env(
            secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
            reward_config=setup.mpo_config.reward,
            feature_config=setup.feature_config,
            n_mission_targets=n_targets,
            observation_layout=setup.observation_layout,
        )
        setup = _replace_agent(setup, SACAgent(env, config=setup.mpo_config))
    if spec.agent_setup_hook is not None:
        setup = spec.agent_setup_hook(setup)

    t0 = time.perf_counter()
    workflow_result = tw.run_training_workflow(setup, show_progress=show_progress)
    wall_s = time.perf_counter() - t0

    train_returns = [float(ep.episode_return) for ep in workflow_result.train_results]
    eval_returns = [float(ep.episode_return) for ep in workflow_result.eval_results]
    warmup_returns = [float(ep.episode_return) for ep in workflow_result.warmup_results]
    learning_stats = _learning_stats_summary(setup.agent, workflow_result.train_results)
    signal = evaluate_learning_mode(
        train_returns,
        eval_returns,
        learning_stats=learning_stats,
        agent_kind=spec.agent_kind,
    )

    videos = [
        {
            "kind": entry["phase"],
            "episode_idx": entry["episode_idx"],
            "rank": entry.get("rank"),
            "path": entry["video"],
        }
        for entry in workflow_result.artifact_manifest
        if entry.get("video")
    ]

    debug_eps = [
        _episode_debug_row(ep, episode_idx=i) for i, ep in enumerate(workflow_result.train_results)
    ]
    kpis = {
        "phase_id": spec.phase_id,
        "hypothesis_id": spec.hypothesis_id,
        "run_id": spec.run_id,
        "run_dir": str(setup.run_dir),
        "wall_s": wall_s,
        "dt_profile": profile,
        "reward_mode": spec.reward_mode,
        "agent_kind": spec.agent_kind,
        "warmup_from_cache": cfg.use_warmup_bundle_cache,
        "warmup_returns": warmup_returns,
        "warmup_return_mean": float(np.mean(warmup_returns)) if warmup_returns else 0.0,
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "train_return_mean": float(np.mean(train_returns)) if train_returns else 0.0,
        "eval_return_mean": signal["eval_return_mean"],
        "baseline_warmup_reference_mean": BASELINE_WARMUP_RETURN_MEAN,
        "learning_signal": signal,
        "learning_stats": learning_stats,
        "debug_episodes": debug_eps,
        "artifacts": {"videos": videos},
        "last_train_kpis": workflow_result.train_kpis,
    }
    append_overnight_log(
        f"DONE {spec.phase_id} learning_mode={signal['learning_mode']} "
        f"train={train_returns} eval_mean={signal['eval_return_mean']}"
    )
    return kpis


def write_phase_error(phase_id: str, exc: BaseException) -> Path:
    path = RESULTS_DIR / f"{phase_id}_error.json"
    write_hypothesis_result(
        path,
        experiment_id="ml_algo_overnight",
        phase_id=phase_id,
        error=str(exc),
        traceback=traceback.format_exc(),
        verdict="error",
    )
    append_overnight_log(f"ERROR {phase_id}: {exc}")
    return path


def write_analysis_card(
    path: Path, *, hypothesis_id: str, json_path: Path, sections: dict[str, str]
) -> None:
    lines = [f"# Analysis — {hypothesis_id}", "", f"Source JSON: `{json_path.name}`", ""]
    for title, body in sections.items():
        lines.extend([f"## {title}", "", body.strip(), ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def verdict_from_signal(signal: dict[str, Any]) -> str:
    if signal.get("learning_mode"):
        return "supported"
    train = signal.get("train_returns") or []
    if train and all(float(r) == 0.0 for r in train):
        return "falsified"
    return "inconclusive"


__all__ = [
    "PhaseSpec",
    "append_overnight_log",
    "evaluate_learning_mode",
    "export_phase_videos",
    "load_dt_profile",
    "run_hypothesis_phase",
    "verdict_from_signal",
    "write_analysis_card",
    "write_hypothesis_result",
    "write_phase_error",
]
