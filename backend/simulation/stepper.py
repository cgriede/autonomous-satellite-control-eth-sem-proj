from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from tqdm import tqdm

from autonomous_control.controller_baselines import MaxTorqueSweepPolicy, RandomTorquePolicy, ZeroTorquePolicy
from autonomous_control.reward import RewardConfig
from environment_definition.constants.EARTH import WGS84_ELLIPSOID
from environment_definition.constants.MISSION import OBSERVATION_TARGET_AREAS
from environment_definition.constants.SIMULATION import (
    RenderMode,
    SIMULATION,
    SimulationConfig,
    _BASELINE_CONTROLLER_MODES,
)

from .attitude_dynamics import AttitudeState2D
from .camera_2d import (
    boresight_dir_for_mount,
    calculate_fov_angles,
)
from .dynamics_kernel import DynamicsKernel
from .reaction_wheel import ReactionWheel
from .reward_kernel import RewardKernel
from .scheduler import resolve_controller_interval_steps
from .sensor_kernel import SensorKernel
from .state_types import SimulationMetadata, SimulationStateSeries, SimulationTimestepState
from utils.geodesics.geodesic_helpers import circle_stripe_footprint_overlap_ratio
from utils.geometry.mission_stripe_disk import primary_stripe_disk_phi_bounds_deg
from utils.geometry.orbit_disk_wgs84 import disk_xy_km_to_geodetic_deg


@dataclass(frozen=True)
class SimulationEpisodeContext:
    simulation_series: SimulationStateSeries
    effective_controller_update_interval_steps: int
    effective_controller_update_interval_s: float
    configured_controller_update_interval_s: float


@dataclass(frozen=True)
class _ControllerAdapterEnv:
    action_space: Any
    dt: Any


def _build_simulation_controller(*, controller_mode: str, tau_max_nm: float, dt: Any, rng: np.random.Generator):
    mode = str(controller_mode).lower()
    if mode == "coast":
        return ZeroTorquePolicy()
    from gymnasium import spaces

    adapter_env = _ControllerAdapterEnv(
        action_space=spaces.Box(
            low=np.array([-tau_max_nm], dtype=np.float32),
            high=np.array([tau_max_nm], dtype=np.float32),
            shape=(1,),
            dtype=np.float32,
        ),
        dt=dt,
    )
    if mode == "random":
        return RandomTorquePolicy(adapter_env, rng=rng)
    if mode == "baseline":
        return MaxTorqueSweepPolicy(adapter_env, period_s=100.0)
    raise ValueError(f"Unsupported controller_mode: {controller_mode!r}")


class SimulationStepper:
    def __init__(
        self,
        *,
        simulation_config: SimulationConfig,
        earth_radius: Any,
        earth_gravitational_parameter: Any,
        satellite: Any,
        satellite_altitude: Any,
        theta_center_rad: float,
        start_angle_deg: float,
        end_angle_deg: float,
        sat_motion_span_scale: float,
        sat_z_offset_deg: float,
        ureg: Any,
        camera_pixel_ray_samples: int = 96,
        camera_observation_line_n_bins: int | None = None,
        reward_config: RewardConfig | None = None,
        clouds: tuple | None = None,
        cameras: tuple = (),
        camera_kernel_backend: str | None = None,
        secondary_camera_observation_line_n_bins: int = 0,
    ) -> None:
        if sat_motion_span_scale <= 0.0:
            raise ValueError("sat_motion_span_scale must be > 0.")
        if len(OBSERVATION_TARGET_AREAS) == 0:
            raise ValueError("MISSION.OBSERVATION_TARGET_AREAS must contain at least one target area.")
        self._sim_config = simulation_config
        self._theta_center_rad = float(theta_center_rad)
        self._render_mode = str(
            simulation_config.render_mode.value
            if isinstance(simulation_config.render_mode, RenderMode)
            else simulation_config.render_mode
        )
        self._controller_mode = str(simulation_config.controller_mode).lower()
        self._ureg = ureg

        # Resolved setup objects (§1.2, §C)
        self._clouds = clouds if clouds is not None else SIMULATION.clouds
        self._cameras = cameras
        self._camera_kernel_backend = camera_kernel_backend if camera_kernel_backend is not None else SIMULATION.camera_kernel_backend
        # Secondary camera guard (§J): only activate secondary if len(cameras) >= 2
        self._has_secondary = len(self._cameras) >= 2
        self._n_bins_secondary = int(secondary_camera_observation_line_n_bins) if self._has_secondary else 0

        r_earth_km = earth_radius.to(ureg.km).magnitude
        sat_altitude_km = satellite_altitude.to(ureg.km).magnitude
        mu_earth_km3_s2 = earth_gravitational_parameter.to((ureg.km ** 3) / (ureg.s ** 2)).magnitude
        theta_start_rad = float(theta_center_rad) + np.deg2rad(float(start_angle_deg))
        theta_end_rad = float(theta_center_rad) + np.deg2rad(float(end_angle_deg))
        render_theta_span = theta_end_rad - theta_start_rad
        sat_theta_span_rad = render_theta_span * float(sat_motion_span_scale)
        sat_theta_start_rad = 0.5 * (theta_start_rad + theta_end_rad) - 0.5 * sat_theta_span_rad
        r_orbit_km = r_earth_km + sat_altitude_km
        omega_rad_s = float(np.sqrt(mu_earth_km3_s2 / (r_orbit_km**3)))
        sim_total_s = float(sat_theta_span_rad / omega_rad_s)
        orbit_period_s = float(2.0 * np.pi / omega_rad_s)

        sim_dt_requested_s = float(SIMULATION.simulation_timestep.to(ureg.s).magnitude)
        if sim_dt_requested_s <= 0.0:
            raise ValueError("SIMULATION.simulation_timestep must be > 0 s.")
        n = max(2, int(np.ceil(sim_total_s / sim_dt_requested_s)) + 1)
        t_s = np.linspace(0.0, sim_total_s, n, dtype=float)
        self._theta_orbit_rad = sat_theta_start_rad + omega_rad_s * t_s
        self._radius_km = np.full(n, r_orbit_km, dtype=float)
        self._sim_total_s = sim_total_s
        self._sim_dt_s = float(t_s[1] - t_s[0])
        self._t_s = t_s
        configured_interval_s = float(SIMULATION.controller_update_interval.to(ureg.s).magnitude)
        self._controller_interval_steps, self._effective_controller_interval_s = resolve_controller_interval_steps(
            configured_interval_s=configured_interval_s,
            sim_dt_s=sim_dt_requested_s,
        )

        sat_inertia = satellite.moment_of_inertia_2d.to(ureg.kg * ureg.m**2)
        omega_w_max = 150.0 * ureg.rad / ureg.s
        wheel_inertia = (satellite.reaction_wheel_max_momentum / omega_w_max).to(ureg.kg * ureg.m**2)
        if sat_inertia.to(ureg.kg * ureg.m**2).magnitude <= 0.0:
            raise ValueError("sat_inertia must be > 0.")
        if wheel_inertia.to(ureg.kg * ureg.m**2).magnitude <= 0.0:
            raise ValueError("wheel_inertia must be > 0.")
        self._sat_inertia = sat_inertia
        self._wheel_inertia = wheel_inertia
        self._reaction_wheel = ReactionWheel(
            wheel_inertia=wheel_inertia,
            max_manouver_rate=satellite.star_tracker_max_maneuver_rate,
        )
        sat_z_initial_angle_rad = sat_theta_start_rad + np.pi + np.deg2rad(float(sat_z_offset_deg))
        self._state = AttitudeState2D(
            theta=float(sat_z_initial_angle_rad) * ureg.rad,
            omega_sat=0.0 * ureg.rad / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        self._body_z_angle_rad = np.empty(n, dtype=float)
        self._body_z_angle_rad[0] = float(self._state.theta.to(ureg.rad).magnitude)
        self._simulation_reward = np.empty(n, dtype=float)
        self._simulation_reward[0] = 0.0
        self._wheel_torque_cmd_nm = np.zeros(n, dtype=float)
        n_bins = int(camera_observation_line_n_bins or SIMULATION.camera_observation_line_n_bins)
        if n_bins < 1:
            raise ValueError("camera_observation_line_n_bins must be >= 1.")

        self._camera_gsd_m = np.full(n, np.nan, dtype=float)
        self._camera_ground_left_xy_km = np.full((n, 2), np.nan, dtype=float)
        self._camera_ground_right_xy_km = np.full((n, 2), np.nan, dtype=float)
        self._camera_ground_center_xy_km = np.full((n, 2), np.nan, dtype=float)
        self._camera_center_first_hit_xy_km = np.full((n, 2), np.nan, dtype=float)
        self._camera_center_first_hit_is_cloud = np.zeros(n, dtype=bool)
        self._camera_center_ray_observation_code = np.zeros(n, dtype=np.int8)
        self._camera_cloud_blocked_fraction = np.full(n, np.nan, dtype=float)
        self._camera_observation_line_codes = np.empty((n, n_bins), dtype=np.int8)
        self._sat_subpoint_lat_deg = np.full(n, np.nan, dtype=float)
        self._sat_subpoint_lon_deg = np.full(n, np.nan, dtype=float)
        self._sat_altitude_m = np.full(n, np.nan, dtype=float)
        self._camera_ground_left_lon_lat_deg = np.full((n, 2), np.nan, dtype=float)
        self._camera_ground_right_lon_lat_deg = np.full((n, 2), np.nan, dtype=float)
        self._camera_ground_center_lon_lat_deg = np.full((n, 2), np.nan, dtype=float)
        self._target_area_intersection_ratio = np.zeros(n, dtype=float)
        self._target_area_novelty_ratio = np.zeros(n, dtype=float)

        # Cloud arc prealloc: use resolved clouds length (§C)
        n_clouds = len(self._clouds)
        self._cloud_arc_radius_km = np.full((n, n_clouds), np.nan, dtype=float)
        self._cloud_arc_start_rad = np.full((n, n_clouds), np.nan, dtype=float)
        self._cloud_arc_end_rad = np.full((n, n_clouds), np.nan, dtype=float)

        # Secondary camera prealloc (§B/§J): allocate only when has_secondary.
        # When has_secondary=False, shape (n, 0) is used (valid sentinel per §J).
        if self._has_secondary and self._n_bins_secondary > 0:
            self._secondary_camera_observation_line_codes = np.empty((n, self._n_bins_secondary), dtype=np.int8)
        else:
            self._secondary_camera_observation_line_codes = np.empty((n, 0), dtype=np.int8)
        self._secondary_camera_cloud_blocked_fraction = np.zeros(n, dtype=float)

        # Secondary camera optics (derived from mount spec)
        self._secondary_vertical_fov_rad: float | None = None
        self._secondary_tilt_rad: float = 0.0
        if self._has_secondary:
            scnd_mount = self._cameras[1]
            self._secondary_vertical_fov_rad = float(
                scnd_mount.camera.fov(axis="y").to(ureg.rad).magnitude
            )
            self._secondary_tilt_rad = float(scnd_mount.tilt_off_nadir.to(ureg.rad).magnitude)

        _, _vf = calculate_fov_angles()
        self._camera_vertical_fov_rad = float(_vf.to(ureg.rad).magnitude)
        self._dt = self._sim_dt_s * ureg.s
        self._camera_pixel_ray_samples = int(camera_pixel_ray_samples)
        self._reward_cfg = reward_config if reward_config is not None else RewardConfig()
        phi_lo_deg, phi_hi_deg = primary_stripe_disk_phi_bounds_deg()
        self._stripe_phi_min_deg = float(phi_lo_deg)
        self._stripe_phi_max_deg = float(phi_hi_deg)
        self._target_area_visited_cells: set[tuple[int, int]] = set()
        self._earth_radius_km = float(r_earth_km)
        self._satellite_altitude = satellite_altitude
        self._metadata = SimulationMetadata(
            orbit_period_s=orbit_period_s,
            omega_rad_s=omega_rad_s,
            sim_total_s=sim_total_s,
            sim_dt_s=self._sim_dt_s,
            theta_start_rad=float(theta_start_rad),
            theta_end_rad=float(theta_end_rad),
            sat_theta_start_rad=float(sat_theta_start_rad),
            sat_theta_span_rad=float(sat_theta_span_rad),
            start_angle_deg=float(start_angle_deg),
            end_angle_deg=float(end_angle_deg),
            controller_mode=self._controller_mode,
            render_mode=self._render_mode,
        )
        self._index = 0
        self._done = False
        self._last_torque_nm = 0.0
        self._populate_camera_and_reward(k=0, prev_omega_wheel=self._state.omega_wheel)

    @property
    def controller_update_interval_steps(self) -> int:
        return self._controller_interval_steps

    @property
    def effective_controller_update_interval_s(self) -> float:
        return self._effective_controller_interval_s

    @property
    def done(self) -> bool:
        return self._done

    @property
    def total_steps(self) -> int:
        return max(0, int(self._t_s.shape[0]) - 1)

    def should_update_controller(self) -> bool:
        return (self._index % self._controller_interval_steps) == 0

    def current_timestep_state(self) -> SimulationTimestepState:
        sat_xy = self._satellite_xy_km(self._index)
        secondary_codes = np.asarray(
            self._secondary_camera_observation_line_codes[self._index], dtype=np.int8
        )
        return SimulationTimestepState(
            step_idx=self._index,
            sim_time_s=float(self._t_s[self._index]),
            sat_pos_xy_km=sat_xy,
            body_z_angle_rad=float(self._body_z_angle_rad[self._index]),
            theta_orbit_rad=float(self._theta_orbit_rad[self._index]),
            radius_km=float(self._radius_km[self._index]),
            omega_sat_rad_s=float(self._state.omega_sat.to(self._ureg.rad / self._ureg.s).magnitude),
            omega_wheel_rad_s=float(self._state.omega_wheel.to(self._ureg.rad / self._ureg.s).magnitude),
            reward=float(self._simulation_reward[self._index]),
            camera_observation_line_codes=np.asarray(
                self._camera_observation_line_codes[self._index], dtype=np.int8
            ),
            camera_center_ray_observation_code=np.int8(
                self._camera_center_ray_observation_code[self._index]
            ),
            secondary_camera_observation_line_codes=secondary_codes,
        )

    def step(self, *, wheel_torque_cmd_nm: float) -> SimulationTimestepState:
        if self._done:
            raise RuntimeError("Cannot step a completed SimulationStepper.")
        self._last_torque_nm = float(wheel_torque_cmd_nm)
        next_idx = self._index + 1
        if next_idx >= self._t_s.shape[0]:
            self._done = True
            return self.current_timestep_state()

        prev_omega_wheel = self._state.omega_wheel
        self._state, _tau_applied = DynamicsKernel.propagate(
            state=self._state,
            wheel_torque_cmd_nm=self._last_torque_nm,
            reaction_wheel=self._reaction_wheel,
            sat_inertia=self._sat_inertia,
            wheel_inertia=self._wheel_inertia,
            dt=self._dt,
            ureg=self._ureg,
        )
        self._index = next_idx
        self._wheel_torque_cmd_nm[self._index] = self._last_torque_nm
        self._body_z_angle_rad[self._index] = float(self._state.theta.to(self._ureg.rad).magnitude)
        self._populate_camera_and_reward(k=self._index, prev_omega_wheel=prev_omega_wheel)
        if self._index >= (self._t_s.shape[0] - 1):
            self._done = True
        return self.current_timestep_state()

    def finalize_series(self) -> SimulationStateSeries:
        return SimulationStateSeries(
            t_s=self._t_s,
            theta_orbit_rad=self._theta_orbit_rad,
            radius_km=self._radius_km,
            body_z_angle_rad=self._body_z_angle_rad,
            simulation_reward=self._simulation_reward,
            wheel_torque_cmd_nm=self._wheel_torque_cmd_nm,
            camera_gsd_m=self._camera_gsd_m,
            camera_vertical_fov_rad=self._camera_vertical_fov_rad,
            camera_ground_left_xy_km=self._camera_ground_left_xy_km,
            camera_ground_right_xy_km=self._camera_ground_right_xy_km,
            camera_ground_center_xy_km=self._camera_ground_center_xy_km,
            camera_center_first_hit_xy_km=self._camera_center_first_hit_xy_km,
            camera_center_first_hit_is_cloud=self._camera_center_first_hit_is_cloud,
            camera_center_ray_observation_code=self._camera_center_ray_observation_code,
            camera_cloud_blocked_fraction=self._camera_cloud_blocked_fraction,
            camera_observation_line_codes=self._camera_observation_line_codes,
            sat_subpoint_lat_deg=self._sat_subpoint_lat_deg,
            sat_subpoint_lon_deg=self._sat_subpoint_lon_deg,
            sat_altitude_m=self._sat_altitude_m,
            camera_ground_left_lon_lat_deg=self._camera_ground_left_lon_lat_deg,
            camera_ground_right_lon_lat_deg=self._camera_ground_right_lon_lat_deg,
            camera_ground_center_lon_lat_deg=self._camera_ground_center_lon_lat_deg,
            target_area_intersection_ratio=self._target_area_intersection_ratio,
            target_area_novelty_ratio=self._target_area_novelty_ratio,
            cloud_arc_radius_km=self._cloud_arc_radius_km,
            cloud_arc_start_rad=self._cloud_arc_start_rad,
            cloud_arc_end_rad=self._cloud_arc_end_rad,
            secondary_camera_observation_line_codes=self._secondary_camera_observation_line_codes,
            secondary_camera_cloud_blocked_fraction=self._secondary_camera_cloud_blocked_fraction,
            secondary_camera_vertical_fov_rad=self._secondary_vertical_fov_rad if self._secondary_vertical_fov_rad is not None else 0.0,
            secondary_camera_tilt_off_nadir_rad=self._secondary_tilt_rad,
            metadata=self._metadata,
        )

    def build_episode_context(self) -> SimulationEpisodeContext:
        configured_interval_s = float(SIMULATION.controller_update_interval.to(self._ureg.s).magnitude)
        return SimulationEpisodeContext(
            simulation_series=self.finalize_series(),
            effective_controller_update_interval_steps=self._controller_interval_steps,
            effective_controller_update_interval_s=self._effective_controller_interval_s,
            configured_controller_update_interval_s=configured_interval_s,
        )

    def _satellite_xy_km(self, k: int) -> np.ndarray:
        """Orbit position in the satellite XY plane used by ``camera_2d`` (Earth disk centered at origin)."""
        return np.array(
            [
                self._radius_km[k] * np.cos(self._theta_orbit_rad[k]),
                self._radius_km[k] * np.sin(self._theta_orbit_rad[k]),
            ],
            dtype=float,
        )

    def _populate_camera_and_reward(self, *, k: int, prev_omega_wheel: Any) -> None:
        sat_pos_xy_km = self._satellite_xy_km(k)
        z_ang = float(self._body_z_angle_rad[k])
        boresight_dir_unit_xy = np.array([np.cos(z_ang), np.sin(z_ang)], dtype=float)

        # Compute secondary boresight from mount tilt (§A)
        secondary_boresight: np.ndarray | None = None
        if self._has_secondary:
            scnd_mount = self._cameras[1]
            tilt_rad = float(scnd_mount.tilt_off_nadir.to(self._ureg.rad).magnitude)
            secondary_boresight = boresight_dir_for_mount(z_ang, tilt_rad)

        sensor = SensorKernel.evaluate(
            sat_pos_xy_km=sat_pos_xy_km,
            boresight_dir_unit_xy=boresight_dir_unit_xy,
            altitude=self._satellite_altitude,
            earth_radius_km=self._earth_radius_km,
            sim_time_s=float(self._t_s[k]),
            sim_total_s=self._sim_total_s,
            n_bins=int(self._camera_observation_line_codes.shape[1]),
            n_clouds=int(self._cloud_arc_radius_km.shape[1]),
            camera_pixel_ray_samples=self._camera_pixel_ray_samples,
            clouds=self._clouds,
            camera_kernel_backend=self._camera_kernel_backend,
            n_bins_secondary=self._n_bins_secondary,
            secondary_boresight_dir_unit_xy=secondary_boresight,
            secondary_vertical_fov_rad=self._secondary_vertical_fov_rad,
        )
        self._camera_gsd_m[k] = sensor.camera_gsd_m
        self._camera_ground_left_xy_km[k, :] = sensor.camera_ground_left_xy_km
        self._camera_ground_right_xy_km[k, :] = sensor.camera_ground_right_xy_km
        self._camera_ground_center_xy_km[k, :] = sensor.camera_ground_center_xy_km
        self._camera_cloud_blocked_fraction[k] = sensor.camera_cloud_blocked_fraction
        self._camera_center_ray_observation_code[k] = sensor.camera_center_ray_observation_code
        self._camera_center_first_hit_is_cloud[k] = sensor.camera_center_first_hit_is_cloud
        self._camera_center_first_hit_xy_km[k, :] = sensor.camera_center_first_hit_xy_km
        self._camera_observation_line_codes[k, :] = sensor.camera_observation_line_codes
        self._cloud_arc_radius_km[k, :] = sensor.cloud_arc_radius_km
        self._cloud_arc_start_rad[k, :] = sensor.cloud_arc_start_rad
        self._cloud_arc_end_rad[k, :] = sensor.cloud_arc_end_rad

        if self._has_secondary and self._n_bins_secondary > 0:
            self._secondary_camera_observation_line_codes[k, :] = sensor.secondary_camera_observation_line_codes
            self._secondary_camera_cloud_blocked_fraction[k] = sensor.secondary_camera_cloud_blocked_fraction

        lon_sp_deg, lat_sp_deg = disk_xy_km_to_geodetic_deg(sat_pos_xy_km, ell=WGS84_ELLIPSOID)
        if not np.all(np.isfinite(sensor.camera_ground_center_xy_km)):
            left_lon_lat = np.array([np.nan, np.nan], dtype=float)
            right_lon_lat = np.array([np.nan, np.nan], dtype=float)
            center_lon_lat = np.array([np.nan, np.nan], dtype=float)
        else:
            lon_l, lat_l = disk_xy_km_to_geodetic_deg(sensor.camera_ground_left_xy_km, ell=WGS84_ELLIPSOID)
            lon_r, lat_r = disk_xy_km_to_geodetic_deg(sensor.camera_ground_right_xy_km, ell=WGS84_ELLIPSOID)
            lon_c, lat_c = disk_xy_km_to_geodetic_deg(sensor.camera_ground_center_xy_km, ell=WGS84_ELLIPSOID)
            left_lon_lat = np.array([lon_l, lat_l], dtype=float)
            right_lon_lat = np.array([lon_r, lat_r], dtype=float)
            center_lon_lat = np.array([lon_c, lat_c], dtype=float)
        sat_lat_deg = float(lat_sp_deg)
        sat_lon_deg = float(lon_sp_deg)
        self._sat_subpoint_lat_deg[k] = sat_lat_deg
        self._sat_subpoint_lon_deg[k] = sat_lon_deg
        self._sat_altitude_m[k] = float(self._satellite_altitude.to(self._ureg.m).magnitude)
        self._camera_ground_left_lon_lat_deg[k, :] = left_lon_lat
        self._camera_ground_right_lon_lat_deg[k, :] = right_lon_lat
        self._camera_ground_center_lon_lat_deg[k, :] = center_lon_lat
        footprint_lr_xy_ok = np.all(np.isfinite(sensor.camera_ground_left_xy_km)) and np.all(
            np.isfinite(sensor.camera_ground_right_xy_km)
        )
        if footprint_lr_xy_ok:
            intersection_ratio = circle_stripe_footprint_overlap_ratio(
                footprint_left_xy_km=sensor.camera_ground_left_xy_km,
                footprint_right_xy_km=sensor.camera_ground_right_xy_km,
                stripe_angle_start_deg=float(self._stripe_phi_min_deg),
                stripe_angle_end_deg=float(self._stripe_phi_max_deg),
            )
        else:
            intersection_ratio = 0.0
        self._target_area_intersection_ratio[k] = float(intersection_ratio)
        if intersection_ratio > 0.0:
            center_lat_deg = float(center_lon_lat[1])
            if np.isfinite(center_lat_deg):
                cell_lat = int(np.floor(center_lat_deg * 10.0))
            else:
                cell_lat = 0
            cell = (cell_lat, 0)
            if cell in self._target_area_visited_cells:
                novelty_ratio = 0.0
            else:
                novelty_ratio = float(intersection_ratio)
                self._target_area_visited_cells.add(cell)
        else:
            novelty_ratio = 0.0
        self._target_area_novelty_ratio[k] = novelty_ratio
        # Use first resolved target_area for reward (§I)
        _target_area = OBSERVATION_TARGET_AREAS[0]
        self._simulation_reward[k] = RewardKernel.evaluate(
            sat_pos_xy_km=sat_pos_xy_km,
            sat_subpoint_lat_deg=float(sat_lat_deg),
            sat_subpoint_lon_deg=float(sat_lon_deg),
            target_area_intersection_ratio=float(intersection_ratio),
            target_area_novelty_ratio=float(novelty_ratio),
            camera_observation_line_codes=sensor.camera_observation_line_codes,
            camera_cloud_blocked_fraction=float(sensor.camera_cloud_blocked_fraction)
            if np.isfinite(sensor.camera_cloud_blocked_fraction)
            else 0.0,
            secondary_camera_cloud_blocked_fraction=float(sensor.secondary_camera_cloud_blocked_fraction),
            wheel_inertia=self._wheel_inertia,
            omega_before=prev_omega_wheel,
            omega_after=self._state.omega_wheel,
            reward_config=self._reward_cfg,
            ureg=self._ureg,
            target_area=_target_area,
        )


def run_baseline_rollout_from_stepper(
    stepper: SimulationStepper,
    *,
    simulation_config: SimulationConfig,
    tau_max_nm: float,
    show_progress: bool = True,
) -> SimulationStateSeries:
    """Run the baseline/random/coast controller loop on an already-constructed stepper.

    Extracted from run_baseline_rollout so that callers can construct the stepper
    via build_stepper(resolved, ...) and then call this loop independently.

    Args:
        stepper: A freshly-constructed SimulationStepper.
        simulation_config: Must have controller_mode in _BASELINE_CONTROLLER_MODES.
        tau_max_nm: Reaction wheel max torque in N·m (from resolved.satellite or constants).
        show_progress: Whether to render a tqdm progress bar.
    """
    if simulation_config.controller_mode not in _BASELINE_CONTROLLER_MODES:
        raise ValueError(
            f"run_baseline_rollout_from_stepper supports {_BASELINE_CONTROLLER_MODES} controller_mode only."
        )
    controller = _build_simulation_controller(
        controller_mode=str(simulation_config.controller_mode),
        tau_max_nm=tau_max_nm,
        dt=stepper._dt,
        rng=np.random.default_rng(simulation_config.controller_seed),
    )
    controller_obs = np.zeros(1, dtype=np.float64)
    torque_cmd_nm = 0.0
    total_steps = max(0, int(stepper._t_s.shape[0]) - 1)
    with tqdm(
        total=total_steps,
        desc="Running simulation",
        unit="step",
        disable=(not show_progress),
    ) as pbar:
        while not stepper.done:
            if stepper.should_update_controller():
                action = controller.get_action(controller_obs, train=False)
                torque_cmd_nm = float(np.asarray(action, dtype=np.float64).reshape(-1)[0])
            stepper.step(wheel_torque_cmd_nm=torque_cmd_nm)
            if pbar.n < total_steps:
                pbar.update(1)
    return stepper.finalize_series()


def run_baseline_rollout(
    *,
    simulation_config: SimulationConfig,
    earth_radius: Any,
    earth_gravitational_parameter: Any,
    satellite: Any,
    satellite_altitude: Any,
    theta_center_rad: float,
    start_angle_deg: float,
    end_angle_deg: float,
    sat_motion_span_scale: float,
    sat_z_offset_deg: float,
    ureg: Any,
    camera_pixel_ray_samples: int = 96,
    camera_observation_line_n_bins: int | None = None,
    reward_config: RewardConfig | None = None,
    show_progress: bool = True,
) -> SimulationStateSeries:
    if simulation_config.controller_mode not in _BASELINE_CONTROLLER_MODES:
        raise ValueError(f"run_baseline_rollout supports {_BASELINE_CONTROLLER_MODES} controller_mode only.")
    stepper = SimulationStepper(
        simulation_config=simulation_config,
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
    tau_max_nm = float(satellite.reaction_wheel_max_torque.to(ureg.N * ureg.m).magnitude)
    return run_baseline_rollout_from_stepper(
        stepper,
        simulation_config=simulation_config,
        tau_max_nm=tau_max_nm,
        show_progress=show_progress,
    )
