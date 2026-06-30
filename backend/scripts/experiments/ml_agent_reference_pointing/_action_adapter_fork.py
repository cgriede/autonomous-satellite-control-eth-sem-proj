"""Deprecated experiment shim — production uses ``autonomous_control.action_adapter``."""

from autonomous_control.action_adapter import (
    AttitudeRequestMode,
    policy_output_to_gym_action,
)

_MODE: AttitudeRequestMode = "torque"


def attitude_request_mode() -> AttitudeRequestMode:
    return _MODE


def set_attitude_request_mode(mode: AttitudeRequestMode) -> None:
    global _MODE
    if mode not in ("torque", "vector"):
        raise ValueError(f"Unsupported attitude_request_mode: {mode!r}")
    _MODE = mode


__all__ = [
    "AttitudeRequestMode",
    "attitude_request_mode",
    "policy_output_to_gym_action",
    "set_attitude_request_mode",
]
