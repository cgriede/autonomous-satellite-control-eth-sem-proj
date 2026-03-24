from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SimulationMetadata : 
    orbit_period_s     : float 
    omega_rad_s        : float
    sim_total_s        : float 
    sim_dt_s           : float 
    theta_start_rad    : float 
    theta_end_rad      : float
    sat_theta_start_rad: float 
    sat_theta_span_rad : float 
    start_angle_deg    : float 
    end_angle_deg      : float


@dataclass(frozen=True)
class SimulationStateSeries: 
    t_s                  : np.ndarray #time index
    theta_orbit_rad      : np.ndarray #orbital angle in respect to earth
    radius_km            : np.ndarray #orbital radius
    body_z_angle_rad     : np.ndarray #body z angle in respect to earth
    metadata             : SimulationMetadata

    def __post_init__(self) -> None:
        n = self.t_s.shape[0]
        if n == 0:
            raise ValueError("SimulationStateSeries cannot be empty.")
        if (
            self.theta_orbit_rad.shape[0] != n
            or self.radius_km.shape[0] != n
            or self.body_z_angle_rad.shape[0] != n
        ):
            raise ValueError("All state vectors must have the same length.")
