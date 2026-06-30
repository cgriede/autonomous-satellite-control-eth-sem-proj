"""Exp 1: MPO shutter threshold 0.5 vs 0.9 + 15s capture credit window."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from dataclasses import replace
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"
for path in (BACKEND_DIR, S01_DIR, OVERNIGHT_ROOT, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import _cpu_budget  # noqa: F401

import numpy as np
import torch

from _capture_window_fork import activate_capture_window_fork, configure_capture_window, deactivate_capture_window_fork
from _plot_shutter import write_all_plots
from _reward_fork import activate_reward_fork
from _shutter_runner import (
    RESULTS_DIR,
    ArmSpec,
    append_log,
    run_mpo_arm,
    verdict_for_arm,
    write_analysis_card,
    write_dt_profile,
    write_hypothesis_result,
)
from _shutter_threshold_fork import shutter_threshold_fork
from _shutter_sim import DT_15, apply_dt_profile, apply_experiment_dt_profile, require_dt_profile
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra

from _frozen_baseline import EXPERIMENT_SEED, frozen_training_config
from autonomous_control.config.randomness import derive_seed
from s01_utils import training_workflow as tw

SUMMARY_JSON = RESULTS_DIR / "shutter_threshold_summary.json"
ANALYSIS_MD = EXPERIMENT_ROOT / "shutter_threshold_analysis.md"
SMOKE_JSON = RESULTS_DIR / "smoke.json"
ARM_KPIS_DIR = RESULTS_DIR / "arm_kpis"


def _arm_kpis_path(arm_id: str) -> Path:
    return ARM_KPIS_DIR / f"{arm_id}.json"


def save_arm_kpis(kpis: dict) -> None:
    ARM_KPIS_DIR.mkdir(parents=True, exist_ok=True)
    _arm_kpis_path(str(kpis["arm_id"])).write_text(
        json.dumps(kpis, indent=2, default=str),
        encoding="utf-8",
    )


def load_arm_kpis(arm_id: str) -> dict | None:
    path = _arm_kpis_path(arm_id)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def backfill_arm_kpis_from_summary() -> None:
    """Seed arm_kpis/ from summary when only summary exists (e.g. pre-persistence t05 run)."""
    if not SUMMARY_JSON.is_file():
        return
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    for arm_id, arm in (summary.get("arms") or {}).items():
        if load_arm_kpis(arm_id) is not None:
            continue
        save_arm_kpis(
            {
                "arm_id": arm_id,
                "threshold": arm.get("threshold"),
                "train_returns": arm.get("train_returns") or [],
                "shutter_cmds_per_episode": arm.get("shutter_cmds_per_episode") or [],
                "eval_return_mean": arm.get("eval_return_mean"),
                "learning_signal": {"learning_mode": arm.get("learning_mode", False)},
                "shutter_samples": [],
            }
        )


def merge_arm_results(fresh: dict[str, dict]) -> dict[str, dict]:
    """Full KPI dicts for plotting: fresh runs + cached arm_kpis for skipped arms."""
    backfill_arm_kpis_from_summary()
    merged: dict[str, dict] = {}
    for arm_id in (a.arm_id for a in DEFAULT_ARMS):
        if arm_id in fresh:
            merged[arm_id] = fresh[arm_id]
        else:
            cached = load_arm_kpis(arm_id)
            if cached is not None:
                merged[arm_id] = cached
    return merged

DEFAULT_ARMS = (
    ArmSpec("mpo_t05", 0.5, "shutter_threshold_05"),
    ArmSpec("mpo_t09", 0.9, "shutter_threshold_09"),
)


def run_smoke(*, allow_cpu: bool = False) -> dict:
    write_dt_profile(train_episodes=1)
    apply_experiment_dt_profile()
    from _shutter_sim import apply_dt_profile

    apply_dt_profile(DT_15)
    require_dt_profile(DT_15, context="ml_shutter_threshold:smoke")
    configure_capture_window(sim_dt_s=DT_15.sim_dt_s)
    set_warmup_fingerprint_extra(
        sim_dt_s=DT_15.sim_dt_s,
        controller_interval_s=DT_15.controller_interval_s,
        reward_mode="sparse",
        shutter_threshold=0.5,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("sparse")
    activate_capture_window_fork()

    if not torch.cuda.is_available() and not allow_cpu:
        raise RuntimeError("CUDA required for smoke; pass --allow-cpu for debug.")

    cfg = replace(
        frozen_training_config(run_id="ml_shutter_smoke", train_episodes=0, rebuild_warmup_bundle_cache=True),
        warmup_episodes=1,
        eval_episodes=0,
        use_warmup_bundle_cache=False,
        background_artifacts=False,
    )
    try:
        with shutter_threshold_fork(0.5):
            setup = tw.build_training_workflow_setup(cfg)
            warmup = setup.runner.run_serial(
                setup.agent,
                mode="warmup",
                episode_idx=0,
                collect_states=False,
                show_training_context=False,
                train_updates_per_step=0,
                feature_config=setup.feature_config,
                observation_layout=setup.observation_layout,
                np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "shutter_smoke", 0)),
            )
            if len(setup.agent.buffer) == 0:
                raise RuntimeError("Smoke warmup produced empty buffer.")
            setup.agent.train()
    finally:
        deactivate_capture_window_fork()

    payload = {
        "passed": True,
        "warmup_return": float(warmup.episode_return),
        "warmup_steps": int(warmup.steps),
        "buffer_size": len(setup.agent.buffer),
    }
    write_hypothesis_result(SMOKE_JSON, phase="smoke", experiment_id="ml_shutter_threshold", **payload)
    append_log(f"SMOKE OK warmup_return={payload['warmup_return']:.1f}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="ml_shutter_threshold experiment")
    parser.add_argument("--smoke", action="store_true", help="Quick smoke test only")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument(
        "--arms",
        default="mpo_t05,mpo_t09",
        help="Comma-separated arm ids (default: mpo_t05,mpo_t09)",
    )
    parser.add_argument("--train-episodes", type=int, default=7)
    args = parser.parse_args()

    if args.smoke:
        run_smoke(allow_cpu=args.allow_cpu)
        print(f"Smoke OK → {SMOKE_JSON}")
        return

    write_dt_profile(train_episodes=int(args.train_episodes))
    arm_map = {a.arm_id: a for a in DEFAULT_ARMS}
    selected = [arm_map[x.strip()] for x in args.arms.split(",") if x.strip() in arm_map]
    if not selected:
        raise SystemExit(f"No valid arms in {args.arms!r}; choose from {list(arm_map)}")

    results: dict[str, dict] = {}
    baseline_cmds: list[int] | None = None
    backfill_arm_kpis_from_summary()
    cached_t05 = load_arm_kpis("mpo_t05")
    if cached_t05:
        baseline_cmds = list(cached_t05.get("shutter_cmds_per_episode") or [])
    for spec in selected:
        try:
            kpis = run_mpo_arm(spec, show_progress=args.show_progress)
            results[spec.arm_id] = kpis
            save_arm_kpis(kpis)
            if spec.arm_id == "mpo_t05":
                baseline_cmds = list(kpis.get("shutter_cmds_per_episode") or [])
        except Exception as exc:
            err_path = RESULTS_DIR / f"{spec.arm_id}_error.json"
            write_hypothesis_result(
                err_path,
                experiment_id="ml_shutter_threshold",
                arm_id=spec.arm_id,
                error=str(exc),
                traceback=traceback.format_exc(),
                verdict="error",
            )
            append_log(f"ERROR {spec.arm_id}: {exc}")
            raise

    plot_arms = merge_arm_results(results)
    plot_paths = write_all_plots(plot_arms)
    arm_summaries = {}
    for arm_id, kpis in plot_arms.items():
        v = verdict_for_arm(kpis, baseline_cmds=baseline_cmds if arm_id != "mpo_t05" else None)
        arm_summaries[arm_id] = {
            "verdict": v,
            "threshold": kpis.get("threshold"),
            "learning_mode": (kpis.get("learning_signal") or {}).get("learning_mode"),
            "train_returns": kpis.get("train_returns") or [],
            "shutter_cmds_per_episode": kpis.get("shutter_cmds_per_episode") or [],
            "eval_return_mean": kpis.get("eval_return_mean"),
            "wall_s": kpis.get("wall_s"),
        }

    summary = {
        "experiment_id": "ml_shutter_threshold",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "dt_profile": json.loads((RESULTS_DIR / "dt_profile.json").read_text(encoding="utf-8")),
        "arms": arm_summaries,
        "plots": plot_paths,
    }
    write_hypothesis_result(SUMMARY_JSON, **summary)
    write_analysis_card(
        ANALYSIS_MD,
        hypothesis_id="shutter_threshold_mpo",
        json_path=SUMMARY_JSON,
        sections={
            "Hypothesis": "Threshold 0.9 reduces MPO shutter spam vs 0.5 with 15s capture window.",
            "Arms": json.dumps(arm_summaries, indent=2),
            "Plots": "\n".join(f"- `{p}`" for p in plot_paths),
            "Verdict": json.dumps({k: v["verdict"] for k, v in arm_summaries.items()}),
        },
    )
    print(f"Wrote {SUMMARY_JSON}")
    for arm_id, s in arm_summaries.items():
        print(f"  {arm_id}: verdict={s['verdict']} shutter_cmds={s['shutter_cmds_per_episode']}")


if __name__ == "__main__":
    main()
