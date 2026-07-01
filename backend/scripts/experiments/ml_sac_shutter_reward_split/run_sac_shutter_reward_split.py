"""Exp 9: SAC vector shutter reward split — waste_off vs Exp 7 both_on baseline."""

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

_split_sim = _load_local_module("_sim_constants_fork")
FIXED_SPLIT_DT = _split_sim.FIXED_SPLIT_DT
apply_experiment_dt_profile = _split_sim.apply_experiment_dt_profile
require_dt_profile = _split_sim.require_dt_profile
write_fixed_split_dt_profile = _split_sim.write_fixed_split_dt_profile

for _local_name in (
    "_reward_fork",
    "_warmup_fingerprint_patch",
    "_run_guard",
    "_runner_common",
    "_split_frozen",
    "_split_runner",
):
    _load_local_module(_local_name)

from _reward_fork import activate_reward_fork  # noqa: E402
from _runner_common import RESULTS_DIR, baseline_exp7_metadata, write_hypothesis_result  # noqa: E402
from _split_frozen import (  # noqa: E402
    EXPERIMENT_SEED,
    frozen_training_config,
    reward_waste_off_budget_on,
    sac_mpo_config_overrides,
)
from _split_runner import (  # noqa: E402
    ARM_WASTE_OFF,
    EXPERIMENT_ID,
    append_log,
    run_waste_off_budget_on,
)
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra  # noqa: E402

if str(OVERNIGHT_ROOT) not in sys.path:
    sys.path.insert(0, str(OVERNIGHT_ROOT))

import _cpu_budget  # noqa: F401

import numpy as np
import torch

from autonomous_control.config.randomness import derive_seed
from s01_utils import training_workflow as tw
from utils.ml_training.training_run_artifacts import finalize_episodes_csv

SUMMARY_JSON = RESULTS_DIR / "sac_shutter_reward_split.json"
SMOKE_JSON = RESULTS_DIR / "smoke.json"


def _load_sac_agent():
    import importlib.util

    _sac_spec = importlib.util.spec_from_file_location(
        "ml_split_smoke_sac_fork",
        OVERNIGHT_ROOT / "agents" / "sac_agent_fork.py",
    )
    assert _sac_spec and _sac_spec.loader
    _sac_mod = importlib.util.module_from_spec(_sac_spec)
    _sac_spec.loader.exec_module(_sac_mod)
    return _sac_mod.SACAgent


def run_smoke(*, allow_cpu: bool = False, enable_tensorboard: bool = False) -> None:
    write_fixed_split_dt_profile(train_episodes=1)
    apply_experiment_dt_profile()
    require_dt_profile(FIXED_SPLIT_DT, context=f"{EXPERIMENT_ID}:smoke")

    set_warmup_fingerprint_extra(
        sim_dt_s=FIXED_SPLIT_DT.sim_dt_s,
        controller_interval_s=FIXED_SPLIT_DT.controller_interval_s,
        reward_mode="sparse",
        budget_arm=ARM_WASTE_OFF,
        attitude_request_mode="vector",
        enable_shutter_waste_penalty=False,
        enable_budget_exhausted_shutter_penalty=True,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork()

    if not torch.cuda.is_available() and not allow_cpu:
        raise RuntimeError("CUDA required for smoke; pass --allow-cpu for debug.")

    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = replace(
        frozen_training_config(
            run_id=f"ml_sac_shutter_split_smoke_{stamp}",
            train_episodes=1 if enable_tensorboard else 0,
            rebuild_warmup_bundle_cache=True,
            experiment_name="sac shutter split smoke",
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
    mpo = reward_waste_off_budget_on(sac_mpo_config_overrides(setup.mpo_config))
    setup = replace(setup, mpo_config=mpo)

    assert not setup.mpo_config.reward.enable_shutter_waste_penalty
    assert setup.mpo_config.reward.enable_budget_exhausted_shutter_penalty

    n_targets = len(setup.mission_setup.resolve(require_camera=True).target_areas or ())
    env = tw.make_attitude_control_env(
        secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
        reward_config=setup.mpo_config.reward,
        feature_config=setup.feature_config,
        n_mission_targets=n_targets,
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
    else:
        rng = np.random.default_rng(derive_seed(EXPERIMENT_SEED, "smoke_train", 0))
        setup.runner.run_serial(
            setup.agent,
            mode="train",
            feature_config=setup.feature_config,
            observation_layout=setup.observation_layout,
            episode_idx=0,
            collect_states=False,
            train_updates_per_step=1,
            early_stop_on_budget_exhausted=False,
            show_simulation_info=False,
            np_rng=rng,
        )

    write_hypothesis_result(
        SMOKE_JSON,
        experiment_id=EXPERIMENT_ID,
        arm_id=ARM_WASTE_OFF,
        reward_flags={
            "enable_shutter_waste_penalty": False,
            "enable_budget_exhausted_shutter_penalty": True,
        },
        run_dir=str(setup.run_dir),
        allow_cpu=allow_cpu,
        tensorboard=enable_tensorboard,
        passed=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=EXPERIMENT_ID)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--train-episodes", type=int, default=50)
    parser.add_argument("--trim-artifacts", action="store_true")
    parser.add_argument("--no-tensorboard", action="store_true")
    args = parser.parse_args()
    enable_tb = not args.no_tensorboard

    if args.smoke:
        run_smoke(allow_cpu=args.allow_cpu, enable_tensorboard=False)
        print(f"Smoke OK → {SMOKE_JSON}")
        return

    write_fixed_split_dt_profile(train_episodes=int(args.train_episodes))
    try:
        kpis = run_waste_off_budget_on(
            show_progress=args.show_progress,
            trim_artifacts=args.trim_artifacts,
            train_episodes=int(args.train_episodes),
            enable_tensorboard=enable_tb,
        )
    except Exception as exc:
        err_path = RESULTS_DIR / "waste_off_error.json"
        write_hypothesis_result(
            err_path,
            experiment_id=EXPERIMENT_ID,
            arm_id=ARM_WASTE_OFF,
            error=str(exc),
            traceback=traceback.format_exc(),
            verdict="error",
        )
        append_log(f"ERROR {ARM_WASTE_OFF}: {exc}")
        raise

    signal = kpis["learning_signal"]
    summary = {
        "experiment_id": EXPERIMENT_ID,
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "dt_profile": json.loads((RESULTS_DIR / "dt_profile.json").read_text(encoding="utf-8")),
        "arms": {
            ARM_WASTE_OFF: {
                "verdict": "pending",
                "learning_mode": signal["learning_mode"],
                "eval_return_mean": kpis["eval_return_mean"],
                "reward_flags": kpis["reward_flags"],
                "post_budget_shutter_cmds_total": kpis["post_budget_shutter_cmds"]["total"],
                "tensorboard_dir": kpis.get("tensorboard_dir"),
                "wall_s": kpis["wall_s"],
                "run_dir": kpis["run_dir"],
            }
        },
        "baseline_exp7": baseline_exp7_metadata(),
        "note": "Compare waste_off_budget_on to Exp 7 penalty_on (both penalties on).",
    }
    write_hypothesis_result(SUMMARY_JSON, **summary)
    print(f"Wrote {SUMMARY_JSON}")
    print(
        f"  {ARM_WASTE_OFF}: learning_mode={signal['learning_mode']} "
        f"eval_mean={kpis['eval_return_mean']} flags={kpis['reward_flags']}"
    )


if __name__ == "__main__":
    main()
