"""Run MPO arms with shutter threshold + capture-window forks."""

from __future__ import annotations

import importlib.util
import sys
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import _cpu_budget  # noqa: F401

EXPERIMENT_ROOT = Path(__file__).resolve().parent
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, OVERNIGHT_ROOT, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import numpy as np

from _capture_window_fork import (  # noqa: E402
    activate_capture_window_fork,
    configure_capture_window,
    deactivate_capture_window_fork,
    reset_capture_window,
)
from _collect_shutter_samples import ShutterSampleCollector  # noqa: E402
from _run_guard import acquire_experiment_run_lock  # noqa: E402
from _shutter_threshold_fork import shutter_threshold_fork  # noqa: E402
from _shutter_sim import (  # noqa: E402
    DT_15,
    apply_experiment_dt_profile,
    apply_dt_profile,
    get_applied_dt_profile,
    require_dt_profile,
    write_dt_profile,
)

from _frozen_baseline import frozen_training_config  # noqa: E402
from _reward_fork import activate_reward_fork  # noqa: E402
from _warmup_fingerprint_patch import (  # noqa: E402
    activate_warmup_fingerprint_patch,
    set_warmup_fingerprint_extra,
)
from s01_utils import training_workflow as tw  # noqa: E402

_overnight_spec = importlib.util.spec_from_file_location(
    "ml_overnight_runner_common",
    OVERNIGHT_ROOT / "_runner_common.py",
)
assert _overnight_spec and _overnight_spec.loader
_overnight_runner = importlib.util.module_from_spec(_overnight_spec)
sys.modules[_overnight_spec.name] = _overnight_runner
_overnight_spec.loader.exec_module(_overnight_runner)

_episode_debug_row = _overnight_runner._episode_debug_row
_learning_stats_summary = _overnight_runner._learning_stats_summary
evaluate_learning_mode = _overnight_runner.evaluate_learning_mode
write_analysis_card = _overnight_runner.write_analysis_card
write_hypothesis_result = _overnight_runner.write_hypothesis_result

RESULTS_DIR = EXPERIMENT_ROOT / "results"
EXPERIMENT_LOG = RESULTS_DIR / "shutter_threshold.log"


def append_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


@dataclass(frozen=True)
class ArmSpec:
    arm_id: str
    threshold: float
    hypothesis_id: str


def run_mpo_arm(spec: ArmSpec, *, show_progress: bool = False) -> dict[str, Any]:
    acquire_experiment_run_lock(script=f"arm:{spec.arm_id}")
    append_log(f"START {spec.arm_id} threshold={spec.threshold}")

    profile = apply_experiment_dt_profile()
    apply_dt_profile(DT_15)
    require_dt_profile(DT_15, context=f"ml_shutter_threshold:{spec.arm_id}")
    applied = get_applied_dt_profile()
    append_log(
        f"DT profile arm={spec.arm_id} "
        f"sim_dt_s={applied['sim_dt_s']} controller_interval_s={applied['controller_interval_s']}"
    )
    configure_capture_window(sim_dt_s=float(profile["sim_dt_s"]))
    set_warmup_fingerprint_extra(
        sim_dt_s=profile.get("sim_dt_s"),
        controller_interval_s=profile.get("controller_interval_s"),
        reward_mode="sparse",
        shutter_threshold=spec.threshold,
        capture_window_s=15.0,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("sparse")
    activate_capture_window_fork()
    reset_capture_window()

    collector = ShutterSampleCollector(threshold=spec.threshold)
    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = replace(
        frozen_training_config(
            run_id=f"ml_shutter_{spec.arm_id}_{stamp}",
            train_episodes=int(profile.get("train_episodes", 7)),
            rebuild_warmup_bundle_cache=True,
        ),
        background_artifacts=False,
    )

    try:
        with shutter_threshold_fork(spec.threshold):
            collector.activate()
            try:
                setup = tw.build_training_workflow_setup(cfg)
                t0 = time.perf_counter()
                workflow_result = tw.run_training_workflow(setup, show_progress=show_progress)
                wall_s = time.perf_counter() - t0
            finally:
                collector.deactivate()
    finally:
        deactivate_capture_window_fork()

    train_returns = [float(ep.episode_return) for ep in workflow_result.train_results]
    eval_returns = [float(ep.episode_return) for ep in workflow_result.eval_results]
    learning_stats = _learning_stats_summary(setup.agent, workflow_result.train_results)
    signal = evaluate_learning_mode(
        train_returns,
        eval_returns,
        learning_stats=learning_stats,
        agent_kind="mpo",
    )
    debug_eps = [
        _episode_debug_row(ep, episode_idx=i) for i, ep in enumerate(workflow_result.train_results)
    ]
    shutter_cmds_per_ep = [int(row["n_shutter_cmds"]) for row in debug_eps]

    kpis = {
        "arm_id": spec.arm_id,
        "threshold": spec.threshold,
        "hypothesis_id": spec.hypothesis_id,
        "run_dir": str(setup.run_dir),
        "wall_s": wall_s,
        "dt_profile": profile,
        "reward_mode": "sparse",
        "capture_window_s": 15.0,
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "eval_return_mean": signal["eval_return_mean"],
        "learning_signal": signal,
        "learning_stats": learning_stats,
        "debug_episodes": debug_eps,
        "shutter_cmds_per_episode": shutter_cmds_per_ep,
        "shutter_samples_n": len(collector.samples),
        "shutter_samples": [
            {
                "episode_idx": s.episode_idx,
                "shutter_gym": s.shutter_gym,
                "shutter_unit": s.shutter_unit,
                "fired": s.fired,
            }
            for s in collector.samples[:5000]
        ],
    }
    append_log(
        f"DONE {spec.arm_id} learning_mode={signal['learning_mode']} "
        f"shutter_cmds={shutter_cmds_per_ep}"
    )
    artifact_errors = list(getattr(workflow_result, "artifact_errors", []) or [])
    if artifact_errors:
        append_log(f"ARTIFACT_WARN {spec.arm_id} n={len(artifact_errors)} first={artifact_errors[0][:120]}")
    return kpis


def verdict_for_arm(kpis: dict[str, Any], *, baseline_cmds: list[int] | None) -> str:
    signal = kpis.get("learning_signal") or {}
    if signal.get("learning_mode"):
        return "supported"
    cmds = kpis.get("shutter_cmds_per_episode") or []
    if baseline_cmds and cmds and float(np.mean(cmds)) < float(np.mean(baseline_cmds)) * 0.5:
        return "supported"
    if cmds and all(int(c) == 0 for c in cmds):
        return "falsified"
    return "inconclusive"


__all__ = [
    "ArmSpec",
    "append_log",
    "run_mpo_arm",
    "verdict_for_arm",
    "write_analysis_card",
    "write_hypothesis_result",
    "write_dt_profile",
    "RESULTS_DIR",
]
