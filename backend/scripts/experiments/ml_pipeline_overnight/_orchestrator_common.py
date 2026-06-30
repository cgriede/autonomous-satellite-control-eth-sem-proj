"""Shared logging and subprocess helpers for pipeline overnight orchestrator."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _pipeline_steps import PipelineStep

ORCHESTRATOR_ROOT = Path(__file__).resolve().parent
EXPERIMENTS_ROOT = ORCHESTRATOR_ROOT.parent
RESULTS_DIR = ORCHESTRATOR_ROOT / "results"
LOG_PATH = RESULTS_DIR / "pipeline_overnight.log"
SUMMARY_PATH = RESULTS_DIR / "pipeline_overnight_summary.json"


def append_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


def write_step_error(step: PipelineStep, exc: BaseException) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    err_path = RESULTS_DIR / f"{step.step_id}_error.json"
    payload = {
        "step_id": step.step_id,
        "slug": step.slug,
        "error": str(exc),
        "traceback": traceback.format_exc(),
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    err_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return err_path


def child_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def run_child(step: PipelineStep, argv: list[str]) -> None:
    if not step.runner.is_file():
        raise FileNotFoundError(f"Runner not found (scaffold pending): {step.runner}")
    cmd = [sys.executable, step.runner.name, *argv]
    append_log(f"EXEC {step.step_id} cwd={step.folder.name} argv={' '.join(argv)}")
    subprocess.run(
        cmd,
        cwd=str(step.folder),
        env=child_env(),
        check=True,
    )


def write_orchestrator_summary(
    *,
    step_results: dict[str, Any],
    started_utc: str,
    completed_utc: str,
    protocol: dict[str, Any] | None = None,
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "experiment_id": "ml_pipeline_overnight",
        "started_utc": started_utc,
        "completed_utc": completed_utc,
        "protocol": protocol or {},
        "steps": step_results,
        "log_path": str(LOG_PATH),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


__all__ = [
    "LOG_PATH",
    "RESULTS_DIR",
    "SUMMARY_PATH",
    "append_log",
    "child_env",
    "run_child",
    "write_orchestrator_summary",
    "write_step_error",
]
