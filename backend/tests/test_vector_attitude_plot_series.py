"""Vector-mode agent pointing series + render plot input helpers."""

from __future__ import annotations

import numpy as np
import pytest

from environment_definition.constants import (
    EARTH_GRAVITATIONAL_PARAMETER,
    EARTH_RADIUS,
    RenderMode,
    SIMULATION,
    SimulationConfig,
    UREG as ureg,
)
from environment_definition.constants.MISSION import los_theta_offsets_deg
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE, SATELLITE_ALTITUDE
from render.episode_series_plotting import (
    agent_pointing_offnadir_deg_for_plot,
    torque_agent_series_for_plot,
)
from simulation.stepper import SimulationStepper


def _make_stepper(*, attitude_request_mode: str = "torque") -> SimulationStepper:
    theta_center = float(SIMULATION.theta_center.to(ureg.rad).magnitude)
    start_angle_deg, end_angle_deg = los_theta_offsets_deg(
        orbit_height=SATELLITE_ALTITUDE,
        margin_deg=float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude),
    )
    return SimulationStepper(
        simulation_config=SimulationConfig(
            render_mode=RenderMode.HEADLESS,
            torque_command_source="external",
            attitude_controller_enabled=True,
            attitude_request_mode=attitude_request_mode,  # type: ignore[arg-type]
        ),
        earth_radius=EARTH_RADIUS,
        earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
        satellite=SATELLITE,
        satellite_altitude=SATELLITE_ALTITUDE,
        theta_center_rad=theta_center,
        start_angle_deg=float(start_angle_deg),
        end_angle_deg=float(end_angle_deg),
        sat_motion_span_scale=float(SIMULATION.sat_motion_span_scale),
        sat_z_offset_deg=float(SIMULATION.sat_z_offset.to(ureg.deg).magnitude),
        ureg=ureg,
    )


def test_vector_mode_records_agent_pointing_offnadir_deg() -> None:
    stepper = _make_stepper(attitude_request_mode="vector")
    ts = stepper.current_timestep_state()
    wheel_nm = stepper.resolve_vector_u_to_torque_nm(
        u=0.25,
        theta_orbit_rad=float(ts.theta_orbit_rad),
        sat_pos_xy_km=np.asarray(ts.sat_pos_xy_km, dtype=float),
        body_z_rad=float(ts.body_z_angle_rad),
        omega_sat_rad_s=float(ts.omega_sat_rad_s),
    )
    stepper.step(wheel_torque_cmd_nm=wheel_nm, agent_pointing_cmd_u=0.25)
    series = stepper.finalize_series()
    assert series.metadata.attitude_request_mode == "vector"
    assert series.agent_pointing_offnadir_deg is not None
    assert series.agent_pointing_cmd_u is not None
    assert np.isfinite(series.agent_pointing_offnadir_deg[1])
    assert series.agent_pointing_cmd_u[1] == pytest.approx(0.25)


def test_plot_helpers_hide_torque_agent_in_vector_mode() -> None:
    stepper = _make_stepper(attitude_request_mode="vector")
    ts = stepper.current_timestep_state()
    wheel_nm = stepper.resolve_vector_u_to_torque_nm(
        u=-0.1,
        theta_orbit_rad=float(ts.theta_orbit_rad),
        sat_pos_xy_km=np.asarray(ts.sat_pos_xy_km, dtype=float),
        body_z_rad=float(ts.body_z_angle_rad),
        omega_sat_rad_s=float(ts.omega_sat_rad_s),
    )
    stepper.step(wheel_torque_cmd_nm=wheel_nm, agent_pointing_cmd_u=-0.1)
    series = stepper.finalize_series()
    assert torque_agent_series_for_plot(series) is None
    agent_deg = agent_pointing_offnadir_deg_for_plot(series)
    assert agent_deg is not None
    assert np.isfinite(agent_deg[1])
    assert agent_deg[1] < 0.0


def test_plot_helpers_show_torque_agent_in_torque_mode() -> None:
    stepper = _make_stepper(attitude_request_mode="torque")
    stepper.step(wheel_torque_cmd_nm=0.01)
    series = stepper.finalize_series()
    agent = torque_agent_series_for_plot(series)
    assert agent is not None
    assert agent_pointing_offnadir_deg_for_plot(series) is None
