from __future__ import annotations

from typing import Any

import numpy as np

from .attitude_dynamics import AttitudeState2D, propagate_reaction_wheel_attitude_2d
from .reaction_wheel import ReactionWheel
from .state_types import SimulationMetadata, SimulationStateSeries


def run_simulation(
    *,
    earth_radius: Any,
    earth_gravitational_parameter: Any,
    satellite: Any,
    satellite_altitude: Any,
    theta_center_rad: float,
    start_angle_deg: float,
    end_angle_deg: float,
    sat_motion_span_scale: float,
    num_frames: int,
    sat_z_offset_deg: float,
    ureg: Any,
) -> SimulationStateSeries:
    """
    Canonical numeric simulation entrypoint for rendering runs.

    Contract:
    - performs numeric propagation / simulation
    - returns a typed `SimulationStateSeries`
    - rendering code should only consume the returned state series
    """

    if num_frames < 2:
        raise ValueError("num_frames must be >= 2.")
    if sat_motion_span_scale <= 0.0:
        raise ValueError("sat_motion_span_scale must be > 0.")

    r_earth_km = earth_radius.to(ureg.km).magnitude
    sat_altitude_km = satellite_altitude.to(ureg.km).magnitude
    mu_earth_km3_s2 = earth_gravitational_parameter.to((ureg.km ** 3) / (ureg.s ** 2)).magnitude

    # Orbital state
    theta_start_rad = float(theta_center_rad) + np.deg2rad(float(start_angle_deg))
    theta_end_rad = float(theta_center_rad) + np.deg2rad(float(end_angle_deg))
    render_theta_span = theta_end_rad - theta_start_rad
    sat_theta_span_rad = render_theta_span * float(sat_motion_span_scale)
    sat_theta_start_rad = 0.5 * (theta_start_rad + theta_end_rad) - 0.5 * sat_theta_span_rad

    r_orbit_km = r_earth_km + sat_altitude_km
    omega_rad_s = float(np.sqrt(mu_earth_km3_s2 / (r_orbit_km**3)))
    orbit_period_s = float(2.0 * np.pi / omega_rad_s)
    sim_total_s = float(sat_theta_span_rad / omega_rad_s)

    t_s = np.linspace(0.0, sim_total_s, int(num_frames))
    theta_orbit_rad = sat_theta_start_rad + omega_rad_s * t_s
    radius_km = np.full(int(num_frames), r_orbit_km, dtype=float)
    sim_dt_s = float(t_s[1] - t_s[0])

    # Attitude dynamics initial conditions
    sat_inertia = satellite.moment_of_inertia_2d.to(ureg.kg * ureg.m**2)
    # Wheel inertia from max momentum and max wheel speed.
    # (Units: max momentum [kg*m^2/s] divided by omega [1/s] => kg*m^2)
    omega_w_max = 150.0 * ureg.rad / ureg.s
    wheel_inertia = (satellite.reaction_wheel_max_momentum / omega_w_max).to(ureg.kg * ureg.m**2)

    if sat_inertia.to(ureg.kg * ureg.m**2).magnitude <= 0.0:
        raise ValueError("sat_inertia must be > 0.")
    if wheel_inertia.to(ureg.kg * ureg.m**2).magnitude <= 0.0:
        raise ValueError("wheel_inertia must be > 0.")

    # Map the prior "body torque cmd" sign convention to this dynamics model:
    # propagate_reaction_wheel_attitude_2d uses alpha_sat = -wheel_torque / sat_inertia.
    body_torque_cmd_nm = satellite.reaction_wheel_max_torque.to(ureg.N * ureg.m).magnitude
    wheel_torque_cmd = (-float(body_torque_cmd_nm)) * ureg.N * ureg.m

    reaction_wheel = ReactionWheel(
        wheel_inertia=wheel_inertia,
        max_manouver_rate=satellite.star_tracker_max_maneuver_rate,
    )

    sat_z_initial_angle_rad = sat_theta_start_rad + np.pi + np.deg2rad(float(sat_z_offset_deg))
    state = AttitudeState2D(
        theta=float(sat_z_initial_angle_rad) * ureg.rad,
        omega_sat=0.0 * ureg.rad / ureg.s,
        omega_wheel=0.0 * ureg.rad / ureg.s,
    )

    body_z_angle_rad = np.empty(int(num_frames), dtype=float)
    body_z_angle_rad[0] = state.theta.to(ureg.rad).magnitude

    dt = sim_dt_s * ureg.s
    for k in range(1, int(num_frames)):
        tau_applied = reaction_wheel.compute_applied_torque(state=state, tau_cmd=wheel_torque_cmd)
        state = propagate_reaction_wheel_attitude_2d(
            state=state,
            wheel_torque=tau_applied,
            sat_inertia=sat_inertia,
            wheel_inertia=wheel_inertia,
            dt=dt,
        )
        body_z_angle_rad[k] = state.theta.to(ureg.rad).magnitude

    metadata = SimulationMetadata(
        orbit_period_s=orbit_period_s,
        omega_rad_s=omega_rad_s,
        sim_total_s=sim_total_s,
        sim_dt_s=sim_dt_s,
        theta_start_rad=float(theta_start_rad),
        theta_end_rad=float(theta_end_rad),
        sat_theta_start_rad=float(sat_theta_start_rad),
        sat_theta_span_rad=float(sat_theta_span_rad),
        start_angle_deg=float(start_angle_deg),
        end_angle_deg=float(end_angle_deg),
    )

    return SimulationStateSeries(
        t_s=t_s,
        theta_orbit_rad=theta_orbit_rad,
        radius_km=radius_km,
        body_z_angle_rad=body_z_angle_rad,
        metadata=metadata,
    )

