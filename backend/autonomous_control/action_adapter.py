"""
Map raw policy logits to torque + active observation, and to Gymnasium torque vector.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from environment_definition.constants.SATELLITE import REACTION_WHEEL_MAX_TORQUE
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

from .feature_selection import AutonomousControllerAction

# Raw policy layout: [torque_channel, active_observation_logit]
POLICY_RAW_DIM = 2


def raw_policy_to_action(
    raw: np.ndarray,
    *,
    tau_limit: Any | None = None,
    active_threshold: float = 0.0,
) -> AutonomousControllerAction:
    """
    Parameters
    ----------
    raw:
        Shape (2,): unbounded torque suggestion and scalar for active observation.
    tau_limit:
        Max |torque| (N*m). Defaults to REACTION_WHEEL_MAX_TORQUE.
    active_threshold:
        active_observation is True iff raw[1] > active_threshold.
    """
    if raw.shape != (POLICY_RAW_DIM,):
        raise ValueError(f"Expected raw shape ({POLICY_RAW_DIM},), got {raw.shape}.")
    if tau_limit is None:
        tau_limit = REACTION_WHEEL_MAX_TORQUE
    tau_max = float(tau_limit.to(ureg.N * ureg.m).magnitude)
    t = float(np.clip(raw[0], -tau_max, tau_max))
    torque = t * ureg.N * ureg.m
    active = bool(raw[1] > active_threshold)
    return AutonomousControllerAction(wheel_torque_cmd=torque, active_observation=active)


def to_gym_torque_array(action: AutonomousControllerAction) -> np.ndarray:
    """Shape (1,) float32 torque in N*m for SatelliteAttitude2D."""
    tau_nm = float(action.wheel_torque_cmd.to(ureg.N * ureg.m).magnitude)
    return np.array([tau_nm], dtype=np.float32)
