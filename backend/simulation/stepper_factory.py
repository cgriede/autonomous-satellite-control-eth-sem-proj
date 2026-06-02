"""Shared stepper factory: sole constructor of SimulationStepper from a ResolvedSimulationSetup.

Callers:
- autonomous_control.episode_runner.EpisodeRunner.run_serial
- autonomous_control.parallel_training._build_stepper (replaces inline construction)
- simulation.run_simulation (when setup kwarg is provided)
"""
from __future__ import annotations

from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig
from .setup_types import ResolvedSimulationSetup, SimulationSetupError
from .stepper import SimulationStepper


def build_stepper(
    resolved: ResolvedSimulationSetup,
    *,
    simulation_config: SimulationConfig,
    require_camera: bool = False,
) -> SimulationStepper:
    """Construct a SimulationStepper from a ResolvedSimulationSetup.

    Args:
        resolved: Fully-populated setup from EnvironmentSetup.resolve().
        simulation_config: Controls render_mode, controller_mode metadata and seed.
        require_camera: When True, raises SimulationSetupError if resolved.cameras is empty.

    Returns:
        A freshly-constructed SimulationStepper ready to step.
    """
    if require_camera and len(resolved.cameras) == 0:
        raise SimulationSetupError(
            "cameras is empty but require_camera=True. "
            "Add CameraMount(...) in build_setup()."
        )
    return SimulationStepper(
        simulation_config=simulation_config,
        earth_radius=resolved.earth_radius,
        earth_gravitational_parameter=resolved.earth_gravitational_parameter,
        satellite=resolved.satellite,
        satellite_altitude=resolved.altitude,
        theta_center_rad=resolved.theta_center_rad,
        start_angle_deg=resolved.start_angle_deg,
        end_angle_deg=resolved.end_angle_deg,
        sat_motion_span_scale=resolved.sat_motion_span_scale,
        sat_z_offset_deg=resolved.sat_z_offset_deg,
        ureg=resolved.ureg,
        camera_pixel_ray_samples=resolved.camera_pixel_ray_samples,
        camera_observation_line_n_bins=resolved.camera_observation_line_n_bins,
        reward_config=resolved.reward_config,
        clouds=resolved.clouds,
        cameras=resolved.cameras,
        camera_kernel_backend=resolved.camera_kernel_backend,
        secondary_camera_observation_line_n_bins=resolved.secondary_camera_observation_line_n_bins,
    )
