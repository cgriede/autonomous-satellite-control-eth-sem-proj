"""Exp 2: SAC sparse — flat encoder (A0) vs vector-compress encoder (A1)."""

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

from _encoder_runner import (
    RESULTS_DIR,
    ArmSpec,
    append_log,
    run_sac_arm,
    verdict_for_arm,
    write_analysis_card,
    write_dt_profile,
    write_hypothesis_result,
)
from _encoder_sim import DT_15, apply_dt_profile, apply_experiment_dt_profile, require_dt_profile
from _reward_fork import activate_reward_fork
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra

from _frozen_baseline import EXPERIMENT_SEED, frozen_training_config
from encoder_agents.sac_modular_agent import SACModularAgent
from autonomous_control.config.randomness import derive_seed
from s01_utils import training_workflow as tw

SUMMARY_JSON = RESULTS_DIR / "modular_encoder_summary.json"
ANALYSIS_MD = EXPERIMENT_ROOT / "modular_encoder_analysis.md"
SMOKE_JSON = RESULTS_DIR / "smoke.json"


def _default_arms(vector_embed_dim: int) -> tuple[ArmSpec, ...]:
    return (
        ArmSpec("sac_a0", "flat", "encoder_flat_baseline"),
        ArmSpec("sac_a1", "compress", "encoder_vector_compress", vector_embed_dim=vector_embed_dim),
    )


def run_smoke(*, allow_cpu: bool = False, vector_embed_dim: int = 8) -> dict:
    write_dt_profile(train_episodes=1)
    apply_experiment_dt_profile()
    apply_dt_profile(DT_15)
    require_dt_profile(DT_15, context="ml_modular_encoder:smoke")
    set_warmup_fingerprint_extra(
        sim_dt_s=DT_15.sim_dt_s,
        controller_interval_s=DT_15.controller_interval_s,
        reward_mode="sparse",
        encoder_arm="smoke",
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("sparse")

    if not torch.cuda.is_available() and not allow_cpu:
        raise RuntimeError("CUDA required for smoke; pass --allow-cpu for debug.")

    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = replace(
        frozen_training_config(
            run_id=f"ml_encoder_smoke_{stamp}",
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
    setup = replace(setup, agent=SACModularAgent(env, config=setup.mpo_config, encoder_mode="compress"))

    warmup = setup.runner.run_serial(
        setup.agent,
        mode="warmup",
        episode_idx=0,
        collect_states=False,
        show_training_context=False,
        train_updates_per_step=0,
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "encoder_smoke", 0)),
    )
    if len(setup.agent.buffer) == 0:
        raise RuntimeError("Smoke warmup produced empty buffer.")
    setup.agent.train()

    payload = {
        "passed": True,
        "encoder_mode": "compress",
        "vector_embed_dim": vector_embed_dim,
        "warmup_return": float(warmup.episode_return),
        "warmup_steps": int(warmup.steps),
        "buffer_size": len(setup.agent.buffer),
    }
    write_hypothesis_result(SMOKE_JSON, phase="smoke", experiment_id="ml_modular_encoder", **payload)
    append_log(f"SMOKE OK warmup_return={payload['warmup_return']:.1f}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="ml_modular_encoder experiment")
    parser.add_argument("--smoke", action="store_true", help="Quick smoke test only")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--arms", default="sac_a0,sac_a1", help="Comma-separated arm ids")
    parser.add_argument("--train-episodes", type=int, default=7)
    parser.add_argument("--vector-embed-dim", type=int, default=8)
    parser.add_argument(
        "--trim-artifacts",
        action="store_true",
        help="Skip train MP4s and export only top eval video (faster; opt-in).",
    )
    args = parser.parse_args()

    if args.smoke:
        run_smoke(allow_cpu=args.allow_cpu, vector_embed_dim=int(args.vector_embed_dim))
        print(f"Smoke OK → {SMOKE_JSON}")
        return

    write_dt_profile(train_episodes=int(args.train_episodes))
    arm_map = {a.arm_id: a for a in _default_arms(int(args.vector_embed_dim))}
    selected = [arm_map[x.strip()] for x in args.arms.split(",") if x.strip() in arm_map]
    if not selected:
        raise SystemExit(f"No valid arms in {args.arms!r}; choose from {list(arm_map)}")

    results: dict[str, dict] = {}
    baseline_kpis: dict | None = None
    for spec in selected:
        try:
            kpis = run_sac_arm(spec, show_progress=args.show_progress, trim_artifacts=args.trim_artifacts)
            results[spec.arm_id] = kpis
            if spec.arm_id == "sac_a0":
                baseline_kpis = kpis
        except Exception as exc:
            err_path = RESULTS_DIR / f"{spec.arm_id}_error.json"
            write_hypothesis_result(
                err_path,
                experiment_id="ml_modular_encoder",
                arm_id=spec.arm_id,
                error=str(exc),
                traceback=traceback.format_exc(),
                verdict="error",
            )
            append_log(f"ERROR {spec.arm_id}: {exc}")
            raise

    arm_summaries = {}
    for arm_id, kpis in results.items():
        v = verdict_for_arm(
            kpis,
            baseline=baseline_kpis if arm_id != "sac_a0" else None,
        )
        arm_summaries[arm_id] = {
            "verdict": v,
            "encoder_kind": kpis["encoder_kind"],
            "vector_embed_dim": kpis.get("vector_embed_dim"),
            "learning_mode": kpis["learning_signal"]["learning_mode"],
            "train_returns": kpis["train_returns"],
            "eval_return_mean": kpis["eval_return_mean"],
            "wall_s": kpis["wall_s"],
        }

    summary = {
        "experiment_id": "ml_modular_encoder",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "dt_profile": json.loads((RESULTS_DIR / "dt_profile.json").read_text(encoding="utf-8")),
        "vector_embed_dim": int(args.vector_embed_dim),
        "arms": arm_summaries,
    }
    write_hypothesis_result(SUMMARY_JSON, **summary)
    write_analysis_card(
        ANALYSIS_MD,
        hypothesis_id="modular_encoder_sac",
        json_path=SUMMARY_JSON,
        sections={
            "Hypothesis": "Vector compressors on bearing/mask (A1) beat flat concat (A0) for SAC sparse.",
            "Arms": json.dumps(arm_summaries, indent=2),
            "Verdict": json.dumps({k: v["verdict"] for k, v in arm_summaries.items()}),
        },
    )
    print(f"Wrote {SUMMARY_JSON}")
    for arm_id, s in arm_summaries.items():
        print(f"  {arm_id}: verdict={s['verdict']} learning_mode={s['learning_mode']}")


if __name__ == "__main__":
    main()
