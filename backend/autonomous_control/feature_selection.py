"""
Controller IO dataclasses + feature builders.

The dataclasses define the explicit contract between a simulation / env source
and the policy. They let us select which ``SimulationStateSeries`` (or env)
fields are exposed to the controller without scattering feature-construction
logic across call sites.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from environment_definition.constants.SIMULATION import OBSERVATION_TARGET
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

if TYPE_CHECKING:
    from environment_definition.attitude_control_env import SatelliteAttitudeControlEnv
    from simulation.state_types import SimulationStateSeries, SimulationTimestepState


@dataclass(frozen=True)
class AutonomousControllerState:
    """
    Controller observation bundle.

    ``obs_vector`` is the fixed-shape tensor consumed by the policy. The extra
    fields carry interpreted scene signals (target visibility, distance) so
    downstream logic (reward decomposition, diagnostics) does not have to
    reconstruct them from the raw vector.
    """

    obs_vector: np.ndarray
    target_visible: bool | None = None
    distance_to_target: Any | None = None  # pint Quantity length, when available


@dataclass(frozen=True)
class AutonomousControllerAction:
    """Torque command (SI) and whether to expose / downlink an image this step."""

    wheel_torque_cmd: Any  # pint Quantity, N*m
    active_observation: bool


@dataclass(frozen=True)
class ControllerFeatureConfig:
    features: tuple[str, ...] = (
        "angle_rel_nadir",
        "omega_sat",
        "alpha_sat",
        "angle_to_target",
        "omega_wheel",
    )


def _build_feature_value_map(
    *,
    current: "SimulationTimestepState",
    previous: "SimulationTimestepState | None",
    target_angle_rad: float,
) -> dict[str, float]:
    nadir_angle = current.theta_orbit_rad + np.pi
    angle_rel_nadir = float(np.arctan2(np.sin(current.body_z_angle_rad - nadir_angle), np.cos(current.body_z_angle_rad - nadir_angle)))
    angle_to_target = float(
        np.arctan2(
            np.sin(current.body_z_angle_rad - target_angle_rad),
            np.cos(current.body_z_angle_rad - target_angle_rad),
        )
    )
    if previous is not None and current.sim_time_s > previous.sim_time_s:
        dt = current.sim_time_s - previous.sim_time_s
        alpha_sat = float((current.omega_sat_rad_s - previous.omega_sat_rad_s) / dt)
    else:
        alpha_sat = 0.0
    return {
        "angle_rel_nadir": angle_rel_nadir,
        "omega_sat": float(current.omega_sat_rad_s),
        "alpha_sat": alpha_sat,
        "angle_to_target": angle_to_target,
        "omega_wheel": float(current.omega_wheel_rad_s),
        "body_z_angle_rad": float(current.body_z_angle_rad),
        "theta_orbit_rad": float(current.theta_orbit_rad),
        "radius_km": float(current.radius_km),
    }


def build_controller_state_from_timestep(
    *,
    current: "SimulationTimestepState",
    previous: "SimulationTimestepState | None",
    target_angle_rad: float,
    feature_config: ControllerFeatureConfig | None = None,
) -> AutonomousControllerState:
    cfg = feature_config if feature_config is not None else ControllerFeatureConfig()
    feature_values = _build_feature_value_map(
        current=current,
        previous=previous,
        target_angle_rad=target_angle_rad,
    )
    obs_vector = np.array([feature_values[name] for name in cfg.features], dtype=np.float32)
    target_visible = bool(
        np.any(np.asarray(current.camera_observation_line_codes, dtype=np.int8) == np.int8(OBSERVATION_TARGET))
    )
    return AutonomousControllerState(
        obs_vector=obs_vector,
        target_visible=target_visible,
        distance_to_target=None,
    )


def build_controller_state_from_env(
    env: "SatelliteAttitudeControlEnv",
) -> AutonomousControllerState:
    """
    Adapter from :class:`SatelliteAttitudeControlEnv` internal state to the controller
    state. Uses the same obs vector the env already returns from
    ``_build_observation`` (5-D attitude kinematics).
    """
    obs_vector = env._build_observation()
    pointing_error_rad = float(
        np.abs(env._wrap_to_pi(env._theta - env.target_theta))
    )
    cos_err = float(np.cos(pointing_error_rad))
    if cos_err > 1e-3:
        d_to_target_km = env._altitude_km / cos_err
    else:
        d_to_target_km = 1.0e9
    target_visible = bool(pointing_error_rad < env._half_vertical_fov_rad)
    return AutonomousControllerState(
        obs_vector=obs_vector,
        target_visible=target_visible,
        distance_to_target=d_to_target_km * ureg.km,
    )


def build_controller_state_from_series(
    series: "SimulationStateSeries", idx: int
) -> AutonomousControllerState:
    """
    Adapter from a ``SimulationStateSeries`` frame to the controller state.

    Only fields available on the series are used. The returned ``obs_vector``
    is a 3-D kinematic/geometric selection (``[body_z_angle_rad,
    theta_orbit_rad, radius_km]``); add more here as the series grows.
    """
    if idx < 0 or idx >= series.t_s.shape[0]:
        raise IndexError(f"frame index {idx} out of range for series length {series.t_s.shape[0]}.")

    obs_vector = np.array(
        [
            float(series.body_z_angle_rad[idx]),
            float(series.theta_orbit_rad[idx]),
            float(series.radius_km[idx]),
        ],
        dtype=np.float32,
    )

    target_visible = bool(
        np.any(series.camera_observation_line_codes[idx] == np.int8(OBSERVATION_TARGET))
    )

    ground_center = np.asarray(series.camera_ground_center_xy_km[idx], dtype=float)
    if np.isnan(ground_center).any():
        distance_to_target = None
    else:
        theta_orbit = float(series.theta_orbit_rad[idx])
        radius_km = float(series.radius_km[idx])
        sat_xy_km = np.array(
            [radius_km * np.cos(theta_orbit), radius_km * np.sin(theta_orbit)],
            dtype=float,
        )
        d_km = float(np.linalg.norm(sat_xy_km - ground_center))
        distance_to_target = d_km * ureg.km

    return AutonomousControllerState(
        obs_vector=obs_vector,
        target_visible=target_visible,
        distance_to_target=distance_to_target,
    )


__all__ = [
    "AutonomousControllerState",
    "AutonomousControllerAction",
    "ControllerFeatureConfig",
    "build_controller_state_from_timestep",
    "build_controller_state_from_env",
    "build_controller_state_from_series",
]
