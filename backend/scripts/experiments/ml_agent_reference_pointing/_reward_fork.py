"""Experiment-only reward patches: sparse + optional vector-mode effort tweak."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Literal

from autonomous_control.action_adapter import AttitudeRequestMode

RewardForkMode = Literal["sparse"]

_MODE: RewardForkMode = "sparse"
_ATTITUDE_MODE: AttitudeRequestMode = "torque"
_ORIGINAL_COMPUTE: Any = None
_PATCHED = False
_VECTOR_DISABLE_TORQUE_EFFORT = True


def reward_fork_mode() -> RewardForkMode:
    return _MODE


def set_vector_reward_options(*, disable_torque_effort: bool = True) -> None:
    global _VECTOR_DISABLE_TORQUE_EFFORT
    _VECTOR_DISABLE_TORQUE_EFFORT = bool(disable_torque_effort)


def activate_reward_fork(
    mode: RewardForkMode = "sparse",
    *,
    attitude_request_mode: AttitudeRequestMode = "torque",
) -> None:
    global _MODE, _ORIGINAL_COMPUTE, _PATCHED, _ATTITUDE_MODE
    import autonomous_control.reward as reward_mod
    from autonomous_control.reward import set_reward_credit_mode

    if not _PATCHED:
        _ORIGINAL_COMPUTE = reward_mod.compute_reward
        reward_mod.compute_reward = _patched_compute_reward  # type: ignore[assignment]
        _PATCHED = True
    _MODE = mode
    _ATTITUDE_MODE = attitude_request_mode
    set_reward_credit_mode("sparse")


def deactivate_reward_fork() -> None:
    global _PATCHED, _MODE, _ATTITUDE_MODE
    if not _PATCHED or _ORIGINAL_COMPUTE is None:
        return
    import autonomous_control.reward as reward_mod
    from autonomous_control.reward import set_reward_credit_mode

    reward_mod.compute_reward = _ORIGINAL_COMPUTE
    _PATCHED = False
    _MODE = "sparse"
    _ATTITUDE_MODE = "torque"
    set_reward_credit_mode("sparse")


def _patched_compute_reward(signals: Any, cfg: Any) -> tuple[float, dict[str, float]]:
    assert _ORIGINAL_COMPUTE is not None
    if _ATTITUDE_MODE == "vector" and _VECTOR_DISABLE_TORQUE_EFFORT:
        cfg = replace(cfg, enable_torque_effort=False)
    total, components = _ORIGINAL_COMPUTE(signals, cfg)
    return float(total), components


__all__ = [
    "RewardForkMode",
    "activate_reward_fork",
    "deactivate_reward_fork",
    "reward_fork_mode",
    "set_vector_reward_options",
]
