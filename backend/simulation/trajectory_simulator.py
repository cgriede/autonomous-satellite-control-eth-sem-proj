from dataclasses import dataclass

import numpy as np

from .state_types import SimulationMetadata, SimulationStateSeries


@dataclass(frozen=True)
class KinematicSimulationConfig:
    earth_radius_km: float
    sat_altitude_km: float
    mu_earth_km3_s2: float
    theta_center_rad: float
    start_angle_deg: float
    end_angle_deg: float
    sat_motion_span_scale: float
    num_frames: int
    sat_z_offset_deg: float
    body_spin_rate_rad_s: float


def simulate_kinematic_trajectory(config: KinematicSimulationConfig) -> SimulationStateSeries:
    if config.num_frames < 2:
        raise ValueError("num_frames must be >= 2.")
    if config.sat_motion_span_scale <= 0.0:
        raise ValueError("sat_motion_span_scale must be > 0.")

    theta_start_rad     = config.theta_center_rad + np.deg2rad(config.start_angle_deg)
    theta_end_rad       = config.theta_center_rad + np.deg2rad(config.end_angle_deg)
    render_theta_span   = theta_end_rad - theta_start_rad
    sat_theta_span_rad  = render_theta_span * config.sat_motion_span_scale
    sat_theta_start_rad = 0.5 * (theta_start_rad + theta_end_rad) - 0.5 * sat_theta_span_rad

    r_orbit_km     = config.earth_radius_km + config.sat_altitude_km
    omega_rad_s    = float(np.sqrt(config.mu_earth_km3_s2 / (r_orbit_km**3)))
    orbit_period_s = float(2.0 * np.pi / omega_rad_s)
    sim_total_s    = float(sat_theta_span_rad / omega_rad_s)

    t_s             = np.linspace(0.0, sim_total_s, config.num_frames)
    theta_orbit_rad = sat_theta_start_rad + omega_rad_s * t_s
    radius_km       = np.full(config.num_frames, r_orbit_km, dtype=float)

    sat_z_initial_angle_rad = sat_theta_start_rad + np.pi + np.deg2rad(config.sat_z_offset_deg)
    body_z_angle_rad        = sat_z_initial_angle_rad + config.body_spin_rate_rad_s * t_s

    sim_dt_s = float(t_s[1] - t_s[0])
    metadata = SimulationMetadata(
        orbit_period_s      = orbit_period_s,
        omega_rad_s         = omega_rad_s,
        sim_total_s         = sim_total_s,
        sim_dt_s            = sim_dt_s,
        theta_start_rad     = float(theta_start_rad),
        theta_end_rad       = float(theta_end_rad),
        sat_theta_start_rad = float(sat_theta_start_rad),
        sat_theta_span_rad  = float(sat_theta_span_rad),
        start_angle_deg     = float(config.start_angle_deg),
        end_angle_deg       = float(config.end_angle_deg),
    )
    return SimulationStateSeries(
        t_s              = t_s,
        theta_orbit_rad  = theta_orbit_rad,
        radius_km        = radius_km,
        body_z_angle_rad = body_z_angle_rad,
        metadata         = metadata,
    )
