"""Shared runner utilities for Exp 14."""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPERIMENT_ROOT = Path(__file__).resolve().parent
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"

RESULTS_DIR = EXPERIMENT_ROOT / "results"
EXPERIMENT_ID = "ml_mpo_multienv_target_select"


def append_log(line: str) -> None:
    """Console-only status line (timestamped). Use JSON artifacts for durable KPIs."""
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    msg = f"[{stamp}] {line}"
    try:
        from tqdm.auto import tqdm

        tqdm.write(msg)
    except ImportError:
        print(msg, flush=True)


def _load_overnight_runner() -> Any:
    spec = importlib.util.spec_from_file_location(
        "ml_overnight_runner_common_exp14_isolated",
        OVERNIGHT_ROOT / "_runner_common.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_overnight = _load_overnight_runner()
write_hypothesis_result = _overnight.write_hypothesis_result
evaluate_learning_mode = _overnight.evaluate_learning_mode
_learning_stats_summary = _overnight._learning_stats_summary


__all__ = [
    "BACKEND_DIR",
    "EXPERIMENT_ID",
    "EXPERIMENT_ROOT",
    "OVERNIGHT_ROOT",
    "RESULTS_DIR",
    "S01_DIR",
    "append_log",
    "evaluate_learning_mode",
    "write_hypothesis_result",
    "_learning_stats_summary",
]
