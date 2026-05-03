from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SimulationTimestepState:
    step_idx: int
    sim_time_s: float
    sat_pos_xy_km: np.ndarray
    body_z_angle_rad: float
    theta_orbit_rad: float
    radius_km: float
    omega_sat_rad_s: float
    omega_wheel_rad_s: float
    reward: float
    camera_observation_line_codes: np.ndarray
    camera_center_ray_observation_code: np.int8


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
    controller_mode    : str = "unknown"
    render_mode        : str = "interactive"


@dataclass(frozen=True)
class SimulationStateSeries: 
    t_s                  : np.ndarray #time index
    theta_orbit_rad      : np.ndarray #orbital angle in respect to earth
    radius_km            : np.ndarray #orbital radius
    body_z_angle_rad     : np.ndarray #body z angle in respect to earth
    simulation_reward    : np.ndarray # per-frame scalar reward
    # Wheel torque command [N·m], same indexing as t_s; frame 0 before any step is 0.
    wheel_torque_cmd_nm  : np.ndarray

    # Camera (2D optics) outputs: the sensor rectangle maps to a 1D
    # in-plane footprint line segment in the renderer's 2D geometry.
    camera_gsd_m                 : np.ndarray # per-frame GSD at current altitude [m]
    camera_vertical_fov_rad      : float      # full vertical FOV angle [rad]
    camera_ground_left_xy_km    : np.ndarray # per-frame (x,y) Earth intersection at left sensor edge
    camera_ground_right_xy_km   : np.ndarray # per-frame (x,y) Earth intersection at right sensor edge
    camera_ground_center_xy_km  : np.ndarray # per-frame (x,y) Earth intersection at boresight
    camera_center_first_hit_xy_km : np.ndarray # per-frame (x,y) first obstruction (cloud or Earth); NaN if none
    camera_center_first_hit_is_cloud : np.ndarray # per-frame bool
    # 0 space, 1 earth, 2 cloud, 3 target (same convention as CameraObservationLine1DResult)
    camera_center_ray_observation_code : np.ndarray
    camera_cloud_blocked_fraction : np.ndarray # per-frame fraction of pixel-strip rays blocked by clouds
    # Per-bin codes from simulate_camera_observation_line_1d (shape n_frames x n_bins); -99 = not computed
    camera_observation_line_codes : np.ndarray
    # Per-bin fixed-ground line codes (shape n_frames x n_bins), including cone-hit marker code.
    fixed_ground_line_codes : np.ndarray
    # Geodetic support fields (deg for compact storage in episode arrays).
    sat_subpoint_lat_deg : np.ndarray
    sat_subpoint_lon_deg : np.ndarray
    sat_altitude_m : np.ndarray
    camera_ground_left_lat_lon_deg : np.ndarray
    camera_ground_right_lat_lon_deg : np.ndarray
    camera_ground_center_lat_lon_deg : np.ndarray
    target_area_intersection_ratio : np.ndarray
    target_area_novelty_ratio : np.ndarray

    # Cloud arc geometry (same convention as `camera_2d.compute_cloud_arc_specs_at_time`), shape (n_frames, n_clouds).
    # Kinematic / non-optics runs fill with NaN.
    cloud_arc_radius_km  : np.ndarray
    cloud_arc_start_rad  : np.ndarray
    cloud_arc_end_rad    : np.ndarray

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
        if self.simulation_reward.shape[0] != n:
            raise ValueError("simulation_reward must have the same length as t_s.")
        if self.wheel_torque_cmd_nm.shape[0] != n:
            raise ValueError("wheel_torque_cmd_nm must have the same length as t_s.")

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
        if self.camera_center_ray_observation_code.shape[0] != n:
            raise ValueError("camera_center_ray_observation_code must have length n.")
        if self.camera_cloud_blocked_fraction.shape[0] != n:
            raise ValueError("camera_cloud_blocked_fraction must have length n.")
        if len(self.camera_observation_line_codes.shape) != 2:
            raise ValueError("camera_observation_line_codes must be 2D (n_frames, n_bins).")
        if self.camera_observation_line_codes.shape[0] != n:
            raise ValueError("camera_observation_line_codes must have length n along axis 0.")
        if self.camera_observation_line_codes.dtype != np.int8:
            raise ValueError("camera_observation_line_codes must have dtype int8.")
        if len(self.fixed_ground_line_codes.shape) != 2:
            raise ValueError("fixed_ground_line_codes must be 2D (n_frames, n_bins).")
        if self.fixed_ground_line_codes.shape[0] != n:
            raise ValueError("fixed_ground_line_codes must have length n along axis 0.")
        if self.fixed_ground_line_codes.dtype != np.int8:
            raise ValueError("fixed_ground_line_codes must have dtype int8.")
        if self.fixed_ground_line_codes.shape[1] != self.camera_observation_line_codes.shape[1]:
            raise ValueError("fixed_ground_line_codes bin count must match camera_observation_line_codes.")
        if self.sat_subpoint_lat_deg.shape[0] != n:
            raise ValueError("sat_subpoint_lat_deg must have length n.")
        if self.sat_subpoint_lon_deg.shape[0] != n:
            raise ValueError("sat_subpoint_lon_deg must have length n.")
        if self.sat_altitude_m.shape[0] != n:
            raise ValueError("sat_altitude_m must have length n.")
        if self.camera_ground_left_lat_lon_deg.shape != (n, 2):
            raise ValueError("camera_ground_left_lat_lon_deg must have shape (n,2).")
        if self.camera_ground_right_lat_lon_deg.shape != (n, 2):
            raise ValueError("camera_ground_right_lat_lon_deg must have shape (n,2).")
        if self.camera_ground_center_lat_lon_deg.shape != (n, 2):
            raise ValueError("camera_ground_center_lat_lon_deg must have shape (n,2).")
        if self.target_area_intersection_ratio.shape[0] != n:
            raise ValueError("target_area_intersection_ratio must have length n.")
        if self.target_area_novelty_ratio.shape[0] != n:
            raise ValueError("target_area_novelty_ratio must have length n.")
        if self.cloud_arc_radius_km.shape[0] != n:
            raise ValueError("cloud_arc_radius_km must have length n along axis 0.")
        if self.cloud_arc_radius_km.shape != self.cloud_arc_start_rad.shape:
            raise ValueError("cloud_arc_start_rad shape must match cloud_arc_radius_km.")
        if self.cloud_arc_radius_km.shape != self.cloud_arc_end_rad.shape:
            raise ValueError("cloud_arc_end_rad shape must match cloud_arc_radius_km.")
