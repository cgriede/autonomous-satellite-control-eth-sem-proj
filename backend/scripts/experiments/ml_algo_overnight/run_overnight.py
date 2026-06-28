"""One-command overnight ML hypothesis cycle: smoke → H0 → H1a → H1b → H6 → H4."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import _cpu_budget  # noqa: F401

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from _phases.h0_dt import phase_h0_dt
from _phases.h1_mpo_sparse import phase_h1a_mpo_sparse, phase_h1b_mpo_stable_eta
from _phases.h4_sac import phase_h4_sac
from _phases.h6_mpo_dense_latent import phase_h6_mpo_dense_latent
from _phases.smoke import phase_smoke
from _runner_common import (
    DT_PROFILE_PATH,
    RESULTS_DIR,
    append_overnight_log,
    write_hypothesis_result,
    write_phase_error,
)

OVERNIGHT_SUMMARY = RESULTS_DIR / "overnight_summary.json"

PHASE_ORDER = ("h0", "h1a", "h1b", "h6", "h4")
PHASE_RESULT_PATHS = {
    "h0": DT_PROFILE_PATH,
    "h1a": RESULTS_DIR / "h1a_mpo_sparse.json",
    "h1b": RESULTS_DIR / "h1b_mpo_stable_eta.json",
    "h6": RESULTS_DIR / "h6_mpo_dense_latent.json",
    "h4": RESULTS_DIR / "h4_sac.json",
}


def _phase_index(name: str) -> int:
    try:
        return PHASE_ORDER.index(name.lower())
    except ValueError as exc:
        raise SystemExit(f"Unknown phase {name!r}; choose from {PHASE_ORDER}") from exc


def _should_run(phase: str, *, from_phase: str | None, only_phases: set[str] | None) -> bool:
    if only_phases is not None and phase not in only_phases:
        return False
    if from_phase is not None and _phase_index(phase) < _phase_index(from_phase):
        return False
    result_path = PHASE_RESULT_PATHS.get(phase)
    if result_path is not None and result_path.is_file() and from_phase is None and only_phases is None:
        return False
    return True


def _load_phase_learning_mode(phase: str) -> dict[str, Any] | None:
    path = PHASE_RESULT_PATHS.get(phase)
    if path is None or not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if phase == "h0":
        return {"aborted": data.get("aborted", False), "learning_mode": not data.get("aborted", False)}
    signal = data.get("learning_signal") or data.get("treatment", {}).get("kpis", {}).get("learning_signal")
    if signal:
        return signal
    return None


def _run_phase_safe(name: str, fn: Callable[..., Any], **kwargs: Any) -> dict[str, Any] | None:
    try:
        return fn(**kwargs)
    except Exception as exc:
        write_phase_error(name, exc)
        print(f"[{name}] ERROR: {exc}", file=sys.stderr)
        traceback.print_exc()
        return None


def _write_summary(results: dict[str, Any]) -> None:
    ranked: list[dict[str, Any]] = []
    for phase in ("h1a", "h1b", "h6", "h4"):
        signal = _load_phase_learning_mode(phase)
        if signal is None:
            continue
        ranked.append(
            {
                "phase": phase,
                "learning_mode": bool(signal.get("learning_mode")),
                "strong_lead": bool(signal.get("strong_lead", False)),
                "beats_baseline": bool(signal.get("beats_baseline", False)),
                "eval_return_mean": signal.get("eval_return_mean"),
                "train_returns": signal.get("train_returns"),
            }
        )
    ranked.sort(
        key=lambda row: (
            not row["learning_mode"],
            not row.get("strong_lead", False),
            -(row.get("eval_return_mean") or 0.0),
        ),
    )
    write_hypothesis_result(
        OVERNIGHT_SUMMARY,
        experiment_id="ml_algo_overnight",
        completed_at_utc=datetime.now(timezone.utc).isoformat(),
        phases=results,
        ranked_by_learning_mode=ranked,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="ML algorithm overnight hypothesis cycle")
    parser.add_argument("--smoke-only", action="store_true", help="Run smoke test and exit")
    parser.add_argument("--allow-cpu", action="store_true", help="Allow smoke without CUDA (debug)")
    parser.add_argument("--from", dest="from_phase", default=None, help=f"Resume from phase: {PHASE_ORDER}")
    parser.add_argument("--phases", default=None, help="Comma-separated subset, e.g. h1a,h6")
    parser.add_argument("--show-progress", action="store_true", help="Enable tqdm progress bars")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    append_overnight_log("=== overnight run start ===")

    only_phases = {p.strip().lower() for p in args.phases.split(",")} if args.phases else None
    show = args.show_progress
    results: dict[str, Any] = {}

    phase_smoke(allow_cpu=args.allow_cpu)
    if args.smoke_only:
        print(f"Smoke OK — see {RESULTS_DIR / 'smoke.json'}")
        return

    if _should_run("h0", from_phase=args.from_phase, only_phases=only_phases):
        h0 = _run_phase_safe("h0", phase_h0_dt)
        results["h0"] = h0
        if h0 and h0.get("aborted"):
            append_overnight_log("ABORT queue: H0 found no valid dt profile")
            _write_summary(results)
            raise SystemExit(1)

    for name, fn in (
        ("h1a", phase_h1a_mpo_sparse),
        ("h1b", phase_h1b_mpo_stable_eta),
        ("h6", phase_h6_mpo_dense_latent),
        ("h4", phase_h4_sac),
    ):
        if not _should_run(name, from_phase=args.from_phase, only_phases=only_phases):
            append_overnight_log(f"SKIP {name}")
            continue
        results[name] = _run_phase_safe(name, fn, show_progress=show)

    _write_summary(results)
    append_overnight_log("=== overnight run complete ===")
    print(f"Done — summary: {OVERNIGHT_SUMMARY}")


if __name__ == "__main__":
    main()
