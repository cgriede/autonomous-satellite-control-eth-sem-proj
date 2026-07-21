"""JSON contract helpers for ml_sac_vector_budget_penalty."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import _cpu_budget  # noqa: F401

import numpy as np

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"

from environment_definition.constants.SATELLITE import MAX_PRIMARY_CAPTURES_PER_ORBIT
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from _budget_frozen import BASELINE_WARMUP_RETURN_MEAN, EXP4_REF1_BASELINE_RUN_DIR  # noqa: E402

RESULTS_DIR = EXPERIMENT_ROOT / "results"
BACKEND_RUNS = BACKEND_DIR / "autonomous_control" / "runs"


def write_hypothesis_result(path: Path, **payload: Any) -> None:
    out = {"run_at_utc": datetime.now(timezone.utc).isoformat(), **payload}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2, default=_json_default), encoding="utf-8")


def _json_default(obj: Any) -> Any:
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Not JSON serializable: {type(obj)!r}")


def baseline_ref1_metadata() -> dict[str, Any]:
    run_dir = BACKEND_RUNS / EXP4_REF1_BASELINE_RUN_DIR
    summary_path = run_dir / "summary_metrics.json"
    out: dict[str, Any] = {
        "experiment_id": "ml_agent_reference_pointing",
        "arm_id": "ref1",
        "run_dir": str(run_dir),
    }
    if summary_path.is_file():
        out["summary_metrics"] = json.loads(summary_path.read_text(encoding="utf-8"))
    return out


def evaluate_learning_mode(
    train_returns: list[float],
    eval_returns: list[float],
    *,
    learning_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    eps = [float(r) for r in train_returns]
    eval_f = [float(r) for r in eval_returns]
    n = len(eps)
    any_nonzero = any(r != 0.0 for r in eps) if eps else False
    improving = n >= 2 and (eps[-1] > eps[0] or (max(eps[1:]) > eps[0] if len(eps) > 1 else False))
    learning_mode = bool(any_nonzero and improving)
    strong_lead = bool(
        eps
        and all(r > 0 for r in eps)
        and improving
        and (float(np.mean(eval_f)) > 0.0 if eval_f else False)
    )
    beats_baseline = bool(eval_f and float(np.mean(eval_f)) > BASELINE_WARMUP_RETURN_MEAN)
    return {
        "learning_mode": learning_mode,
        "strong_lead": strong_lead,
        "beats_baseline": beats_baseline,
        "train_returns": eps,
        "eval_return_mean": float(np.mean(eval_f)) if eval_f else None,
    }


def _learning_stats_summary(agent: Any, train_results: list[Any]) -> dict[str, Any]:
    if not train_results:
        return {}
    last = train_results[-1]
    stats = getattr(last, "learning_stats", None) or {}
    return dict(stats) if isinstance(stats, dict) else {}


def count_post_budget_shutter_cmds(train_results: list[Any]) -> dict[str, int]:
    """Count shutter commands fired after capture budget hit zero (per train episode)."""
    budget = int(MAX_PRIMARY_CAPTURES_PER_ORBIT)
    per_ep: dict[str, int] = {}
    total = 0
    for episode_idx, ep in enumerate(train_results):
        series = ep.simulation_series
        meta = series.metadata
        cmd_steps = list(getattr(meta, "take_picture_cmd_steps", ()) or ())
        post = max(0, len(cmd_steps) - budget)
        per_ep[str(episode_idx)] = post
        total += post
    return {"total": total, "per_episode": per_ep, "budget_per_episode": budget}


__all__ = [
    "RESULTS_DIR",
    "baseline_ref1_metadata",
    "count_post_budget_shutter_cmds",
    "evaluate_learning_mode",
    "write_hypothesis_result",
    "_learning_stats_summary",
]
