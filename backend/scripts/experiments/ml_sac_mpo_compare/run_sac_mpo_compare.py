"""Exp 3: SAC sparse vs MPO dense @ dt 1.5s (same-day compare, patience early abort)."""

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
_PATH_ROOTS = (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT, OVERNIGHT_ROOT)
for path in reversed(_PATH_ROOTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import _cpu_budget  # noqa: F401

import numpy as np
import torch

from _compare_runner import (
    RESULTS_DIR,
    append_log,
    default_arms,
    run_compare_arm,
    verdict_for_compare,
    write_analysis_card,
    write_hypothesis_result,
)
from _compare_sim import (
    FIXED_COMPARE_PROFILE,
    apply_dt_profile,
    apply_experiment_dt_profile,
    require_dt_profile,
    write_fixed_compare_dt_profile,
)
from _compare_frozen import COMPARE_TRAIN_EPISODES_DEFAULT, EXPERIMENT_SEED, PATIENCE_EPISODES_DEFAULT, frozen_training_config
from _reward_fork import activate_reward_fork
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra

from autonomous_control.config.randomness import derive_seed
from s01_utils import training_workflow as tw
from utils.ml_training.training_run_artifacts import finalize_episodes_csv

SUMMARY_JSON = RESULTS_DIR / "compare_sac_mpo.json"
ANALYSIS_MD = EXPERIMENT_ROOT / "compare_sac_mpo_analysis.md"
SMOKE_JSON = RESULTS_DIR / "smoke.json"


def _load_sac_agent():
    import importlib.util

    _sac_spec = importlib.util.spec_from_file_location(
        "ml_compare_smoke_sac_fork",
        OVERNIGHT_ROOT / "agents" / "sac_agent_fork.py",
    )
    assert _sac_spec and _sac_spec.loader
    _sac_mod = importlib.util.module_from_spec(_sac_spec)
    _sac_spec.loader.exec_module(_sac_mod)
    return _sac_mod.SACAgent


def run_smoke(*, allow_cpu: bool = False, enable_tensorboard: bool = False) -> dict:
    write_fixed_compare_dt_profile(train_episodes=1)
    apply_experiment_dt_profile()
    apply_dt_profile(FIXED_COMPARE_PROFILE)
    require_dt_profile(FIXED_COMPARE_PROFILE, context="ml_sac_mpo_compare:smoke")
    set_warmup_fingerprint_extra(
        sim_dt_s=FIXED_COMPARE_PROFILE.sim_dt_s,
        controller_interval_s=FIXED_COMPARE_PROFILE.controller_interval_s,
        reward_mode="sparse",
        compare_arm="smoke",
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("sparse")

    if not torch.cuda.is_available() and not allow_cpu:
        raise RuntimeError("CUDA required for smoke; pass --allow-cpu for debug.")

    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = replace(
        frozen_training_config(
            run_id=f"ml_compare_smoke_{stamp}",
            train_episodes=0,
            rebuild_warmup_bundle_cache=True,
        ),
        warmup_episodes=1,
        eval_episodes=0,
        use_warmup_bundle_cache=False,
        background_artifacts=False,
    )
    setup = tw.build_training_workflow_setup(cfg)
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

    warmup = setup.runner.run_serial(
        setup.agent,
        mode="warmup",
        episode_idx=0,
        collect_states=False,
        show_training_context=False,
        train_updates_per_step=0,
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "compare_smoke", 0)),
    )
    if len(setup.agent.buffer) == 0:
        raise RuntimeError("Smoke warmup produced empty buffer.")
    setup.agent.train()

    # Dense reward fork activates without error.
    activate_reward_fork("dense")

    tensorboard_run_dir: str | None = None
    if enable_tensorboard:
        tb_stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
        tb_cfg = replace(
            frozen_training_config(
                run_id=f"ml_compare_smoke_tb_{tb_stamp}",
                train_episodes=1,
                rebuild_warmup_bundle_cache=True,
            ),
            warmup_episodes=1,
            eval_episodes=0,
            enable_tensorboard=True,
            use_warmup_bundle_cache=False,
            background_artifacts=False,
            train_episode_videos=0,
            eval_episode_videos=0,
            export_episode_reward_plots=False,
        )
        tb_setup = tw.build_training_workflow_setup(tb_cfg)
        tb_env = tw.make_attitude_control_env(
            secondary_camera_observation_line_n_bins=tb_setup.secondary_camera_bins,
            reward_config=tb_setup.mpo_config.reward,
            feature_config=tb_setup.feature_config,
            n_mission_targets=len(
                tb_setup.mission_setup.resolve(require_camera=True).target_areas or ()
            ),
            observation_layout=tb_setup.observation_layout,
        )
        tb_setup = replace(tb_setup, agent=SACAgent(tb_env, config=tb_setup.mpo_config))
        tb_ctx = tw.open_training_workflow(tb_setup, show_progress=False)
        try:
            tw.run_warmup(tb_ctx)
            tw.run_training(tb_ctx)
            finalize_episodes_csv(tb_setup.run_dir, tb_ctx.episode_rows)
        finally:
            tb_ctx.close()
        tb_dir = tb_setup.run_dir / "tensorboard"
        if not tb_dir.is_dir() or not any(tb_dir.glob("events.out.tfevents.*")):
            raise RuntimeError(f"TensorBoard smoke failed: missing event files in {tb_dir}")
        episodes_csv = tb_setup.run_dir / "episodes.csv"
        if not episodes_csv.is_file():
            raise RuntimeError(f"TensorBoard smoke failed: missing {episodes_csv}")
        from utils.ml_training.tensorboard_run_writer import verify_train_return_parity

        verify_train_return_parity(tb_setup.run_dir)
        tensorboard_run_dir = str(tb_setup.run_dir)

    payload = {
        "passed": True,
        "warmup_return": float(warmup.episode_return),
        "warmup_steps": int(warmup.steps),
        "buffer_size": len(setup.agent.buffer),
        "reward_modes_checked": ["sparse", "dense"],
        "tensorboard_run_dir": tensorboard_run_dir,
    }
    write_hypothesis_result(
        SMOKE_JSON,
        phase="smoke",
        experiment_id="ml_sac_mpo_compare",
        **payload,
    )
    append_log(f"SMOKE OK warmup_return={payload['warmup_return']:.1f}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="ml_sac_mpo_compare — Exp 3 SAC vs MPO")
    parser.add_argument("--smoke", action="store_true", help="Quick smoke test only")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--arms", default="compare_sac,compare_mpo", help="Comma-separated arm ids")
    parser.add_argument("--train-episodes", type=int, default=COMPARE_TRAIN_EPISODES_DEFAULT)
    parser.add_argument("--patience-episodes", type=int, default=PATIENCE_EPISODES_DEFAULT)
    parser.add_argument(
        "--trim-artifacts",
        action="store_true",
        help="Skip train MP4s and export only top eval video (faster; opt-in).",
    )
    parser.add_argument(
        "--tensorboard",
        action="store_true",
        help="Enable TensorBoard episode logging (opt-in until review sign-off).",
    )
    args = parser.parse_args()

    if args.smoke:
        run_smoke(allow_cpu=args.allow_cpu, enable_tensorboard=args.tensorboard)
        print(f"Smoke OK → {SMOKE_JSON}")
        return

    write_fixed_compare_dt_profile(train_episodes=int(args.train_episodes))
    arm_map = {a.arm_id: a for a in default_arms()}
    selected = [arm_map[x.strip()] for x in args.arms.split(",") if x.strip() in arm_map]
    if not selected:
        raise SystemExit(f"No valid arms in {args.arms!r}; choose from {list(arm_map)}")

    results: dict[str, dict] = {}
    for spec in selected:
        try:
            kpis = run_compare_arm(
                spec,
                show_progress=args.show_progress,
                trim_artifacts=args.trim_artifacts,
                max_train_episodes=int(args.train_episodes),
                patience_episodes=int(args.patience_episodes),
                enable_tensorboard=args.tensorboard,
            )
            results[spec.arm_id] = kpis
        except Exception as exc:
            err_path = RESULTS_DIR / f"{spec.arm_id}_error.json"
            write_hypothesis_result(
                err_path,
                experiment_id="ml_sac_mpo_compare",
                arm_id=spec.arm_id,
                error=str(exc),
                traceback=traceback.format_exc(),
                verdict="error",
            )
            append_log(f"ERROR {spec.arm_id}: {exc}")
            raise

    arm_summaries = {}
    for arm_id, kpis in results.items():
        signal = kpis["learning_signal"]
        abort = kpis.get("early_abort") or {}
        arm_summaries[arm_id] = {
            "verdict": verdict_for_compare(kpis),
            "agent_kind": kpis["agent_kind"],
            "reward_mode": kpis["reward_mode"],
            "learning_mode": signal["learning_mode"],
            "train_returns": kpis["train_returns"],
            "eval_return_mean": kpis["eval_return_mean"],
            "wall_s": kpis["wall_s"],
            "early_aborted": abort.get("early_aborted"),
            "train_episodes_completed": abort.get("train_episodes_completed"),
            "best_train_return": abort.get("best_train_return"),
        }

    summary = {
        "experiment_id": "ml_sac_mpo_compare",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "dt_profile": json.loads((RESULTS_DIR / "dt_profile.json").read_text(encoding="utf-8")),
        "patience_episodes": int(args.patience_episodes),
        "arms": arm_summaries,
    }
    write_hypothesis_result(SUMMARY_JSON, **summary)
    write_analysis_card(
        ANALYSIS_MD,
        hypothesis_id="sac_mpo_compare",
        json_path=SUMMARY_JSON,
        sections={
            "Hypothesis": "SAC sparse vs MPO dense @ dt 1.5s — algorithm × reward pairing.",
            "Arms": json.dumps(arm_summaries, indent=2),
            "Verdict": json.dumps({k: v["verdict"] for k, v in arm_summaries.items()}),
        },
    )
    print(f"Wrote {SUMMARY_JSON}")
    for arm_id, s in arm_summaries.items():
        print(
            f"  {arm_id}: verdict={s['verdict']} learning_mode={s['learning_mode']} "
            f"eps={s['train_episodes_completed']} early_aborted={s['early_aborted']}"
        )


if __name__ == "__main__":
    main()
