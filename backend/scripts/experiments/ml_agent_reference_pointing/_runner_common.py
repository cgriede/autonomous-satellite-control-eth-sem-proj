"""JSON contract helpers for ml_agent_reference_pointing (no overnight _runner_common import)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import _cpu_budget  # noqa: F401

import numpy as np

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from _reference_frozen import BASELINE_WARMUP_RETURN_MEAN  # noqa: E402

RESULTS_DIR = EXPERIMENT_ROOT / "results"


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


def evaluate_learning_mode(
    train_returns: list[float],
    eval_returns: list[float],
    *,
    learning_stats: dict[str, Any] | None = None,
    agent_kind: Literal["mpo", "sac"] = "mpo",
) -> dict[str, Any]:
    eps = [float(r) for r in train_returns]
    eval_f = [float(r) for r in eval_returns]
    n = len(eps)
    any_nonzero = any(r != 0.0 for r in eps) if eps else False
    improving = n >= 2 and (eps[-1] > eps[0] or (max(eps[1:]) > eps[0] if len(eps) > 1 else False))
    stats = learning_stats or {}
    kl_mean_last = float(stats.get("kl_mean_last", float("nan")))
    if agent_kind == "sac":
        kl_finite = True
    else:
        kl_finite = np.isfinite(kl_mean_last) and kl_mean_last < 1e4
    learning_mode = bool(any_nonzero and improving and kl_finite)
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
        "kl_mean_last": kl_mean_last if agent_kind == "mpo" else None,
    }


def write_analysis_card(
    path: Path,
    *,
    hypothesis_id: str,
    json_path: Path,
    sections: dict[str, str],
) -> None:
    lines = [f"# Analysis — {hypothesis_id}", "", f"Source: `{json_path}`", ""]
    for title, body in sections.items():
        lines.extend([f"## {title}", "", body, ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _episode_debug_row(result: Any, *, episode_idx: int) -> dict[str, Any]:
    series = result.simulation_series
    meta = series.metadata
    shutter_steps = list(getattr(meta, "take_picture_cmd_steps", ()) or ())
    rewards = np.asarray(series.simulation_reward[1 : result.steps + 1], dtype=float)
    return {
        "episode_idx": episode_idx,
        "episode_return": float(result.episode_return),
        "steps": int(result.steps),
        "positive_reward_steps": int(np.sum(rewards > 0.0)),
        "shutter_cmd_steps": len(shutter_steps),
    }


def _learning_stats_summary(agent: Any, train_results: list[Any]) -> dict[str, Any]:
    if not train_results:
        return {}
    last = train_results[-1]
    stats = getattr(last, "learning_stats", None) or {}
    return dict(stats) if isinstance(stats, dict) else {}


__all__ = [
    "RESULTS_DIR",
    "evaluate_learning_mode",
    "write_analysis_card",
    "write_hypothesis_result",
    "_episode_debug_row",
    "_learning_stats_summary",
]
