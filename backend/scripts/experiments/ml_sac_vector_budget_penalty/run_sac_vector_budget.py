"""Exp 7: SAC vector sparse + budget-exhausted shutter penalty (single treatment arm)."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"


def _load_local_module(name: str):
    import importlib.util

    path = EXPERIMENT_ROOT / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(S01_DIR) not in sys.path:
    sys.path.insert(0, str(S01_DIR))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

_budget_sim = _load_local_module("_sim_constants_fork")
FIXED_BUDGET_DT = _budget_sim.FIXED_BUDGET_DT
apply_dt_profile = _budget_sim.apply_dt_profile
apply_experiment_dt_profile = _budget_sim.apply_experiment_dt_profile
require_dt_profile = _budget_sim.require_dt_profile
write_fixed_budget_dt_profile = _budget_sim.write_fixed_budget_dt_profile

for _local_name in (
    "_reward_fork",
    "_warmup_fingerprint_patch",
    "_run_guard",
    "_runner_common",
    "_budget_frozen",
    "_budget_runner",
):
    _load_local_module(_local_name)

from _budget_frozen import EXPERIMENT_SEED, frozen_training_config, sac_mpo_config_overrides  # noqa: E402
from _budget_runner import EXPERIMENT_ID, append_log, finalize_penalty_on_from_run, run_penalty_on  # noqa: E402
from _reward_fork import activate_reward_fork, budget_penalty_enabled  # noqa: E402
from _runner_common import RESULTS_DIR, write_hypothesis_result  # noqa: E402
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra  # noqa: E402

if str(OVERNIGHT_ROOT) not in sys.path:
    sys.path.insert(0, str(OVERNIGHT_ROOT))

import _cpu_budget  # noqa: F401

import numpy as np
import torch

from autonomous_control.config.randomness import derive_seed
from s01_utils import training_workflow as tw
from utils.ml_training.training_run_artifacts import finalize_episodes_csv

SUMMARY_JSON = RESULTS_DIR / "sac_vector_budget.json"
SMOKE_JSON = RESULTS_DIR / "smoke.json"


def _load_sac_agent():
    import importlib.util

    _sac_spec = importlib.util.spec_from_file_location(
        "ml_budget_smoke_sac_fork",
        OVERNIGHT_ROOT / "agents" / "sac_agent_fork.py",
    )
    assert _sac_spec and _sac_spec.loader
    _sac_mod = importlib.util.module_from_spec(_sac_spec)
    _sac_spec.loader.exec_module(_sac_mod)
    return _sac_mod.SACAgent


def _verify_run_config(run_dir: Path) -> dict:
    config_path = run_dir / "config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Smoke missing config.json at {config_path}")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    exp = payload.get("experiment") or {}
    if exp.get("experiment_id") != EXPERIMENT_ID:
        raise RuntimeError(f"config experiment_id mismatch: {exp.get('experiment_id')}")
    if exp.get("attitude_request_mode") != "vector":
        raise RuntimeError(f"expected vector mode, got {exp.get('attitude_request_mode')!r}")
    if not exp.get("budget_exhausted_shutter_penalty"):
        raise RuntimeError("budget_exhausted_shutter_penalty not set in config experiment block")
    return exp


def run_smoke(*, allow_cpu: bool = False, enable_tensorboard: bool = True) -> dict:
    write_fixed_budget_dt_profile(train_episodes=1)
    apply_experiment_dt_profile()
    apply_dt_profile(FIXED_BUDGET_DT)
    require_dt_profile(FIXED_BUDGET_DT, context=f"{EXPERIMENT_ID}:smoke")

    set_warmup_fingerprint_extra(
        sim_dt_s=FIXED_BUDGET_DT.sim_dt_s,
        controller_interval_s=FIXED_BUDGET_DT.controller_interval_s,
        reward_mode="sparse",
        budget_arm="smoke",
        attitude_request_mode="vector",
        budget_exhausted_shutter_penalty=True,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork(budget_exhausted_shutter_penalty=True)

    if not torch.cuda.is_available() and not allow_cpu:
        raise RuntimeError("CUDA required for smoke; pass --allow-cpu for debug.")

    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    smoke_train_eps = 1 if enable_tensorboard else 0
    cfg = replace(
        frozen_training_config(
            run_id=f"ml_sac_vector_budget_smoke_{stamp}",
            train_episodes=smoke_train_eps,
            rebuild_warmup_bundle_cache=True,
            experiment_name="sac vector budget smoke",
        ),
        warmup_episodes=1,
        eval_episodes=0,
        use_warmup_bundle_cache=False,
        background_artifacts=False,
        train_episode_videos=0,
        eval_episode_videos=0,
        export_episode_reward_plots=False,
    )
    if enable_tensorboard:
        cfg = replace(cfg, enable_tensorboard=True)

    setup = tw.build_training_workflow_setup(cfg)
    setup = replace(setup, mpo_config=sac_mpo_config_overrides(setup.mpo_config))

    from _budget_runner import _patch_run_config

    _patch_run_config(
        setup.run_dir,
        dt_profile={
            "sim_dt_s": FIXED_BUDGET_DT.sim_dt_s,
            "controller_interval_s": FIXED_BUDGET_DT.controller_interval_s,
            "label": FIXED_BUDGET_DT.label,
        },
        enable_tensorboard=enable_tensorboard,
    )

    env = tw.make_attitude_control_env(
        secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
        reward_config=setup.mpo_config.reward,
        feature_config=setup.feature_config,
        n_mission_targets=len(
            setup.mission_setup.resolve(require_camera=True).target_areas or ()
        ),
        observation_layout=setup.observation_layout,
    )
    SACAgent = _load_sac_agent()
    setup = replace(setup, agent=SACAgent(env, config=setup.mpo_config))

    if enable_tensorboard:
        ctx = tw.open_training_workflow(setup, show_progress=False)
        try:
            tw.run_warmup(ctx)
            tw.run_training(ctx)
            finalize_episodes_csv(setup.run_dir, ctx.episode_rows)
        finally:
            ctx.close()
        tb_dir = setup.run_dir / "tensorboard"
        if not tb_dir.is_dir() or not any(tb_dir.glob("events.out.tfevents.*")):
            raise RuntimeError(f"TensorBoard smoke failed: missing event files in {tb_dir}")
        from utils.ml_training.tensorboard_run_writer import verify_train_return_parity

        verify_train_return_parity(setup.run_dir)
        exp_block = _verify_run_config(setup.run_dir)
        payload = {
            "passed": True,
            "arm_id": "penalty_on",
            "attitude_request_mode": "vector",
            "budget_exhausted_shutter_penalty": budget_penalty_enabled(),
            "tensorboard_run_dir": str(setup.run_dir),
            "tensorboard_dir": str(tb_dir),
            "run_dir": str(setup.run_dir),
            "config_experiment": exp_block,
        }
    else:
        warmup = setup.runner.run_serial(
            setup.agent,
            mode="warmup",
            episode_idx=0,
            collect_states=False,
            show_training_context=False,
            train_updates_per_step=0,
            feature_config=setup.feature_config,
            observation_layout=setup.observation_layout,
            np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "budget_smoke", 0)),
        )
        if len(setup.agent.buffer) == 0:
            raise RuntimeError("Smoke warmup produced empty buffer.")
        train_ep = setup.runner.run_serial(
            setup.agent,
            mode="train",
            episode_idx=0,
            collect_states=False,
            show_training_context=False,
            train_updates_per_step=1,
            feature_config=setup.feature_config,
            observation_layout=setup.observation_layout,
            np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "budget_smoke_train", 0)),
        )
        setup.agent.train()
        exp_block = _verify_run_config(setup.run_dir)
        payload = {
            "passed": True,
            "arm_id": "penalty_on",
            "attitude_request_mode": "vector",
            "budget_exhausted_shutter_penalty": budget_penalty_enabled(),
            "warmup_return": float(warmup.episode_return),
            "train_return": float(train_ep.episode_return),
            "buffer_size": len(setup.agent.buffer),
            "run_dir": str(setup.run_dir),
            "config_experiment": exp_block,
        }

    write_hypothesis_result(SMOKE_JSON, phase="smoke", experiment_id=EXPERIMENT_ID, **payload)
    append_log(f"SMOKE OK tensorboard={enable_tensorboard}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="ml_sac_vector_budget_penalty — Exp 7")
    parser.add_argument("--smoke", action="store_true", help="Quick smoke (vector + penalty fork)")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--train-episodes", type=int, default=50)
    parser.add_argument(
        "--trim-artifacts",
        action="store_true",
        help="Skip train MP4s and export only top eval video (faster; opt-in).",
    )
    parser.add_argument(
        "--no-tensorboard",
        action="store_true",
        help="Disable TensorBoard episode logging (on by default for Exp 7 live test).",
    )
    parser.add_argument(
        "--finalize-run",
        type=Path,
        metavar="RUN_DIR",
        help="Recover KPI JSON + MP4s from a completed run that crashed during post-processing.",
    )
    parser.add_argument(
        "--no-export-videos",
        action="store_true",
        help="With --finalize-run, skip MP4 export (KPI JSON only).",
    )
    args = parser.parse_args()
    enable_tb = not args.no_tensorboard

    if args.finalize_run is not None:
        kpis = finalize_penalty_on_from_run(
            args.finalize_run,
            show_progress=args.show_progress,
            export_videos=not args.no_export_videos,
        )
        signal = kpis["learning_signal"]
        summary = {
            "experiment_id": EXPERIMENT_ID,
            "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "dt_profile": json.loads((RESULTS_DIR / "dt_profile.json").read_text(encoding="utf-8")),
            "arms": {
                "penalty_on": {
                    "verdict": "pending",
                    "learning_mode": signal["learning_mode"],
                    "eval_return_mean": kpis["eval_return_mean"],
                    "post_budget_shutter_cmds_total": kpis["post_budget_shutter_cmds"]["total"],
                    "tensorboard_dir": kpis.get("tensorboard_dir"),
                    "wall_s": kpis["wall_s"],
                    "run_dir": kpis["run_dir"],
                    "finalized_from_crash": True,
                }
            },
            "baseline_ref1": kpis["baseline_ref1"],
            "note": "Recovered via --finalize-run after post-processing crash.",
        }
        write_hypothesis_result(SUMMARY_JSON, **summary)
        print(f"Wrote {SUMMARY_JSON}")
        print(
            f"  penalty_on: learning_mode={signal['learning_mode']} "
            f"eval_mean={kpis['eval_return_mean']} post_budget_cmds={kpis['post_budget_shutter_cmds']['total']}"
        )
        return

    if args.smoke:
        run_smoke(allow_cpu=args.allow_cpu, enable_tensorboard=enable_tb)
        print(f"Smoke OK → {SMOKE_JSON}")
        return

    write_fixed_budget_dt_profile(train_episodes=int(args.train_episodes))
    try:
        kpis = run_penalty_on(
            show_progress=args.show_progress,
            trim_artifacts=args.trim_artifacts,
            train_episodes=int(args.train_episodes),
            enable_tensorboard=enable_tb,
        )
    except Exception as exc:
        err_path = RESULTS_DIR / "penalty_on_error.json"
        write_hypothesis_result(
            err_path,
            experiment_id=EXPERIMENT_ID,
            arm_id="penalty_on",
            error=str(exc),
            traceback=traceback.format_exc(),
            verdict="error",
        )
        append_log(f"ERROR penalty_on: {exc}")
        raise

    signal = kpis["learning_signal"]
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "dt_profile": json.loads((RESULTS_DIR / "dt_profile.json").read_text(encoding="utf-8")),
        "arms": {
            "penalty_on": {
                "verdict": "pending",
                "learning_mode": signal["learning_mode"],
                "eval_return_mean": kpis["eval_return_mean"],
                "post_budget_shutter_cmds_total": kpis["post_budget_shutter_cmds"]["total"],
                "tensorboard_dir": kpis.get("tensorboard_dir"),
                "wall_s": kpis["wall_s"],
                "run_dir": kpis["run_dir"],
            }
        },
        "baseline_ref1": kpis["baseline_ref1"],
        "note": "Compare penalty_on to Exp 4 Ref1 baseline (no penalty_off re-run).",
    }
    write_hypothesis_result(SUMMARY_JSON, **summary)
    print(f"Wrote {SUMMARY_JSON}")
    print(
        f"  penalty_on: learning_mode={signal['learning_mode']} "
        f"eval_mean={kpis['eval_return_mean']} tb={kpis.get('tensorboard_dir')}"
    )


if __name__ == "__main__":
    main()
