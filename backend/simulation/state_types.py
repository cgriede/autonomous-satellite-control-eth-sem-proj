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

    # Camera (2D optics) outputs: the sensor rectangle maps to a 1D
    # in-plane footprint line segment in the renderer's 2D geometry.
    camera_gsd_m                 : np.ndarray # per-frame GSD at current altitude [m]
    camera_vertical_fov_rad      : float      # full vertical FOV angle [rad]
    camera_ground_left_xy_km    : np.ndarray # per-frame (x,y) Earth intersection at left sensor edge
    camera_ground_right_xy_km   : np.ndarray # per-frame (x,y) Earth intersection at right sensor edge
    camera_ground_center_xy_km  : np.ndarray # per-frame (x,y) Earth intersection at boresight
    camera_center_first_hit_xy_km : np.ndarray # per-frame (x,y) first obstruction (cloud or Earth); NaN if none
    camera_center_first_hit_is_cloud : np.ndarray # per-frame bool
    camera_cloud_blocked_fraction : np.ndarray # per-frame fraction of pixel-strip rays blocked by clouds

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

        if self.camera_gsd_m.shape[0] != n:
            raise ValueError("camera_gsd_m must have the same length as t_s.")
        if self.camera_ground_left_xy_km.shape != (n, 2):
            raise ValueError("camera_ground_left_xy_km must have shape (n,2).")
        if self.camera_ground_right_xy_km.shape != (n, 2):
            raise ValueError("camera_ground_right_xy_km must have shape (n,2).")
        if self.camera_ground_center_xy_km.shape != (n, 2):
            raise ValueError("camera_ground_center_xy_km must have shape (n,2).")
        if self.camera_center_first_hit_xy_km.shape != (n, 2):
            raise ValueError("camera_center_first_hit_xy_km must have shape (n,2).")
        if self.camera_center_first_hit_is_cloud.shape[0] != n:
            raise ValueError("camera_center_first_hit_is_cloud must have length n.")
        if self.camera_cloud_blocked_fraction.shape[0] != n:
            raise ValueError("camera_cloud_blocked_fraction must have length n.")
