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


def raw_policy_to_action(
    raw: np.ndarray,
    *,
    tau_limit: Any = REACTION_WHEEL_MAX_TORQUE,
    active_threshold: float = 0.5,
) -> AutonomousControllerAction:
    """Map MPO policy output (already scaled by get_action) to controller action.
    
    Args:
        raw: Policy output [torque_nm, shutter_signal].
             Torque is in physical units [-tau_max, tau_max] N*m (post-tanh scaled).
             Shutter is in [0, 1] range (post-sigmoid scaled).
        tau_limit: Maximum torque limit for safety clipping.
        active_threshold: Threshold to convert shutter signal to binary command.
    """
    if raw.shape != (POLICY_RAW_DIM,):
        raise ValueError(f"Expected raw shape ({POLICY_RAW_DIM},), got {raw.shape}.")
    
    torque_nm = raw[0]  # Already scaled to physical units by get_action
    shutter_signal = raw[1]  # Already scaled to [0, 1] by get_action
    tau_max = float(tau_limit.to(ureg.N * ureg.m).magnitude)

    # Clip torque to safety limit (should already be within bounds from get_action)
    t = float(np.clip(torque_nm, -tau_max, tau_max))
    torque = t * ureg.N * ureg.m
    
    # Convert sigmoid output to binary shutter command
    active = bool(shutter_signal > active_threshold)
    return AutonomousControllerAction(wheel_torque_cmd=torque, active_observation=active)


def to_gym_action_array(
    action: AutonomousControllerAction,
    *,
    take_picture_signal: float,
) -> np.ndarray:
    """Map controller action to gym/MPO buffer vector ``[torque_nm, take_picture]``."""
    tau_nm = float(action.wheel_torque_cmd.to(ureg.N * ureg.m).magnitude)
    return np.array([tau_nm, float(take_picture_signal)], dtype=np.float32)


def policy_output_to_gym_action(
    raw: np.ndarray,
    *,
    tau_limit: Any | None = None,
    active_threshold: float = 0.0,
) -> tuple[AutonomousControllerAction, np.ndarray]:
    """Parse policy output and return controller action plus stored gym action vector."""
    parsed = raw_policy_to_action(
        raw,
        tau_limit=tau_limit,
        active_threshold=active_threshold,
    )
    signal = float(raw[1]) if raw.shape == (POLICY_RAW_DIM,) else -1.0
    return parsed, to_gym_action_array(parsed, take_picture_signal=signal)

