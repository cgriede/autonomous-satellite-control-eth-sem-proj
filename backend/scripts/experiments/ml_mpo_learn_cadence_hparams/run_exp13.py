"""Exp 13: MPO learn cadence + untouched hyperparams @ dt 1.5s."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"


def _ensure_experiment_root_first() -> None:
    experiment = str(EXPERIMENT_ROOT)
    while experiment in sys.path:
        sys.path.remove(experiment)
    sys.path.insert(0, experiment)


for path in (BACKEND_DIR, S01_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
_ensure_experiment_root_first()

import _cpu_budget  # noqa: F401

import torch  # noqa: E402

from _cadence_profiles import cadence_arm_by_id, default_cadence_arms  # noqa: E402
from _hparam_profiles import hparam_arm_by_id  # noqa: E402
from _runner import (  # noqa: E402
    EXPERIMENT_ID,
    RESULTS_DIR,
    append_log,
    run_cadence_arm,
    run_timing_episode,
    write_hypothesis_result,
)

SUMMARY_JSON = RESULTS_DIR / "learn_cadence_hparams_summary.json"
SMOKE_JSON = RESULTS_DIR / "smoke.json"
TIMING_JSON = RESULTS_DIR / "timing_a0.json"


def run_smoke(*, allow_cpu: bool = False) -> dict:
    if not torch.cuda.is_available() and not allow_cpu:
        raise RuntimeError("CUDA required for smoke; pass --allow-cpu for debug.")

    arms = [cadence_arm_by_id("baseline_1_1_1"), cadence_arm_by_id("cadence_1_1_10")]
    results: list[dict] = []
    for cadence in arms:
        payload = run_cadence_arm(cadence, smoke=True)
        results.append(payload)
        append_log(
            f"SMOKE {cadence.arm_id} n_train_updates={payload['n_train_updates']} "
            f"steps={payload['train_steps']}"
        )

    out = {
        "experiment_id": EXPERIMENT_ID,
        "passed": True,
        "arms": results,
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_hypothesis_result(SMOKE_JSON, phase="smoke", **out)
    return out


def run_timing_a0(*, arms: list[str] | None = None) -> dict:
    selected = default_cadence_arms()
    if arms:
        selected = tuple(cadence_arm_by_id(a) for a in arms)

    rows: list[dict] = []
    for idx, cadence in enumerate(selected):
        report = run_timing_episode(
            cadence,
            rebuild_warmup_cache=idx == 0,
        )
        rows.append(report)
        print(
            f"{cadence.arm_id}: wall={report['episode_wall_s']:.2f}s "
            f"steps/s={report.get('steps_per_s', 0):.2f} "
            f"trains={report['n_train_updates']}"
        )

    payload = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "A0",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "variants": rows,
    }
    write_hypothesis_result(TIMING_JSON, **payload)
    md_path = RESULTS_DIR / "timing_a0.md"
    lines = [
        "# Exp 13 Track A0 — learn cadence timing",
        "",
        f"- **Run at:** {payload['run_at_utc']}",
        "",
        "| Arm | ratio | wall (s) | steps/s | train updates | controller (s) | collect | burst |",
        "|-----|-------|----------|---------|---------------|----------------|---------|-------|",
    ]
    baseline_sps = rows[0].get("steps_per_s", 1.0) if rows else 1.0
    for row in rows:
        speedup = row.get("steps_per_s", 0) / baseline_sps if baseline_sps > 0 else 0.0
        cadence = row.get("extra", row)
        lines.append(
            f"| {row.get('arm_id', cadence.get('arm_id', '?'))} | "
            f"{row.get('ratio_label', '?')} | "
            f"{row.get('episode_wall_s', 0):.2f} | "
            f"{row.get('steps_per_s', 0):.2f} ({speedup:.2f}×) | "
            f"{row.get('n_train_updates', 0)} | "
            f"{row.get('controller_interval_s', '?')} | "
            f"{row.get('train_every_n_steps', '?')} | "
            f"{row.get('updates_per_step', '?')} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote {TIMING_JSON.name}, {md_path.name}")
    return payload


def run_overnight(*, show_progress: bool = False, trim_artifacts: bool = True) -> dict:
    """Overnight slot: Track A0 timing + A1 parity (10 train ep, key cadence arms)."""
    append_log("OVERNIGHT start Track A0 + A1 parity")
    a0 = run_timing_a0()

    parity_arms = ("baseline_1_1_1", "cadence_1_1_10", "cadence_1_1_50")
    parity_results: list[dict] = []
    for arm_id in parity_arms:
        cadence = cadence_arm_by_id(arm_id)
        kpis = run_cadence_arm(
            cadence,
            show_progress=show_progress,
            trim_artifacts=trim_artifacts,
            train_episodes=10,
        )
        per_arm_path = RESULTS_DIR / f"overnight_{arm_id}.json"
        write_hypothesis_result(per_arm_path, experiment_id=EXPERIMENT_ID, phase="A1_parity", **kpis)
        parity_results.append(kpis)
        append_log(
            f"OVERNIGHT A1 {arm_id} wall_s={kpis['wall_s']:.1f} "
            f"eval_mean={kpis.get('eval_return_mean', 0):.1f}"
        )

    payload = {
        "experiment_id": EXPERIMENT_ID,
        "phase": "overnight",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "track_a0": a0,
        "track_a1_parity": parity_results,
    }
    overnight_path = RESULTS_DIR / "learn_cadence_overnight.json"
    write_hypothesis_result(overnight_path, **payload)
    write_hypothesis_result(SUMMARY_JSON, **payload)
    append_log(f"OVERNIGHT done → {overnight_path.name}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Exp 13 — MPO learn cadence + hparams")
    parser.add_argument("--smoke", action="store_true", help="Smoke baseline + cadence_1_1_10")
    parser.add_argument("--timing-a0", action="store_true", help="Track A0: one timed train ep per cadence arm")
    parser.add_argument("--arm", action="append", default=[], help="Cadence arm_id (repeatable)")
    parser.add_argument("--hparam-arm", default=None, help="Optional hparam arm_id (Track B)")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--show-progress", action="store_true")
    parser.add_argument("--train-episodes", type=int, default=None)
    parser.add_argument("--trim-artifacts", action="store_true")
    parser.add_argument(
        "--overnight",
        action="store_true",
        help="Track A0 timing + A1 parity (10 train ep on baseline, 1:1:10, 1:1:50)",
    )
    args = parser.parse_args()

    if args.overnight:
        run_overnight(show_progress=args.show_progress, trim_artifacts=True)
        print(f"Overnight track done → {RESULTS_DIR / 'learn_cadence_overnight.json'}")
        return

    if args.smoke:
        out = run_smoke(allow_cpu=args.allow_cpu)
        print(f"Smoke OK → {SMOKE_JSON}")
        for arm in out["arms"]:
            print(
                f"  {arm['arm_id']}: n_train_updates={arm['n_train_updates']} "
                f"run_dir={arm['run_dir']}"
            )
        return

    if args.timing_a0:
        run_timing_a0(arms=args.arm or None)
        return

    arm_ids = args.arm or [a.arm_id for a in default_cadence_arms()]
    hparam = hparam_arm_by_id(args.hparam_arm) if args.hparam_arm else None
    cadence_for_hparam = cadence_arm_by_id("baseline_1_1_1")

    summary_arms: list[dict] = []
    append_log(f"RUN start arms={arm_ids} hparam={args.hparam_arm}")

    for arm_id in arm_ids:
        cadence = cadence_arm_by_id(arm_id)
        if hparam is not None and arm_id != cadence_for_hparam.arm_id:
            print(f"Skipping {arm_id} when --hparam-arm set (use baseline cadence only)")
            continue
        try:
            kpis = run_cadence_arm(
                cadence,
                hparam=hparam,
                show_progress=args.show_progress,
                trim_artifacts=args.trim_artifacts,
                train_episodes=args.train_episodes,
            )
        except Exception as exc:
            err_path = RESULTS_DIR / f"{arm_id}_error.json"
            write_hypothesis_result(
                err_path,
                experiment_id=EXPERIMENT_ID,
                arm_id=arm_id,
                error=str(exc),
                traceback=traceback.format_exc(),
                verdict="error",
            )
            append_log(f"ERROR arm={arm_id}: {exc}")
            raise
        summary_arms.append(kpis)
        per_arm_path = RESULTS_DIR / f"{arm_id}.json"
        write_hypothesis_result(per_arm_path, experiment_id=EXPERIMENT_ID, **kpis)
        print(f"Done {arm_id} wall_s={kpis['wall_s']:.1f} eval_mean={kpis['eval_return_mean']:.1f}")

    summary = {
        "experiment_id": EXPERIMENT_ID,
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "train_episodes": args.train_episodes,
        "hparam_arm": args.hparam_arm,
        "arms": summary_arms,
    }
    write_hypothesis_result(SUMMARY_JSON, **summary)
    print(f"Wrote {SUMMARY_JSON}")


if __name__ == "__main__":
    main()
