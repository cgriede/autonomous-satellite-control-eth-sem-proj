"""Exp 5: MPO model-size width ablation (S/M/L) @ dt 1.5s."""

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
def _ensure_experiment_root_first() -> None:
    experiment = str(EXPERIMENT_ROOT)
    while experiment in sys.path:
        sys.path.remove(experiment)
    sys.path.insert(0, experiment)


for path in (BACKEND_DIR, S01_DIR, OVERNIGHT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
_ensure_experiment_root_first()

import _cpu_budget  # noqa: F401

import numpy as np
import torch

from _mpo_runner import (  # noqa: E402
    RESULTS_DIR,
    append_log,
    default_arms,
    run_mpo_size_arm,
    write_hypothesis_result,
    _sync_run_config_mpo,
    _verify_run_config_widths,
)
from _profile_baseline import EXPERIMENT_SEED, frozen_training_config, profile, size_preset  # noqa: E402
from _reward_fork import RewardForkMode, activate_reward_fork  # noqa: E402
from _sim_constants_fork import (  # noqa: E402
    DT_15,
    apply_dt_profile,
    apply_experiment_dt_profile,
    require_dt_profile,
    write_dt_profile,
)
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra  # noqa: E402

from autonomous_control.config.randomness import derive_seed  # noqa: E402
from autonomous_control.controller_agent import MPOAgent  # noqa: E402
from s01_utils import training_workflow as tw  # noqa: E402

SUMMARY_JSON = RESULTS_DIR / "mpo_model_size_summary.json"
SMOKE_JSON = RESULTS_DIR / "smoke.json"


def _default_train_episodes() -> int:
    return int((profile().get("workflow") or {}).get("train_episodes", 50))


def _parse_reward_mode(raw: str) -> RewardForkMode:
    mode = raw.strip().lower()
    if mode not in ("sparse", "dense"):
        raise SystemExit(f"Invalid --reward-mode {raw!r}; choose sparse or dense")
    return mode  # type: ignore[return-value]


def run_smoke(
    *,
    allow_cpu: bool = False,
    reward_mode: RewardForkMode = "sparse",
    arm_id: str = "mpo_s",
) -> dict:
    arm_map = {a.arm_id: a for a in default_arms()}
    if arm_id not in arm_map:
        raise SystemExit(f"Smoke arm {arm_id!r} not in {list(arm_map)}")
    spec = arm_map[arm_id]
    mpo_overrides = {**profile().get("mpo", {}), **size_preset(spec.size)}

    write_dt_profile(train_episodes=1)
    apply_experiment_dt_profile()
    apply_dt_profile(DT_15)
    require_dt_profile(DT_15, context="ml_mpo_model_size:smoke")
    set_warmup_fingerprint_extra(
        sim_dt_s=DT_15.sim_dt_s,
        controller_interval_s=DT_15.controller_interval_s,
        reward_mode=reward_mode,
        mpo_size_arm=f"smoke_{arm_id}",
        model_size=spec.size,
        **mpo_overrides,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork(reward_mode)

    if not torch.cuda.is_available() and not allow_cpu:
        raise RuntimeError("CUDA required for smoke; pass --allow-cpu for debug.")

    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = replace(
        frozen_training_config(
            run_id=f"ml_mpo_model_size_smoke_{arm_id}_{stamp}",
            train_episodes=0,
            rebuild_warmup_bundle_cache=True,
        ),
        warmup_episodes=1,
        eval_episodes=0,
        use_warmup_bundle_cache=False,
        background_artifacts=False,
    )
    setup = tw.build_training_workflow_setup(cfg)
    mpo_config = replace(setup.mpo_config, **mpo_overrides)
    setup = replace(
        setup,
        agent=MPOAgent(
            tw.make_attitude_control_env(
                secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
                reward_config=mpo_config.reward,
                feature_config=setup.feature_config,
                n_mission_targets=len(
                    setup.mission_setup.resolve(require_camera=True).target_areas or ()
                ),
                observation_layout=setup.observation_layout,
            ),
            config=mpo_config,
        ),
        mpo_config=mpo_config,
    )
    _sync_run_config_mpo(setup)
    config_mpo = _verify_run_config_widths(setup.run_dir, mpo_overrides)

    warmup = setup.runner.run_serial(
        setup.agent,
        mode="warmup",
        episode_idx=0,
        collect_states=False,
        show_training_context=False,
        train_updates_per_step=0,
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "mpo_model_size_smoke", 0)),
    )
    if len(setup.agent.buffer) == 0:
        raise RuntimeError("Smoke warmup produced empty buffer.")
    setup.agent.train()

    activate_reward_fork("dense" if reward_mode == "sparse" else "sparse")

    payload = {
        "passed": True,
        "arm_id": arm_id,
        "size": spec.size,
        "reward_mode": reward_mode,
        "mpo_overrides": mpo_overrides,
        "config_mpo": config_mpo,
        "run_dir": str(setup.run_dir),
        "warmup_return": float(warmup.episode_return),
        "warmup_steps": int(warmup.steps),
        "buffer_size": len(setup.agent.buffer),
        "reward_modes_checked": ["sparse", "dense"],
    }
    write_hypothesis_result(
        SMOKE_JSON,
        phase="smoke",
        experiment_id="ml_mpo_model_size",
        **payload,
    )
    append_log(
        f"SMOKE OK arm={arm_id} warmup_return={payload['warmup_return']:.1f} "
        f"actor={config_mpo.get('num_units_actor')} critic={config_mpo.get('num_units_critic')}"
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="ml_mpo_model_size — Exp 5 MPO width ablation")
    parser.add_argument("--smoke", action="store_true", help="Quick smoke on selected arm(s)")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--train-episodes", type=int, default=None)
    parser.add_argument(
        "--reward-mode",
        default="sparse",
        choices=("sparse", "dense"),
        help="Reward fork for all arms (default sparse; charter default dense pending Exp 3)",
    )
    parser.add_argument(
        "--arms",
        default="all",
        help="Comma-separated arm ids or 'all' (default: mpo_s,mpo_m,mpo_l)",
    )
    parser.add_argument(
        "--trim-artifacts",
        action="store_true",
        help="Skip train MP4s and export only top eval video (faster; opt-in).",
    )
    args = parser.parse_args()

    reward_mode = _parse_reward_mode(args.reward_mode)

    if args.smoke:
        arm_map = {a.arm_id: a for a in default_arms()}
        if args.arms.strip().lower() == "all":
            smoke_arms = ("mpo_s",)
        else:
            smoke_arms = tuple(
                x.strip() for x in args.arms.split(",") if x.strip() in arm_map
            )
        if not smoke_arms:
            raise SystemExit(f"No valid smoke arms in {args.arms!r}; choose from {list(arm_map)}")
        results = {}
        for arm_id in smoke_arms:
            results[arm_id] = run_smoke(
                allow_cpu=args.allow_cpu,
                reward_mode=reward_mode,
                arm_id=arm_id,
            )
        print(f"Smoke OK → {SMOKE_JSON}")
        for arm_id, row in results.items():
            print(
                f"  {arm_id}: actor={row['config_mpo'].get('num_units_actor')} "
                f"critic={row['config_mpo'].get('num_units_critic')} "
                f"warmup_return={row['warmup_return']:.1f}"
            )
        return

    train_episodes = int(
        args.train_episodes if args.train_episodes is not None else _default_train_episodes()
    )
    write_dt_profile(train_episodes=train_episodes)
    append_log(
        f"GRID start train_episodes={train_episodes} reward_mode={reward_mode} "
        f"ref={profile().get('ref_run_id')}"
    )

    arm_map = {a.arm_id: a for a in default_arms()}
    if args.arms.strip().lower() == "all":
        selected = list(default_arms())
    else:
        selected = [arm_map[x.strip()] for x in args.arms.split(",") if x.strip() in arm_map]
    if not selected:
        raise SystemExit(f"No valid arms in {args.arms!r}; choose from {list(arm_map)}")

    results: dict[str, dict] = {}
    for spec in selected:
        try:
            kpis = run_mpo_size_arm(
                spec,
                reward_mode=reward_mode,
                show_progress=args.show_progress,
                trim_artifacts=args.trim_artifacts,
                train_episodes=train_episodes,
            )
            results[spec.arm_id] = kpis
        except Exception as exc:
            err_path = RESULTS_DIR / f"{spec.arm_id}_error.json"
            write_hypothesis_result(
                err_path,
                experiment_id="ml_mpo_model_size",
                arm_id=spec.arm_id,
                error=str(exc),
                traceback=traceback.format_exc(),
                verdict="error",
            )
            append_log(f"ERROR {spec.arm_id}: {exc}")
            raise

    arm_summaries = {}
    for arm_id, kpis in results.items():
        signal = kpis.get("learning_signal") or {}
        arm_summaries[arm_id] = {
            "size": kpis["size"],
            "reward_mode": kpis["reward_mode"],
            "learning_mode": signal.get("learning_mode"),
            "train_return_best": max(kpis["train_returns"]) if kpis["train_returns"] else None,
            "eval_return_mean": kpis["eval_return_mean"],
            "num_units_actor": kpis["mpo_overrides"]["num_units_actor"],
            "num_units_critic": kpis["mpo_overrides"]["num_units_critic"],
            "wall_s": kpis["wall_s"],
        }

    summary = {
        "experiment_id": "ml_mpo_model_size",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "ref_run_id": profile().get("ref_run_id"),
        "train_episodes": train_episodes,
        "reward_mode": reward_mode,
        "shared_mpo": profile().get("mpo"),
        "arms": arm_summaries,
    }
    write_hypothesis_result(SUMMARY_JSON, **summary)
    print(f"Wrote {SUMMARY_JSON}")
    for arm_id, row in arm_summaries.items():
        print(
            f"  {arm_id}: learning_mode={row['learning_mode']} "
            f"train_best={row['train_return_best']:.1f} eval_mean={row['eval_return_mean']:.1f}"
        )


if __name__ == "__main__":
    main()
