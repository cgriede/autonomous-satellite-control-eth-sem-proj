"""
Minimal timestep feature selection for controller inputs.

This module intentionally does one thing: read selected keys from a single
``SimulationTimestepState`` and return them as a dictionary for downstream
controller input construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from simulation.state_types import SimulationTimestepState


@dataclass(frozen=True)
class ControllerFeatureConfig:
    """
    Grouped feature-key selection from ``SimulationTimestepState``.

    The returned input dictionary preserves grouped order:
    ``attitude_keys -> orbit_keys -> wheel_keys -> vision_keys -> mission_keys``.
    """

    attitude_keys: tuple[str, ...] = (
        "body_z_angle_rad",
        "omega_sat_rad_s",
    )
    orbit_keys: tuple[str, ...] = (
        "theta_orbit_rad",
    )
    # `state_vector` is built from selected state attributes.
    # `vision_observation` refers to camera-derived arrays/scalars included here.
    # `secondary_camera_observation_line_codes` has shape (n_bins_secondary,) or (0,) when
    # no secondary camera; controller_observation_dim must account for +200 bins when dual-camera.
    vision_keys: tuple[str, ...] = (
        "camera_observation_line_codes",
        "secondary_camera_observation_line_codes",
    )

    @property
    def selected_keys(self) -> tuple[str, ...]:
        return (
            self.attitude_keys
            + self.orbit_keys
            + self.vision_keys
        )


def _to_plain_value(value: Any) -> Any:
    """Return float for scalar numerics, keep bool/arrays/other payloads as-is."""
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    return value


def _select_keys_from_timestep(
    *,
    timestep: "SimulationTimestepState",
    keys: tuple[str, ...],
) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for key in keys:
        if not hasattr(timestep, key):
            raise KeyError(f"SimulationTimestepState has no attribute '{key}'.")
        selected[key] = _to_plain_value(getattr(timestep, key))
    return selected


def select_controller_inputs_from_timestep(
    *,
    timestep: "SimulationTimestepState",
    feature_config: ControllerFeatureConfig | None = None,
) -> dict[str, Any]:
    """Select configured timestep keys for controller input construction."""
    cfg = feature_config if feature_config is not None else ControllerFeatureConfig()
    return _select_keys_from_timestep(timestep=timestep, keys=cfg.selected_keys)


# TODO: align reward computation to a similarly explicit key-selection interface.

__all__ = [
    "ControllerFeatureConfig",
    "select_controller_inputs_from_timestep",
]
