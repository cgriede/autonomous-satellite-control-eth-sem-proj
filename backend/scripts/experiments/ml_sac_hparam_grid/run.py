"""SAC hparam grid: size S/M/L × reward sparse/dense @ raised LRs (flat encoder)."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FORK_ROOT = Path(__file__).resolve().parent
MODULAR_ROOT = FORK_ROOT.parent / "ml_modular_encoder"
COMPARE_ROOT = FORK_ROOT.parent / "ml_sac_mpo_compare"
BACKEND_DIR = FORK_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
OVERNIGHT_ROOT = FORK_ROOT.parent / "ml_algo_overnight"
for path in (BACKEND_DIR, S01_DIR, MODULAR_ROOT, COMPARE_ROOT, OVERNIGHT_ROOT, FORK_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import _cpu_budget  # noqa: F401

from _encoder_sim import write_dt_profile  # noqa: E402
from _profile_baseline import profile  # noqa: E402
from _hparam_runner import (  # noqa: E402
    RESULTS_DIR,
    append_log,
    default_arms,
    run_hparam_arm,
    write_hypothesis_result,
)

SUMMARY_JSON = RESULTS_DIR / "sac_hparam_grid_summary.json"


def _default_train_episodes() -> int:
    return int((profile().get("workflow") or {}).get("train_episodes", 50))


def main() -> None:
    parser = argparse.ArgumentParser(description="SAC hparam grid (size × reward)")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--train-episodes", type=int, default=None)
    parser.add_argument(
        "--arms",
        default="all",
        help="Comma-separated arm ids or 'all' (default: all 6 arms)",
    )
    parser.add_argument(
        "--trim-artifacts",
        action="store_true",
        help="Skip train MP4s and export only top eval video (faster; opt-in).",
    )
    args = parser.parse_args()

    train_episodes = int(args.train_episodes if args.train_episodes is not None else _default_train_episodes())
    write_dt_profile(train_episodes=train_episodes)
    append_log(f"GRID start train_episodes={train_episodes} ref={profile().get('ref_run_id')}")

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
            kpis = run_hparam_arm(
                spec,
                show_progress=args.show_progress,
                trim_artifacts=args.trim_artifacts,
            )
            results[spec.arm_id] = kpis
        except Exception as exc:
            err_path = RESULTS_DIR / f"{spec.arm_id}_error.json"
            write_hypothesis_result(
                err_path,
                experiment_id="ml_sac_hparam_grid",
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
            "wall_s": kpis["wall_s"],
        }

    summary = {
        "experiment_id": "ml_sac_hparam_grid",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "ref_run_id": profile().get("ref_run_id"),
        "train_episodes": train_episodes,
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
