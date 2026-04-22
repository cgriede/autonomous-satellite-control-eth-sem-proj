from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class AutonomousControllerState:
    """
    Minimal state for the linear dummy policy: a fixed-length feature vector.
    Optional flags are placeholders for wiring camera / sim codes later.
    """

    obs_vector: np.ndarray
    target_visible: bool | None = None
    distance_to_target: Any | None = None  # pint Quantity length, when available


@dataclass(frozen=True)
class AutonomousControllerAction:
    """Torque command (SI) and whether to expose / downlink an image this step."""

    wheel_torque_cmd: Any  # pint Quantity, N*m
    active_observation: bool
