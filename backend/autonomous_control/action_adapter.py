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
    """Map MPO gym action tensor to simulation/controller commands.

    MPO keeps a single tanh-squashed action vector. This adapter applies the
    per-dimension simulation semantics at the ML/simulation boundary:
    - dim 0 (torque): continuous N*m, clipped to hardware limit
    - dim 1 (shutter): tanh gym value mapped to [0, 1], then thresholded
    """
    if raw.shape != (POLICY_RAW_DIM,):
        raise ValueError(f"Expected raw shape ({POLICY_RAW_DIM},), got {raw.shape}.")

    tau_max = float(tau_limit.to(ureg.N * ureg.m).magnitude)
    t = float(np.clip(raw[0], -tau_max, tau_max))
    torque = t * ureg.N * ureg.m
    
    
    #Map MPO gym shutter dim (tanh-squashed in [-1, 1]) to [0, 1] at sim boundary.
    shutter_signal = float(0.5 * (np.clip(raw[1], -1.0, 1.0) + 1.0))
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
    active_threshold: float = 0.5,
) -> tuple[AutonomousControllerAction, np.ndarray]:
    """Parse policy output and return controller action plus stored gym action vector."""
    if tau_limit is None:
        tau_limit = REACTION_WHEEL_MAX_TORQUE
    parsed = raw_policy_to_action(
        raw,
        tau_limit=tau_limit,
        active_threshold=active_threshold,
    )
    signal = float(raw[1]) if raw.shape == (POLICY_RAW_DIM,) else -1.0
    return parsed, to_gym_action_array(parsed, take_picture_signal=signal)

