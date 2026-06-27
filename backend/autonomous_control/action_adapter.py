"""Map policy outputs to controller actions and environment actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from environment_definition.constants.SATELLITE import REACTION_WHEEL_MAX_TORQUE
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

@dataclass(frozen=True)
class AutonomousControllerAction:
    """Controller torque command plus observation activation switch."""

    wheel_torque_cmd: Any  # pint Quantity, N*m
    active_observation: bool

POLICY_RAW_DIM = 2
DEFAULT_SHUTTER_THRESHOLD = 0.5


def shutter_gym_to_unit_interval(shutter_gym: float) -> float:
    """Map policy shutter dim in [-1, 1] to decision interval [0, 1]."""
    return float(0.5 * (np.clip(float(shutter_gym), -1.0, 1.0) + 1.0))


def shutter_cmd_from_gym(shutter_gym: float, *, threshold: float = DEFAULT_SHUTTER_THRESHOLD) -> bool:
    """Boolean shutter command: values mapped to [0, 1] above ``threshold`` fire."""
    return shutter_gym_to_unit_interval(shutter_gym) > float(threshold)


def raw_policy_to_action(
    raw: np.ndarray,
    *,
    tau_limit: Any = REACTION_WHEEL_MAX_TORQUE,
    active_threshold: float = DEFAULT_SHUTTER_THRESHOLD,
) -> AutonomousControllerAction:
    """Map normalized MPO action vector to simulation/controller commands.

    Policy / replay buffer semantics (both dims in [-1, 1]):
    - dim 0 (torque): fraction of RW max torque request (-1 = full reverse, +1 = full forward)
    - dim 1 (shutter): continuous pre-threshold signal; cmd is bool via ``shutter_cmd_from_gym``
    """
    if raw.shape != (POLICY_RAW_DIM,):
        raise ValueError(f"Expected raw shape ({POLICY_RAW_DIM},), got {raw.shape}.")

    tau_max = float(tau_limit.to(ureg.N * ureg.m).magnitude)
    torque_norm = float(np.clip(raw[0], -1.0, 1.0))
    torque_nm = torque_norm * tau_max
    torque = torque_nm * ureg.N * ureg.m
    active = shutter_cmd_from_gym(float(raw[1]), threshold=active_threshold)

    return AutonomousControllerAction(wheel_torque_cmd=torque, active_observation=active)


def to_gym_action_array(
    raw: np.ndarray,
) -> np.ndarray:
    """Store normalized policy output for MPO replay: ``[torque_norm, shutter_gym]`` in [-1, 1]."""
    if raw.shape != (POLICY_RAW_DIM,):
        raise ValueError(f"Expected raw shape ({POLICY_RAW_DIM},), got {raw.shape}.")
    return np.array(
        [float(np.clip(raw[0], -1.0, 1.0)), float(np.clip(raw[1], -1.0, 1.0))],
        dtype=np.float32,
    )


def policy_output_to_gym_action(
    raw: np.ndarray,
    *,
    tau_limit: Any | None = None,
    active_threshold: float = DEFAULT_SHUTTER_THRESHOLD,
) -> tuple[AutonomousControllerAction, np.ndarray]:
    """Parse policy output and return controller action plus stored gym action vector."""
    if tau_limit is None:
        tau_limit = REACTION_WHEEL_MAX_TORQUE
    parsed = raw_policy_to_action(
        raw,
        tau_limit=tau_limit,
        active_threshold=active_threshold,
    )
    stored = to_gym_action_array(raw)
    return parsed, stored


__all__ = [
    "AutonomousControllerAction",
    "DEFAULT_SHUTTER_THRESHOLD",
    "POLICY_RAW_DIM",
    "policy_output_to_gym_action",
    "raw_policy_to_action",
    "shutter_cmd_from_gym",
    "shutter_gym_to_unit_interval",
    "to_gym_action_array",
]
