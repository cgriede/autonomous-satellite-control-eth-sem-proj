"""Exp 14 — multi-env MPO target selection + mission score."""

from __future__ import annotations

import argparse
import json
import math
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"


def _ensure_paths() -> None:
    experiment = str(EXPERIMENT_ROOT)
    while experiment in sys.path:
        sys.path.remove(experiment)
    sys.path.insert(0, experiment)
    for path in (BACKEND_DIR, S01_DIR):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


_ensure_paths()

import _cpu_budget  # noqa: F401

import torch  # noqa: E402

from _env_setup_fork import build_exp14_env_setup_fixed  # noqa: E402
from _episode_loop_fork import run_exp14_episode  # noqa: E402
from _eval_harness import run_baseline_eval, run_eval_comparison  # noqa: E402
from _multienv_runner import run_stage_b  # noqa: E402
from _profile_baseline import SCREEN_TRAIN_EP, SCREEN_WARMUP_EP, profile, screen_env_seeds  # noqa: E402
from _exp14_artifacts import artifact_root, export_warmup_artifacts
from _exp14_reward_fork import activate_reward_fork, reward_mode_contract  # noqa: E402
from _exp14_runner_common import EXPERIMENT_ID, RESULTS_DIR, append_log, write_hypothesis_result  # noqa: E402
from _training_setup import build_training_context  # noqa: E402
from _screen_runner import default_arms, run_screen  # noqa: E402
from _exp14_sim_constants import (  # noqa: E402
    DT_15,
    apply_dt_profile,
    apply_experiment_dt_profile,
    require_dt_profile,
    write_dt_profile,
)
from _exp14_progress import make_progress_display, print_environment_banner, run_phase_episodes  # noqa: E402
from _verify_conversions import run_verify_checks  # noqa: E402
from _warmup_baseline_quality import assess_warmup_baseline_quality, require_warmup_baseline_quality  # noqa: E402
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra  # noqa: E402

SMOKE_JSON = RESULTS_DIR / "smoke.json"


def run_check_mutex() -> dict:
    """Fail if another pipeline training job holds the global lock."""
    experiments_dir = EXPERIMENT_ROOT.parent
    if str(experiments_dir) not in sys.path:
        sys.path.insert(0, str(experiments_dir))
    from pipeline_run_guard import check_pipeline_run_clear, read_active_run  # noqa: E402

    check_pipeline_run_clear(slug=EXPERIMENT_ID)
    active = read_active_run()
    payload = {
        "clear": active is None,
        "slug": EXPERIMENT_ID,
        "active": active,
    }
    print(f"Mutex clear for slug={EXPERIMENT_ID!r}")
    return payload


def run_verify() -> dict:
    checks = run_verify_checks()
    payload = {"passed": True, "checks": checks}
    out = RESULTS_DIR / "verify.json"
    write_hypothesis_result(out, experiment_id=EXPERIMENT_ID, **payload)
    print(f"Verify OK → {out}")
    return payload


def run_smoke(*, allow_cpu: bool = False) -> dict:
    if not torch.cuda.is_available() and not allow_cpu:
        raise RuntimeError("CUDA required for smoke; pass --allow-cpu for debug.")

    run_verify_checks()
    write_dt_profile(train_episodes=2)
    dt_profile = apply_experiment_dt_profile()
    apply_dt_profile(DT_15)
    require_dt_profile(DT_15, context="exp14_smoke")

    set_warmup_fingerprint_extra(
        sim_dt_s=dt_profile.get("sim_dt_s"),
        controller_interval_s=dt_profile.get("controller_interval_s"),
        reward_mode="exp14_sparse",
        experiment_id=EXPERIMENT_ID,
        attitude_request_mode="vector",
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("exp14_sparse")

    setup = build_exp14_env_setup_fixed(mission_seed=0, cloud_seed=0)
    ctx = build_training_context(setup)
    append_log("SMOKE start")

    warmup = run_exp14_episode(
        setup,
        ctx.agent,
        mode="warmup",
        feature_config=ctx.feature_config,
        observation_layout=ctx.observation_layout,
        episode_idx=0,
        reward_config=ctx.reward_config,
    )
    train_results = []
    for ep in range(2):
        train_results.append(
            run_exp14_episode(
                setup,
                ctx.agent,
                mode="train",
                feature_config=ctx.feature_config,
                observation_layout=ctx.observation_layout,
                episode_idx=ep,
                reward_config=ctx.reward_config,
            )
        )

    if len(ctx.agent.buffer) == 0:
        raise RuntimeError("Smoke produced empty replay buffer.")
    train_metrics = ctx.agent.train()
    if train_metrics is None:
        raise RuntimeError("Smoke train() returned None (buffer too small).")
    for key in ("kl", "alpha_mu", "alpha_sigma", "eta"):
        val = float(train_metrics.get(key, float("nan")))
        if not math.isfinite(val):
            raise RuntimeError(f"Smoke train_metrics[{key!r}] not finite: {val}")

    eval_result = run_exp14_episode(
        setup,
        ctx.agent,
        mode="eval",
        feature_config=ctx.feature_config,
        observation_layout=ctx.observation_layout,
        reward_config=ctx.reward_config,
    )

    payload = {
        "passed": True,
        "experiment_id": EXPERIMENT_ID,
        "reward_mode_contract": reward_mode_contract("exp14_sparse"),
        "warmup_return": float(warmup.episode_return),
        "warmup_mission_score": float(warmup.mission_score),
        "train_returns": [float(r.episode_return) for r in train_results],
        "train_mission_scores": [float(r.mission_score) for r in train_results],
        "eval_return": float(eval_result.episode_return),
        "score_ep": float(eval_result.mission_score),
        "buffer_size": len(ctx.agent.buffer),
        "train_metrics": train_metrics,
    }
    write_hypothesis_result(SMOKE_JSON, phase="smoke", **payload)
    append_log(f"SMOKE OK score_ep={payload['score_ep']:.4f}")
    return payload


def run_export_warmup_preview(
    *,
    arm_id: str | None = None,
    warmup_episodes: int = 1,
    reward_plot_only: bool = False,
    show_progress: bool = False,
) -> dict:
    """Run warmup on screen-fixed env and export video + latent/applied reward plot.

    Does not acquire the pipeline mutex — safe to run while ``--screen`` is active.
    """
    write_dt_profile(train_episodes=1)
    dt_profile = apply_experiment_dt_profile()
    apply_dt_profile(DT_15)
    require_dt_profile(DT_15, context="exp14_warmup_preview")

    arm_map = {a.arm_id: a for a in default_arms()}
    arm = arm_map.get(arm_id or "hp_default", default_arms()[0])

    set_warmup_fingerprint_extra(
        sim_dt_s=dt_profile.get("sim_dt_s"),
        controller_interval_s=dt_profile.get("controller_interval_s"),
        reward_mode=arm.reward_mode,
        hparam_arm=arm.arm_id,
        attitude_request_mode="vector",
        experiment_id=EXPERIMENT_ID,
    )
    activate_warmup_fingerprint_patch()

    setup = build_exp14_env_setup_fixed()
    ctx = build_training_context(setup, arm=arm)
    mission_seed, cloud_seed = screen_env_seeds()
    progress_display = make_progress_display(ctx.agent, show_progress=show_progress)
    print_environment_banner(
        env_index=None,
        mission_seed=mission_seed,
        cloud_seed=cloud_seed,
        label="ENV warmup-preview",
    )
    append_log(f"WARMUP PREVIEW arm={arm.arm_id} episodes={warmup_episodes}")

    warmup_results = run_phase_episodes(
        setup,
        ctx,
        mode="warmup",
        episode_count=int(warmup_episodes),
        progress_display=progress_display,
        show_progress=show_progress,
        phase_bar_desc=f"Warmup preview [{arm.arm_id}]",
        experiment_name=f"{EXPERIMENT_ID}:warmup_preview",
    )

    warmup_quality = assess_warmup_baseline_quality(warmup_results)
    require_warmup_baseline_quality(warmup_results, context="warmup_preview")

    out_dir = artifact_root(label="warmup_preview")
    export_payload = export_warmup_artifacts(
        warmup_results,
        out_dir,
        warmup_videos=0 if reward_plot_only else 1,
        export_reward_plots=True,
        show_progress=show_progress,
    )

    payload = {
        "experiment_id": EXPERIMENT_ID,
        "arm_id": arm.arm_id,
        "reward_mode": arm.reward_mode,
        "reward_mode_contract": reward_mode_contract(arm.reward_mode),
        "warmup_episodes": int(warmup_episodes),
        "warmup_returns": [float(r.episode_return) for r in warmup_results],
        "warmup_mission_scores": [float(r.mission_score) for r in warmup_results],
        "warmup_quality": warmup_quality,
        "out_dir": str(out_dir),
        **export_payload,
    }
    out_json = RESULTS_DIR / "warmup_preview.json"
    write_hypothesis_result(out_json, phase="warmup_preview", **payload)
    for item in export_payload.get("artifacts", []):
        print(f"  {item.get('kind')}: {item.get('path')}")
    if export_payload.get("errors"):
        print("errors:")
        for err in export_payload["errors"]:
            print(f"  - {err}")
    append_log(f"WARMUP PREVIEW done → {out_dir}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Exp 14 ml_mpo_multienv_target_select")
    parser.add_argument("--verify", action="store_true", help="Run conversion checks A–G")
    parser.add_argument(
        "--check-mutex",
        action="store_true",
        help="Fail if another pipeline training job is active (optional preflight)",
    )
    parser.add_argument("--smoke", action="store_true", help="Verify + 1 warmup + 2 train + eval")
    parser.add_argument("--screen", action="store_true", help="Stage A hparam screen")
    parser.add_argument("--full", action="store_true", help="Stage B multi-env full run")
    parser.add_argument(
        "--from-scratch",
        action="store_true",
        help="Stage B: do not load screen winner checkpoint (default: resume)",
    )
    parser.add_argument("--eval-baseline", action="store_true", help="Baseline 5-seed eval only")
    parser.add_argument("--eval-comparison", action="store_true", help="Baseline + treatment eval")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument(
        "--arms",
        default="all",
        help="Comma-separated screen arm ids or 'all'",
    )
    parser.add_argument("--arm", default=None, help="Stage B hparam arm override")
    parser.add_argument("--trim-artifacts", action="store_true", help="Skip MP4/reward plot export during screen")
    parser.add_argument(
        "--export-artifacts",
        action="store_true",
        help="Export warmup/train/eval videos and latent/applied reward plots during screen",
    )
    parser.add_argument(
        "--export-warmup-preview",
        action="store_true",
        help="Run warmup only and export video + reward plot (no pipeline lock; parallel-safe)",
    )
    parser.add_argument(
        "--reward-plot-only",
        action="store_true",
        help="With --export-warmup-preview: skip slow MP4 encode",
    )
    parser.add_argument(
        "--warmup-episodes",
        type=int,
        default=1,
        help="Episode count for --export-warmup-preview (default 1)",
    )
    args = parser.parse_args()

    if args.verify:
        run_verify()
        return

    if args.check_mutex:
        run_check_mutex()
        return

    if args.smoke:
        payload = run_smoke(allow_cpu=args.allow_cpu)
        print(f"Smoke OK → {SMOKE_JSON}")
        print(f"  score_ep={payload['score_ep']:.4f}")
        return

    if args.export_warmup_preview:
        payload = run_export_warmup_preview(
            arm_id=args.arm,
            warmup_episodes=int(args.warmup_episodes),
            reward_plot_only=bool(args.reward_plot_only),
            show_progress=args.show_progress,
        )
        print(json.dumps(payload, indent=2, default=str))
        return

    if args.screen:
        arm_map = {a.arm_id: a for a in default_arms()}
        if args.arms.strip().lower() == "all":
            selected = default_arms()
        else:
            selected = tuple(
                arm_map[x.strip()]
                for x in args.arms.split(",")
                if x.strip() in arm_map
            )
        if not selected:
            raise SystemExit(f"No valid arms in {args.arms!r}")
        # Default is trimmed screen artifacts; allow explicit trim/export flags.
        trim_artifacts = bool(args.trim_artifacts)
        if not args.trim_artifacts and not args.export_artifacts:
            trim_artifacts = True
        if args.export_artifacts:
            trim_artifacts = False
        summary = run_screen(
            selected,
            show_progress=args.show_progress,
            trim_artifacts=trim_artifacts,
            export_artifacts=args.export_artifacts,
        )
        print(json.dumps(summary, indent=2, default=str))
        return

    if args.full:
        summary = run_stage_b(
            arm_id=args.arm,
            show_progress=args.show_progress,
            resume_from_screen=not args.from_scratch,
        )
        print(json.dumps(summary, indent=2, default=str))
        return

    if args.eval_baseline:
        payload = run_baseline_eval(show_progress=args.show_progress)
        print(json.dumps(payload, indent=2, default=str))
        return

    if args.eval_comparison:
        setup = build_exp14_env_setup_fixed()
        ctx = build_training_context(setup)
        payload = run_eval_comparison(ctx, show_progress=args.show_progress)
        print(json.dumps(payload, indent=2, default=str))
        return

    parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        err_path = RESULTS_DIR / "run_error.json"
        write_hypothesis_result(
            err_path,
            experiment_id=EXPERIMENT_ID,
            error=str(exc),
            traceback=traceback.format_exc(),
            verdict="error",
        )
        append_log(f"ERROR: {exc}")
        raise


__all__ = ["main", "run_smoke", "run_verify"]
