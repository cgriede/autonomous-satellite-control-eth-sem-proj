"""Frozen safe-mode penalty knobs + Exp 8 reward parity for Exp 10."""

from __future__ import annotations

from typing import Any

from _profile_baseline import safe_mode_penalty_knobs

# Exp 8 canonical run — read-only comparator (penalty off).
EXP8_BASELINE_RUN_ID = "9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19"

# Default per penalized controller step [dimensionless reward units].
DEFAULT_K_SAFE_MODE_PENALTY = 2.0

_PENALTY_EVENT_NAMES = frozenset({"AGENT_CUT", "SAFE_MODE_TAKEOVER"})
_PENALTY_EVENT_PREFIX = "SAFE_MODE_INTERVAL_"


def penalty_config() -> dict[str, Any]:
    knobs = safe_mode_penalty_knobs()
    return {
        "enable_safe_mode_penalty": bool(knobs.get("enable_safe_mode_penalty", True)),
        "k_safe_mode_penalty": float(knobs.get("k_safe_mode_penalty", DEFAULT_K_SAFE_MODE_PENALTY)),
    }


def is_penalized_safety_event(event_name: str) -> bool:
    name = str(event_name)
    return name in _PENALTY_EVENT_NAMES or name.startswith(_PENALTY_EVENT_PREFIX)


def count_penalized_issue_steps(attitude_safety_events: list[dict[str, Any]]) -> int:
    """Count distinct issue steps with at least one penalized attitude-safety event."""
    steps: set[int] = set()
    for row in attitude_safety_events:
        if is_penalized_safety_event(str(row.get("event", ""))):
            steps.add(int(row["step"]))
    return len(steps)


__all__ = [
    "DEFAULT_K_SAFE_MODE_PENALTY",
    "EXP8_BASELINE_RUN_ID",
    "count_penalized_issue_steps",
    "is_penalized_safety_event",
    "penalty_config",
]
