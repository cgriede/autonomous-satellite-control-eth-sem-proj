"""Sequential overnight pipeline batch: Exp 10 → 11 → 12 → 13 (global mutex per arm)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPERIMENTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENTS_ROOT.parents[2]
RUNS_DIR = REPO_ROOT / "backend" / "autonomous_control" / "runs"
RESULTS_DIR = EXPERIMENTS_ROOT / "results"
BATCH_LOG = RESULTS_DIR / "pipeline_overnight_batch.log"
BATCH_SUMMARY = RESULTS_DIR / "pipeline_overnight_batch.json"


@dataclass(frozen=True)
class BatchStep:
    slug: str
    script: str
    label: str
    extra_args: tuple[str, ...] = ()
    preflight: Callable[[Path], str | None] | None = None  # None = ready; str = skip reason


def _exp13_ready(exp_dir: Path) -> str | None:
    smoke = exp_dir / "results" / "smoke.json"
    if smoke.is_file():
        return None
    return f"smoke missing ({smoke.relative_to(REPO_ROOT)}) — other agent still building"


OVERNIGHT_QUEUE: tuple[BatchStep, ...] = (
    BatchStep("ml_mpo_safe_mode_penalty", "run_mpo_safe_mode_penalty.py", "Exp 10"),
    BatchStep("ml_mpo_decoupled_dual_vector", "run_mpo_vector.py", "Exp 11"),
    BatchStep("ml_mpo_vector_torque_effort", "run_mpo_vector_torque_effort.py", "Exp 12"),
    BatchStep(
        "ml_mpo_learn_cadence_hparams",
        "run_exp13.py",
        "Exp 13",
        extra_args=("--overnight",),
        preflight=_exp13_ready,
    ),
)


def _append_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with BATCH_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")
    print(line)


def _git_sync_runs(*, slug: str, label: str) -> dict[str, Any]:
    from _git_sync_runs import sync_runs_git  # noqa: E402

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    msg = f"chore(runs): sync after {label} ({slug}) [{stamp}]"
    _append_log(f"GIT sync runs after {label}")
    result = sync_runs_git(message=msg, push=True)
    _append_log(f"GIT result {label}: {result.get('status')} {result.get('reason', result.get('push_error', ''))}")
    return result


def _run_arm(step: BatchStep, *, extra_args: list[str], smoke_only: bool) -> dict[str, Any]:
    exp_dir = EXPERIMENTS_ROOT / step.slug
    arm_extra = () if smoke_only else step.extra_args
    cmd = [sys.executable, step.script, *arm_extra, *extra_args]
    _append_log(f"START {step.label} ({step.slug}) → {' '.join(cmd)}")
    t0 = datetime.now(timezone.utc)
    proc = subprocess.run(cmd, cwd=exp_dir, check=False)
    elapsed_s = (datetime.now(timezone.utc) - t0).total_seconds()
    status = "ok" if proc.returncode == 0 else "error"
    _append_log(f"DONE {step.label} exit={proc.returncode} elapsed_s={elapsed_s:.0f}")
    return {
        "slug": step.slug,
        "label": step.label,
        "script": step.script,
        "exit_code": proc.returncode,
        "elapsed_s": elapsed_s,
        "status": status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run pipeline experiments 10→13 sequentially (one mutex slot at a time)."
    )
    parser.add_argument("--smoke-only", action="store_true", help="Run --smoke --allow-cpu on each slug")
    parser.add_argument("--from-slug", default=None, help="Start at this slug (skip earlier queue items)")
    parser.add_argument("--show-progress", action="store_true", help="Pass --show-progress to full runs")
    parser.add_argument("--continue-on-error", action="store_true", help="Run remaining slugs even if one fails")
    parser.add_argument(
        "--skip-not-ready",
        action="store_true",
        help="Skip slugs failing preflight (e.g. Exp 13 without smoke.json)",
    )
    parser.add_argument(
        "--git-sync-runs",
        action="store_true",
        help="After each successful arm, commit+push backend/autonomous_control/runs/",
    )
    args = parser.parse_args()

    if str(EXPERIMENTS_ROOT) not in sys.path:
        sys.path.insert(0, str(EXPERIMENTS_ROOT))
    from pipeline_run_guard import check_pipeline_run_clear, read_active_run  # noqa: E402

    try:
        check_pipeline_run_clear(slug="pipeline_overnight_batch")
    except RuntimeError as exc:
        active = read_active_run()
        raise SystemExit(f"Pipeline blocked: {exc}\nActive: {active}") from exc

    queue = list(OVERNIGHT_QUEUE)
    if args.from_slug:
        slugs = [q.slug for q in queue]
        if args.from_slug not in slugs:
            raise SystemExit(f"Unknown slug {args.from_slug!r}; choose from {slugs}")
        queue = queue[slugs.index(args.from_slug) :]

    extra: list[str] = ["--smoke", "--allow-cpu"] if args.smoke_only else []
    if args.show_progress and not args.smoke_only:
        extra.append("--show-progress")

    _append_log(
        f"BATCH start smoke_only={args.smoke_only} from={args.from_slug or 'head'} "
        f"git_sync={args.git_sync_runs} queue={[q.slug for q in queue]}"
    )

    results: list[dict[str, Any]] = []
    for step in queue:
        exp_dir = EXPERIMENTS_ROOT / step.slug
        if step.preflight is not None:
            skip_reason = step.preflight(exp_dir)
            if skip_reason:
                _append_log(f"SKIP {step.label} — preflight: {skip_reason}")
                row = {"slug": step.slug, "label": step.label, "status": "skipped", "reason": skip_reason}
                results.append(row)
                if args.skip_not_ready:
                    continue
                if not args.continue_on_error:
                    _append_log(f"BATCH abort — {step.label} not ready (use --skip-not-ready to continue)")
                    break
                continue

        try:
            check_pipeline_run_clear(slug=step.slug)
        except RuntimeError as exc:
            _append_log(f"SKIP {step.label} — mutex blocked: {exc}")
            results.append({"slug": step.slug, "label": step.label, "status": "blocked", "error": str(exc)})
            if not args.continue_on_error:
                break
            continue

        try:
            row = _run_arm(step, extra_args=extra, smoke_only=args.smoke_only)
        except Exception as exc:
            _append_log(f"ERROR {step.label}: {exc}")
            results.append(
                {
                    "slug": step.slug,
                    "label": step.label,
                    "status": "error",
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
            if not args.continue_on_error:
                break
            continue

        results.append(row)
        if row["status"] == "ok" and args.git_sync_runs:
            git_row = _git_sync_runs(slug=step.slug, label=step.label)
            row["git_sync"] = git_row

        if row["status"] != "ok" and not args.continue_on_error:
            _append_log(f"BATCH abort after {step.label} exit={row['exit_code']}")
            break

    summary = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "smoke_only": args.smoke_only,
        "git_sync_runs": args.git_sync_runs,
        "queue": [q.slug for q in queue],
        "results": results,
    }
    BATCH_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _append_log(f"BATCH summary → {BATCH_SUMMARY}")

    failed = [r for r in results if r.get("status") not in ("ok", "skipped")]
    if failed:
        raise SystemExit(f"Batch finished with failures: {[r.get('slug') for r in failed]}")


if __name__ == "__main__":
    main()
