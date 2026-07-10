"""Exp 15 — per-episode seed diversity + paired baseline."""

from __future__ import annotations

import argparse
import sys
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

from _env_setup_fork import (  # noqa: E402
    build_exp15_episode_setup,
    build_exp15_warmup_setup,
    episode_seeds,
)
from _episode_loop_fork import run_exp14_episode  # noqa: E402
from _episode_seed_runner import DEFAULT_TRAIN_EP, DEFAULT_WARMUP_EP, run_full  # noqa: E402
from _eval_harness import run_eval_comparison  # noqa: E402
from _exp14_reward_fork import activate_reward_fork  # noqa: E402
from _exp14_runner_common import EXPERIMENT_ID, RESULTS_DIR, append_log, write_hypothesis_result  # noqa: E402
from _exp14_sim_constants import (  # noqa: E402
    DT_15,
    apply_dt_profile,
    apply_experiment_dt_profile,
    require_dt_profile,
    write_dt_profile,
)
from _paired_baseline import run_baseline_score_on_setup  # noqa: E402
from _training_setup import build_training_context  # noqa: E402
from _verify_conversions import run_verify_checks  # noqa: E402
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra  # noqa: E402

SMOKE_JSON = RESULTS_DIR / "smoke.json"


def run_check_mutex() -> dict:
    experiments_dir = EXPERIMENT_ROOT.parent
    if str(experiments_dir) not in sys.path:
        sys.path.insert(0, str(experiments_dir))
    from pipeline_run_guard import check_pipeline_run_clear, read_active_run  # noqa: E402

    check_pipeline_run_clear(slug=EXPERIMENT_ID)
    active = read_active_run()
    print(f"Mutex clear for slug={EXPERIMENT_ID!r}")
    return {"clear": active is None, "slug": EXPERIMENT_ID, "active": active}


def run_verify() -> dict:
    checks = run_verify_checks()
    payload = {"passed": True, "checks": checks}
    out = RESULTS_DIR / "verify.json"
    write_hypothesis_result(out, experiment_id=EXPERIMENT_ID, **payload)
    print(f"Verify OK → {out}")
    return payload


def run_smoke(*, allow_cpu: bool = False, show_progress: bool = False) -> dict:
    if not torch.cuda.is_available() and not allow_cpu:
        raise RuntimeError("CUDA required for smoke; pass --allow-cpu for debug.")

    run_verify_checks()
    write_dt_profile(train_episodes=2)
    dt_profile = apply_experiment_dt_profile()
    apply_dt_profile(DT_15)
    require_dt_profile(DT_15, context="exp15_smoke")

    set_warmup_fingerprint_extra(
        sim_dt_s=dt_profile.get("sim_dt_s"),
        controller_interval_s=dt_profile.get("controller_interval_s"),
        reward_mode="exp14_sparse",
        experiment_id=EXPERIMENT_ID,
        attitude_request_mode="vector",
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("exp14_sparse")

    warmup_setup = build_exp15_warmup_setup()
    ctx = build_training_context(warmup_setup)
    append_log("SMOKE start")

    run_exp14_episode(
        warmup_setup,
        ctx.agent,
        mode="warmup",
        feature_config=ctx.feature_config,
        observation_layout=ctx.observation_layout,
        reward_config=ctx.reward_config,
        show_progress=show_progress,
    )

    train_rows = []
    seeds_seen: list[tuple[int, int]] = []
    for ep_i in range(2):
        seeds = episode_seeds(ep_i)
        setup = build_exp15_episode_setup(ep_i)
        seeds_seen.append((seeds["mission_seed"], seeds["cloud_seed"]))
        baseline = run_baseline_score_on_setup(setup, show_progress=False)
        result = run_exp14_episode(
            setup,
            ctx.agent,
            mode="train",
            feature_config=ctx.feature_config,
            observation_layout=ctx.observation_layout,
            reward_config=ctx.reward_config,
            episode_idx=ep_i,
            show_progress=show_progress,
        )
        train_rows.append(
            {
                "episode_index": ep_i,
                "mission_seed": seeds["mission_seed"],
                "cloud_seed": seeds["cloud_seed"],
                "baseline_score": baseline["score_ep"],
                "agent_score": float(result.mission_score),
                "delta_score": float(result.mission_score) - float(baseline["score_ep"]),
            }
        )

    distinct = len(set(seeds_seen)) == 2
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "smoke",
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "passed": bool(distinct),
        "distinct_episode_seeds": distinct,
        "seeds_seen": [{"mission": m, "cloud": c} for m, c in seeds_seen],
        "train_rows": train_rows,
        "device": str(ctx.agent.device),
    }
    write_hypothesis_result(SMOKE_JSON, **payload)
    append_log(f"SMOKE done passed={distinct} → {SMOKE_JSON}")
    if not distinct:
        raise RuntimeError("Smoke failed: episode seeds were not distinct")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Exp 15 ml_mpo_episode_seed_diversity")
    parser.add_argument("--check-mutex", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--eval-comparison", action="store_true")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--train-episodes", type=int, default=DEFAULT_TRAIN_EP)
    parser.add_argument("--warmup-episodes", type=int, default=DEFAULT_WARMUP_EP)
    parser.add_argument(
        "--no-pair-baseline-train",
        action="store_true",
        help="Skip baseline on train episodes (eval still paired)",
    )
    parser.add_argument("--arm", default="hp_explore")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.check_mutex:
        run_check_mutex()
        return
    if args.verify:
        run_verify()
        return
    if args.smoke:
        run_smoke(allow_cpu=args.allow_cpu, show_progress=args.show_progress)
        return
    if args.full:
        run_full(
            train_episodes=int(args.train_episodes),
            warmup_episodes=int(args.warmup_episodes),
            pair_baseline_train=not args.no_pair_baseline_train,
            show_progress=args.show_progress,
            arm_id=str(args.arm),
        )
        return
    if args.eval_comparison:
        from _exp14_checkpoints import load_agent_checkpoint, resolve_screen_checkpoint
        from _profile_baseline import SCREEN_ARMS

        arm = next(a for a in SCREEN_ARMS if a.arm_id == args.arm)
        ctx = build_training_context(build_exp15_warmup_setup(), arm=arm)
        ckpt = resolve_screen_checkpoint(arm.arm_id)
        # prefer episode_seed_final
        from _exp14_checkpoints import checkpoint_path

        final = checkpoint_path(arm.arm_id, tag="episode_seed_final")
        path = final if final.is_file() else ckpt
        if path is None or not Path(path).is_file():
            raise FileNotFoundError("No checkpoint; run --full first")
        load_agent_checkpoint(ctx.agent, Path(path))
        run_eval_comparison(ctx, show_progress=args.show_progress)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
