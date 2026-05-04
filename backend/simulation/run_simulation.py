from __future__ import annotations

from typing import Any

from autonomous_control.reward import RewardConfig
from environment_definition.constants.SIMULATION import SimulationConfig

from .state_types import SimulationStateSeries
from .stepper import run_baseline_rollout


def run_simulation(
    *,
    simulation_config: SimulationConfig | None = None,
    earth_radius: Any,
    earth_gravitational_parameter: Any,
    satellite: Any,
    satellite_altitude: Any,
    theta_center_rad: float,
    start_angle_deg: float,
    end_angle_deg: float,
    sat_motion_span_scale: float,
    num_frames: int | None = None,
    sat_z_offset_deg: float,
    ureg: Any,
    camera_pixel_ray_samples: int = 96,
    camera_observation_line_n_bins: int | None = None,
    reward_config: RewardConfig | None = None,
) -> SimulationStateSeries:
    _ = num_frames  # compatibility: simulation now derives frame count from time-based config
    sim_config = simulation_config if simulation_config is not None else SimulationConfig()
    return run_baseline_rollout(
        simulation_config=sim_config,
        earth_radius=earth_radius,
        earth_gravitational_parameter=earth_gravitational_parameter,
        satellite=satellite,
        satellite_altitude=satellite_altitude,
        theta_center_rad=theta_center_rad,
        start_angle_deg=start_angle_deg,
        end_angle_deg=end_angle_deg,
        sat_motion_span_scale=sat_motion_span_scale,
        sat_z_offset_deg=sat_z_offset_deg,
        ureg=ureg,
        camera_pixel_ray_samples=camera_pixel_ray_samples,
        camera_observation_line_n_bins=camera_observation_line_n_bins,
        reward_config=reward_config,
    )
