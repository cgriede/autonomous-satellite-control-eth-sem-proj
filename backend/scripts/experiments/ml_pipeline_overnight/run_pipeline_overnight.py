"""Sequential overnight orchestrator for pipeline experiments 3–6.

Runs one slug at a time via each experiment's own runner + pipeline_run_guard.
Watch profile: `.cursor/skills/long-run-watch/profiles/ml-pipeline-overnight.md`
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ORCHESTRATOR_ROOT = Path(__file__).resolve().parent
EXPERIMENTS_ROOT = ORCHESTRATOR_ROOT.parent
REPO_ROOT = EXPERIMENTS_ROOT.parents[2]
for path in (EXPERIMENTS_ROOT, ORCHESTRATOR_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from _orchestrator_common import (  # noqa: E402
    LOG_PATH,
    SUMMARY_PATH,
    append_log,
    run_child,
    write_orchestrator_summary,
    write_step_error,
)
from _pipeline_steps import (  # noqa: E402
    PIPELINE_STEPS,
    STEP_BY_ID,
    STEP_ORDER,
    extract_step_kpis,
    gate_open,
    step_index,
    step_readiness,
)
from pipeline_run_guard import check_pipeline_run_clear  # noqa: E402


def _parse_steps(raw: str | None) -> tuple[str, ...]:
    if raw is None:
        return STEP_ORDER
    ids = tuple(x.strip().lower() for x in raw.split(",") if x.strip())
    unknown = [x for x in ids if x not in STEP_BY_ID]
    if unknown:
        raise SystemExit(f"Unknown --steps {unknown!r}; choose from {STEP_ORDER}")
    return ids


def _should_run_step(
    step_id: str,
    *,
    selected: tuple[str, ...],
    from_step: str | None,
    skip_complete: bool,
) -> bool:
    if step_id not in selected:
        return False
    if from_step is not None and step_index(step_id) < step_index(from_step):
        return False
    step = STEP_BY_ID[step_id]
    if skip_complete and step.summary.is_file():
        return False
    return True


def _build_argv(
    step_id: str,
    *,
    show_progress: bool,
    allow_cpu: bool,
    train_episodes: int | None,
    patience_episodes: int | None,
    reward_mode: str | None,
    trim_artifacts: bool,
    extra_argv: list[str],
) -> list[str]:
    argv: list[str] = []
    if show_progress:
        argv.append("--show-progress")
    if allow_cpu:
        argv.append("--allow-cpu")
    if trim_artifacts:
        argv.append("--trim-artifacts")

    if step_id == "exp3":
        if train_episodes is not None:
            argv.extend(["--train-episodes", str(train_episodes)])
        if patience_episodes is not None:
            argv.extend(["--patience-episodes", str(patience_episodes)])
    elif step_id in ("exp5", "exp6"):
        if train_episodes is not None:
            argv.extend(["--train-episodes", str(train_episodes)])
        if reward_mode is not None and step_id == "exp5":
            argv.extend(["--reward-mode", reward_mode])
    elif step_id == "exp4":
        if not any(a == "--arms" for a in extra_argv):
            argv.extend(["--arms", "ref0,ref1"])

    argv.extend(extra_argv)
    return argv


def _summarize_step_result(step_id: str, status: str, *, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    step = STEP_BY_ID[step_id]
    row: dict[str, Any] = {
        "step_id": step_id,
        "experiment_id": step.experiment_id,
        "slug": step.slug,
        "status": status,
        "summary_path": str(step.summary) if step.summary.is_file() else None,
    }
    kpis = extract_step_kpis(step)
    if kpis:
        row["summary"] = kpis
        arms = kpis.get("arms")
        if isinstance(arms, dict):
            row["learning_mode_by_arm"] = {
                k: (v.get("learning_mode") if isinstance(v, dict) else None)
                for k, v in arms.items()
            }
    if detail:
        row.update(detail)
    return row


def cmd_preflight(*, selected: tuple[str, ...]) -> int:
    rows = [step_readiness(STEP_BY_ID[sid]) for sid in STEP_ORDER if sid in selected]
    print(json.dumps(rows, indent=2))
    pending = [r for r in rows if r["status"] in ("scaffold_pending", "smoke_pending")]
    return 1 if pending else 0


def cmd_smoke_all(*, selected: tuple[str, ...], allow_cpu: bool) -> None:
    append_log("=== pipeline smoke-all start ===")
    for step_id in STEP_ORDER:
        if step_id not in selected:
            continue
        step = STEP_BY_ID[step_id]
        ready = step_readiness(step)
        if not ready["runner_exists"]:
            append_log(f"SMOKE SKIP {step_id} runner missing")
            print(f"[{step_id}] SKIP — runner missing: {step.runner}")
            continue
        check_pipeline_run_clear(slug=step.slug)
        argv = ["--smoke"]
        if allow_cpu:
            argv.append("--allow-cpu")
        try:
            run_child(step, argv)
            print(f"[{step_id}] smoke OK → {step.smoke}")
        except Exception as exc:
            write_step_error(step, exc)
            append_log(f"SMOKE FAIL {step_id}: {exc}")
            raise
    append_log("=== pipeline smoke-all complete ===")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pipeline overnight orchestrator — sequential Exp 3–6"
    )
    parser.add_argument(
        "--steps",
        default=None,
        help=f"Comma subset (default all): {','.join(STEP_ORDER)}",
    )
    parser.add_argument(
        "--from",
        dest="from_step",
        default=None,
        help=f"Resume from step id: {STEP_ORDER}",
    )
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Print readiness JSON for selected steps and exit",
    )
    parser.add_argument(
        "--smoke-all",
        action="store_true",
        help="Run --smoke on each selected step whose runner exists",
    )
    parser.add_argument("--show-progress", action="store_true", help="Pass --show-progress to child runners")
    parser.add_argument("--allow-cpu", action="store_true", help="Pass --allow-cpu to smoke / debug")
    parser.add_argument(
        "--ignore-gates",
        action="store_true",
        help="Run steps even if predecessor summary missing (debug only)",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Log step error and continue to next step",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run steps even if summary JSON already exists",
    )
    parser.add_argument("--train-episodes", type=int, default=None, help="Forward to exp3/5/6 runners")
    parser.add_argument("--patience-episodes", type=int, default=None, help="Forward to exp3 only")
    parser.add_argument(
        "--reward-mode",
        default=None,
        choices=("sparse", "dense"),
        help="Forward to exp5 runner",
    )
    parser.add_argument(
        "--trim-artifacts",
        action="store_true",
        help="Forward --trim-artifacts to child runners (opt-in faster video export)",
    )
    parser.add_argument(
        "--protocol",
        default="charter",
        choices=("charter", "learnable"),
        help="charter=exp3 defaults (20 ep); learnable=50 ep + longer patience (hparam-grid recipe)",
    )
    parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Extra args forwarded to each child runner (after --)",
    )
    args = parser.parse_args()

    selected = _parse_steps(args.steps)
    if args.from_step:
        _ = step_index(args.from_step.lower())

    if args.preflight:
        raise SystemExit(cmd_preflight(selected=selected))

    train_episodes = args.train_episodes
    patience_episodes = args.patience_episodes
    reward_mode = args.reward_mode
    protocol_note: dict[str, Any] = {"name": args.protocol}
    if args.protocol == "learnable" and train_episodes is None:
        train_episodes = 50
        protocol_note["train_episodes"] = 50
    if args.protocol == "learnable" and patience_episodes is None:
        patience_episodes = 20
        protocol_note["patience_episodes"] = 20
    if args.protocol == "learnable" and reward_mode is None:
        reward_mode = "sparse"
        protocol_note["reward_mode_exp5"] = "sparse"

    extra_argv = [x for x in args.extra if x != "--"]

    if args.smoke_all:
        cmd_smoke_all(selected=selected, allow_cpu=args.allow_cpu)
        return

    started_utc = datetime.now(timezone.utc).isoformat()
    append_log("=== pipeline overnight start ===")
    step_results: dict[str, Any] = {}
    completed: set[str] = set()

    for step_id in STEP_ORDER:
        if step_id not in selected:
            continue
        step = STEP_BY_ID[step_id]

        if not _should_run_step(
            step_id,
            selected=selected,
            from_step=args.from_step.lower() if args.from_step else None,
            skip_complete=not args.force,
        ):
            if step.summary.is_file() and not args.force:
                append_log(f"SKIP {step_id} summary exists")
                step_results[step_id] = _summarize_step_result(step_id, "skipped_complete")
                completed.add(step_id)
            else:
                append_log(f"SKIP {step_id} filtered")
                step_results[step_id] = _summarize_step_result(step_id, "skipped_filter")
            continue

        ok_gate, gate_reason = gate_open(step, completed=completed, ignore_gates=args.ignore_gates)
        if not ok_gate:
            append_log(f"GATE {step_id}: {gate_reason}")
            step_results[step_id] = _summarize_step_result(
                step_id, "blocked", detail={"gate_reason": gate_reason}
            )
            print(f"[{step_id}] BLOCKED — {gate_reason}")
            continue

        ready = step_readiness(step)
        if ready["status"] == "scaffold_pending":
            append_log(f"PENDING {step_id} scaffold")
            step_results[step_id] = _summarize_step_result(
                step_id, "scaffold_pending", detail={"readiness": ready}
            )
            print(f"[{step_id}] SCAFFOLD PENDING — {step.runner}")
            if not args.continue_on_error:
                break
            continue
        if ready["status"] == "smoke_pending":
            append_log(f"PENDING {step_id} smoke")
            step_results[step_id] = _summarize_step_result(
                step_id, "smoke_pending", detail={"readiness": ready}
            )
            print(f"[{step_id}] SMOKE PENDING — run: python run_pipeline_overnight.py --smoke-all")
            if not args.continue_on_error:
                break
            continue

        check_pipeline_run_clear(slug=step.slug)
        argv = _build_argv(
            step_id,
            show_progress=args.show_progress,
            allow_cpu=args.allow_cpu,
            train_episodes=train_episodes,
            patience_episodes=patience_episodes,
            reward_mode=reward_mode,
            trim_artifacts=args.trim_artifacts,
            extra_argv=extra_argv,
        )
        try:
            run_child(step, argv)
            step_results[step_id] = _summarize_step_result(step_id, "completed")
            completed.add(step_id)
            append_log(f"DONE {step_id}")
        except Exception as exc:
            err_path = write_step_error(step, exc)
            step_results[step_id] = _summarize_step_result(
                step_id, "error", detail={"error": str(exc), "error_path": str(err_path)}
            )
            append_log(f"ERROR {step_id}: {exc}")
            print(f"[{step_id}] ERROR — see {err_path}", file=sys.stderr)
            if not args.continue_on_error:
                break

    completed_utc = datetime.now(timezone.utc).isoformat()
    write_orchestrator_summary(
        step_results=step_results,
        started_utc=started_utc,
        completed_utc=completed_utc,
        protocol=protocol_note,
    )
    append_log("=== pipeline overnight complete ===")
    print(f"Orchestrator summary → {SUMMARY_PATH}")
    print(f"Log → {LOG_PATH}")
    for step_id, row in step_results.items():
        print(f"  {step_id}: {row.get('status')}")


if __name__ == "__main__":
    main()
