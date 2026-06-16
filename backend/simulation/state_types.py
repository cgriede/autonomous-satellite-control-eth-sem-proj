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
    # Secondary camera (§B/§E): shape (n_bins_secondary,) or (0,) when no secondary camera.
    secondary_camera_observation_line_codes: np.ndarray = None  # type: ignore[assignment]
    primary_camera_image_smear_px: float = float("nan")
    primary_camera_image_quality: float = float("nan")

    def __post_init__(self) -> None:
        if self.secondary_camera_observation_line_codes is None:
            object.__setattr__(
                self,
                "secondary_camera_observation_line_codes",
                np.empty(0, dtype=np.int8),
            )


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
    # Display label for render telemetry (see control_stack_display_label).
    controller_mode: str = "unknown"
    torque_command_source: str = "unknown"
    builtin_torque_policy: str | None = None
    torque_policy_label: str | None = None
    attitude_controller_enabled: bool = False
    render_mode: str = "interactive"
    # Optional render framing for multi-band target grids (φ bounds on orbit disk, degrees).
    target_region_bounds_deg: tuple[tuple[float, float], ...] | None = None
    view_anchor_xy_km: tuple[float, float] | None = None
    # Sim-step indices where a take-picture command fires (render shutter bands / applied reward).
    take_picture_cmd_steps: tuple[int, ...] | None = None


@dataclass(frozen=True)
class SimulationStateSeries: 
    t_s                  : np.ndarray #time index
    theta_orbit_rad      : np.ndarray #orbital angle in respect to earth
    radius_km            : np.ndarray #orbital radius
    body_z_angle_rad     : np.ndarray #body z angle in respect to earth
    simulation_reward    : np.ndarray # per-frame scalar reward
    # Wheel torque applied to plant [N·m] (after attitude safety), same indexing as t_s.
    wheel_torque_cmd_nm: np.ndarray

    # Camera (2D optics) outputs: the sensor rectangle maps to a 1D
    # in-plane footprint line segment in the renderer's 2D geometry.
    camera_gsd_m                 : np.ndarray # per-frame effective GSD at boresight [m]
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
    # Geodetic support fields (deg for compact storage in episode arrays).
    sat_subpoint_lat_deg : np.ndarray
    sat_subpoint_lon_deg : np.ndarray
    sat_altitude_m : np.ndarray
    # Columns are ``(lon_deg, lat_deg)``. Footprint corners use geodetic hits from WGS84 ellipsoid LOS;
    # subsatellite columns track ``ecef2geodetic`` of satellite disk positions (see ``orbit_disk_wgs84``).
    camera_ground_left_lon_lat_deg: np.ndarray
    camera_ground_right_lon_lat_deg: np.ndarray
    camera_ground_center_lon_lat_deg: np.ndarray
    target_area_intersection_ratio : np.ndarray
    target_area_novelty_ratio : np.ndarray

    # Cloud arc geometry (same convention as `camera_2d.compute_cloud_arc_specs_at_time`), shape (n_frames, n_clouds).
    # Kinematic / non-optics runs fill with NaN.
    cloud_arc_radius_km  : np.ndarray
    cloud_arc_start_rad  : np.ndarray
    cloud_arc_end_rad    : np.ndarray

    metadata             : SimulationMetadata

    # Agent-requested torque before attitude safety (optional; defaults to applied in __post_init__).
    wheel_torque_agent_cmd_nm: np.ndarray | None = None

    # Secondary camera fields (§B): placed after metadata with None defaults for backward compat.
    # n_bins_secondary == 0 (shape (n, 0)) signals "no secondary camera".
    # Bin dimensions may differ from primary (heterogeneous per-camera bin counts).
    # When None, __post_init__ fills with empty arrays of shape (n, 0) / (n,).
    secondary_camera_observation_line_codes: np.ndarray = None  # type: ignore[assignment]
    # Per-frame cloud-blocked fraction for the secondary strip (0.0 when no secondary).
    secondary_camera_cloud_blocked_fraction: np.ndarray = None  # type: ignore[assignment]
    # Scalar geometry for rendering the secondary camera FOV cone and strip.
    # Both default to 0.0 when no secondary camera is configured.
    secondary_camera_vertical_fov_rad: float = 0.0
    secondary_camera_tilt_off_nadir_rad: float = 0.0
    # Primary-camera motion blur during exposure (dimensionless smear in GSD units; quality in [0,1]).
    camera_image_smear_px: np.ndarray = None  # type: ignore[assignment]
    camera_image_quality: np.ndarray = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        n = self.t_s.shape[0]
        # Materialize optional secondary fields (None → empty sentinel arrays).
        if self.secondary_camera_observation_line_codes is None:
            object.__setattr__(
                self, "secondary_camera_observation_line_codes", np.empty((n, 0), dtype=np.int8)
            )
        if self.secondary_camera_cloud_blocked_fraction is None:
            object.__setattr__(
                self, "secondary_camera_cloud_blocked_fraction", np.zeros(n, dtype=float)
            )
        if self.camera_image_smear_px is None:
            object.__setattr__(self, "camera_image_smear_px", np.full(n, np.nan, dtype=float))
        if self.camera_image_quality is None:
            object.__setattr__(self, "camera_image_quality", np.full(n, np.nan, dtype=float))
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
        if self.wheel_torque_agent_cmd_nm is None:
            object.__setattr__(self, "wheel_torque_agent_cmd_nm", np.array(self.wheel_torque_cmd_nm))
        elif self.wheel_torque_agent_cmd_nm.shape[0] != n:
            raise ValueError("wheel_torque_agent_cmd_nm must have the same length as t_s.")

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
        if self.camera_image_smear_px.shape[0] != n:
            raise ValueError("camera_image_smear_px must have the same length as t_s.")
        if self.camera_image_quality.shape[0] != n:
            raise ValueError("camera_image_quality must have the same length as t_s.")
        if self.sat_subpoint_lat_deg.shape[0] != n:
            raise ValueError("sat_subpoint_lat_deg must have length n.")
        if self.sat_subpoint_lon_deg.shape[0] != n:
            raise ValueError("sat_subpoint_lon_deg must have length n.")
        if self.sat_altitude_m.shape[0] != n:
            raise ValueError("sat_altitude_m must have length n.")
        if self.camera_ground_left_lon_lat_deg.shape != (n, 2):
            raise ValueError("camera_ground_left_lon_lat_deg must have shape (n,2).")
        if self.camera_ground_right_lon_lat_deg.shape != (n, 2):
            raise ValueError("camera_ground_right_lon_lat_deg must have shape (n,2).")
        if self.camera_ground_center_lon_lat_deg.shape != (n, 2):
            raise ValueError("camera_ground_center_lon_lat_deg must have shape (n,2).")
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
        # Secondary camera validation (§B/§J): skip bin-count equality check vs primary;
        # n_bins_secondary == 0 is valid and means "no secondary camera".
        if len(self.secondary_camera_observation_line_codes.shape) != 2:
            raise ValueError("secondary_camera_observation_line_codes must be 2D (n_frames, n_bins_secondary).")
        if self.secondary_camera_observation_line_codes.shape[0] != n:
            raise ValueError("secondary_camera_observation_line_codes must have length n along axis 0.")
        if self.secondary_camera_observation_line_codes.dtype != np.int8:
            raise ValueError("secondary_camera_observation_line_codes must have dtype int8.")
        if self.secondary_camera_cloud_blocked_fraction.shape[0] != n:
            raise ValueError("secondary_camera_cloud_blocked_fraction must have length n.")
