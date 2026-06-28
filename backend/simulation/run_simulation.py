from __future__ import annotations

from typing import Any

from autonomous_control.reward import RewardConfig
from environment_definition.constants.SIMULATION import SimulationConfig

from .state_types import SimulationStateSeries
from .stepper import run_baseline_rollout


def run_simulation(
    *,
    setup=None,  # EnvironmentSetup | None
    simulation_config: SimulationConfig | None = None,
    earth_radius: Any | None = None,
    earth_gravitational_parameter: Any | None = None,
    satellite: Any | None = None,
    satellite_altitude: Any | None = None,
    theta_center_rad: float | None = None,
    start_angle_deg: float | None = None,
    end_angle_deg: float | None = None,
    sat_motion_span_scale: float | None = None,
    num_frames: int | None = None,
    sat_z_offset_deg: float | None = None,
    ureg: Any | None = None,
    camera_observation_line_n_bins: int | None = None,
    reward_config: RewardConfig | None = None,
) -> SimulationStateSeries:
    """Run a baseline/random-controller simulation episode.

    Accepts either a EnvironmentSetup (new path) or the legacy flat kwargs.
    When `setup` is provided, all legacy flat kwargs are ignored.
    """
    _ = num_frames  # compatibility: simulation derives frame count from time-based config

    if setup is not None:
        from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig as _SC
        from .setup_types import EnvironmentSetup
        from .stepper import run_baseline_rollout_from_stepper
        from .stepper_factory import build_stepper

        assert isinstance(setup, EnvironmentSetup), (
            f"run_simulation(setup=...) expects EnvironmentSetup, got {type(setup)}"
        )
        sim_cfg = simulation_config if simulation_config is not None else _SC(
            render_mode=RenderMode.HEADLESS,
            builtin_torque_policy="random",
        )
        resolved = setup.resolve(require_camera=False)
        stepper = build_stepper(resolved, simulation_config=sim_cfg)
        tau_max_nm = float(
            resolved.satellite.reaction_wheel_max_torque
            .to(resolved.ureg.N * resolved.ureg.m)
            .magnitude
        )
        return run_baseline_rollout_from_stepper(
            stepper,
            simulation_config=sim_cfg,
            tau_max_nm=tau_max_nm,
        )

    # Legacy flat-kwargs path (all existing callers).
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
        camera_observation_line_n_bins=camera_observation_line_n_bins,
        reward_config=reward_config,
    )
