"""Exp 4: agent-reference pointing — Ref0 torque vs Ref1 vector SAC sparse."""

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
_ref_sim = _load_local_module("_sim_constants_fork")
FIXED_REFERENCE_DT = _ref_sim.FIXED_REFERENCE_DT
apply_dt_profile = _ref_sim.apply_dt_profile
apply_experiment_dt_profile = _ref_sim.apply_experiment_dt_profile
require_dt_profile = _ref_sim.require_dt_profile
write_fixed_reference_dt_profile = _ref_sim.write_fixed_reference_dt_profile
for _local_name in (
    "_reward_fork",
    "_warmup_fingerprint_patch",
    "_run_guard",
    "_runner_common",
    "_reference_frozen",
    "_reference_runner",
):
    _load_local_module(_local_name)

from _reference_frozen import EXPERIMENT_SEED, frozen_training_config, sac_mpo_config_overrides
from _reference_runner import (
    ReferenceArmSpec,
    append_log,
    default_arms,
    run_reference_arm,
    verdict_for_reference,
)

if str(OVERNIGHT_ROOT) not in sys.path:
    sys.path.insert(0, str(OVERNIGHT_ROOT))

import _cpu_budget  # noqa: F401

import numpy as np
import torch

from _reward_fork import activate_reward_fork
from _runner_common import RESULTS_DIR, write_hypothesis_result
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra

from autonomous_control.config.randomness import derive_seed
from s01_utils import training_workflow as tw

SUMMARY_JSON = RESULTS_DIR / "agent_reference.json"
ANALYSIS_MD = EXPERIMENT_ROOT / "agent_reference_analysis.md"
SMOKE_JSON = RESULTS_DIR / "smoke.json"


def _load_sac_agent():
    import importlib.util

    _sac_spec = importlib.util.spec_from_file_location(
        "ml_ref_smoke_sac_fork",
        OVERNIGHT_ROOT / "agents" / "sac_agent_fork.py",
    )
    assert _sac_spec and _sac_spec.loader
    _sac_mod = importlib.util.module_from_spec(_sac_spec)
    _sac_spec.loader.exec_module(_sac_mod)
    return _sac_mod.SACAgent


def _verify_run_config(run_dir: Path, *, attitude_request_mode: str) -> dict:
    config_path = run_dir / "config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Smoke missing config.json at {config_path}")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    exp = payload.get("experiment") or {}
    if exp.get("experiment_id") != "ml_agent_reference_pointing":
        raise RuntimeError(f"config experiment_id mismatch: {exp.get('experiment_id')}")
    if exp.get("attitude_request_mode") != attitude_request_mode:
        raise RuntimeError(
            f"config attitude_request_mode expected {attitude_request_mode!r}, "
            f"got {exp.get('attitude_request_mode')!r}"
        )
    return exp


def run_smoke(*, allow_cpu: bool = False) -> dict:
    """Ref0: one warmup episode + one train step; verify run_dir config."""
    write_fixed_reference_dt_profile(train_episodes=1)
    apply_experiment_dt_profile()
    apply_dt_profile(FIXED_REFERENCE_DT)
    require_dt_profile(FIXED_REFERENCE_DT, context="ml_agent_reference_pointing:smoke")

    spec = ReferenceArmSpec(
        arm_id="ref0",
        hypothesis_id="agent_ref_torque_control",
        run_id="ref0_smoke",
        attitude_request_mode="torque",
        agent_kind="sac",
        reward_mode="sparse",
    )
    set_warmup_fingerprint_extra(
        sim_dt_s=FIXED_REFERENCE_DT.sim_dt_s,
        controller_interval_s=FIXED_REFERENCE_DT.controller_interval_s,
        reward_mode="sparse",
        reference_arm="smoke",
        attitude_request_mode="torque",
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("sparse", attitude_request_mode="torque")

    if not torch.cuda.is_available() and not allow_cpu:
        raise RuntimeError("CUDA required for smoke; pass --allow-cpu for debug.")

    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = replace(
        frozen_training_config(
            run_id=f"ml_ref_smoke_{stamp}",
            train_episodes=0,
            rebuild_warmup_bundle_cache=True,
            experiment_name="agent reference smoke",
            attitude_request_mode="torque",
        ),
        warmup_episodes=1,
        eval_episodes=0,
        use_warmup_bundle_cache=False,
        background_artifacts=False,
    )
    setup = tw.build_training_workflow_setup(cfg)
    setup = replace(setup, mpo_config=sac_mpo_config_overrides(setup.mpo_config))

    from _reference_runner import _patch_run_config

    _patch_run_config(
        setup.run_dir,
        spec=spec,
        dt_profile={
            "sim_dt_s": FIXED_REFERENCE_DT.sim_dt_s,
            "controller_interval_s": FIXED_REFERENCE_DT.controller_interval_s,
            "label": FIXED_REFERENCE_DT.label,
        },
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

    warmup = setup.runner.run_serial(
        setup.agent,
        mode="warmup",
        episode_idx=0,
        collect_states=False,
        show_training_context=False,
        train_updates_per_step=0,
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "ref_smoke", 0)),
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
        np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "ref_smoke_train", 0)),
    )
    setup.agent.train()

    exp_block = _verify_run_config(setup.run_dir, attitude_request_mode="torque")
    payload = {
        "passed": True,
        "arm_id": "ref0",
        "attitude_request_mode": "torque",
        "warmup_return": float(warmup.episode_return),
        "warmup_steps": int(warmup.steps),
        "train_return": float(train_ep.episode_return),
        "train_steps": int(train_ep.steps),
        "buffer_size": len(setup.agent.buffer),
        "run_dir": str(setup.run_dir),
        "config_experiment": exp_block,
    }
    write_hypothesis_result(
        SMOKE_JSON,
        phase="smoke",
        experiment_id="ml_agent_reference_pointing",
        **payload,
    )
    append_log(f"SMOKE OK warmup_return={payload['warmup_return']:.1f}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="ml_agent_reference_pointing — Exp 4")
    parser.add_argument("--smoke", action="store_true", help="Quick smoke test (Ref0 only)")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--arms", default="ref0,ref1", help="Comma-separated arm ids")
    parser.add_argument("--include-ref2", action="store_true", help="Include optional MPO Ref2 arm")
    parser.add_argument("--train-episodes", type=int, default=50)
    parser.add_argument(
        "--trim-artifacts",
        action="store_true",
        help="Skip train MP4s and export only top eval video (faster; opt-in).",
    )
    args = parser.parse_args()

    if args.smoke:
        run_smoke(allow_cpu=args.allow_cpu)
        print(f"Smoke OK → {SMOKE_JSON}")
        return

    write_fixed_reference_dt_profile(train_episodes=int(args.train_episodes))
    arm_map = {a.arm_id: a for a in default_arms(include_ref2=args.include_ref2)}
    selected = [arm_map[x.strip()] for x in args.arms.split(",") if x.strip() in arm_map]
    if not selected:
        raise SystemExit(f"No valid arms in {args.arms!r}; choose from {list(arm_map)}")

    results: dict[str, dict] = {}
    for spec in selected:
        try:
            kpis = run_reference_arm(
                spec,
                show_progress=args.show_progress,
                trim_artifacts=args.trim_artifacts,
                train_episodes=int(args.train_episodes),
            )
            results[spec.arm_id] = kpis
        except Exception as exc:
            err_path = RESULTS_DIR / f"{spec.arm_id}_error.json"
            write_hypothesis_result(
                err_path,
                experiment_id="ml_agent_reference_pointing",
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
        arm_summaries[arm_id] = {
            "verdict": verdict_for_reference(kpis),
            "attitude_request_mode": kpis["attitude_request_mode"],
            "learning_mode": signal["learning_mode"],
            "eval_return_mean": kpis["eval_return_mean"],
            "reference_clamp_count": kpis.get("reference_clamp_count"),
            "wall_s": kpis["wall_s"],
        }

    summary = {
        "experiment_id": "ml_agent_reference_pointing",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "dt_profile": json.loads((RESULTS_DIR / "dt_profile.json").read_text(encoding="utf-8")),
        "arms": arm_summaries,
    }
    write_hypothesis_result(SUMMARY_JSON, **summary)
    print(f"Wrote {SUMMARY_JSON}")
    for arm_id, s in arm_summaries.items():
        print(
            f"  {arm_id}: verdict={s['verdict']} mode={s['attitude_request_mode']} "
            f"learning_mode={s['learning_mode']}"
        )


if __name__ == "__main__":
    main()
