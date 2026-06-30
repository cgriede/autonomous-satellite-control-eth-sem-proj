"""Experiment-only shutter threshold patch."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import autonomous_control.action_adapter as action_adapter
import autonomous_control.episode_runner as episode_runner

_ORIG_THRESHOLD = action_adapter.DEFAULT_SHUTTER_THRESHOLD
_ORIG_POLICY_OUTPUT = episode_runner.policy_output_to_gym_action


def _patched_policy_output(
    raw: Any,
    *,
    tau_limit: Any = None,
    active_threshold: float = _ORIG_THRESHOLD,
) -> Any:
    return _ORIG_POLICY_OUTPUT(raw, tau_limit=tau_limit, active_threshold=active_threshold)


@contextmanager
def shutter_threshold_fork(threshold: float) -> Iterator[None]:
    """Patch global shutter threshold for one training run."""
    t = float(threshold)

    def _bound(raw: Any, *, tau_limit: Any = None, active_threshold: float = t) -> Any:
        return _ORIG_POLICY_OUTPUT(raw, tau_limit=tau_limit, active_threshold=active_threshold)

    action_adapter.DEFAULT_SHUTTER_THRESHOLD = t
    episode_runner.policy_output_to_gym_action = _bound  # type: ignore[assignment]
    try:
        yield
    finally:
        action_adapter.DEFAULT_SHUTTER_THRESHOLD = _ORIG_THRESHOLD
        episode_runner.policy_output_to_gym_action = _ORIG_POLICY_OUTPUT  # type: ignore[assignment]
