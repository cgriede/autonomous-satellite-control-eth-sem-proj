from __future__ import annotations

from typing import Any

import numpy as np

from autonomous_control.reward import RewardConfig, RewardSignals, canonical_reward
from environment_definition.constants.SIMULATION import (
    FIXED_GROUND_CONE_HIT_EARTH,
    OBSERVATION_LINE_NOT_COMPUTED,
    SIMULATION,
)

from .attitude_dynamics import AttitudeState2D, propagate_reaction_wheel_attitude_2d
from .camera_2d import (
    OBSERVATION_EARTH,
    OBSERVATION_SPACE,
    OBSERVATION_TARGET,
    calculate_fov_angles,
    compute_cloud_arc_specs_at_time,
    simulate_camera_observation_line_1d,
    simulate_camera_strip_2d,
)
from .reaction_wheel import ReactionWheel
from .state_types import SimulationMetadata, SimulationStateSeries


def _controller_agent_placeholder_step(*, frame_index: int, sim_time_s: float) -> None:
    """
    Reserved hook for a future controller agent (e.g. torque commands).
    Reaction-wheel torque is currently fixed inside the attitude update above.
    """
    del frame_index, sim_time_s


def _fixed_ground_codes_from_observation_line(
    observation_codes: np.ndarray,
    rel_angles_rad: np.ndarray,
    center_ray_code: np.int8,
) -> np.ndarray:
    fixed_codes = np.asarray(observation_codes, dtype=np.int8).copy()
    if fixed_codes.ndim != 1:
        raise ValueError("observation_codes must be a 1D array.")
    if rel_angles_rad.shape != fixed_codes.shape:
        raise ValueError("rel_angles_rad shape must match observation_codes shape.")

    fixed_codes[fixed_codes == np.int8(OBSERVATION_SPACE)] = np.int8(OBSERVATION_EARTH)

    if int(center_ray_code) == int(OBSERVATION_EARTH):
        center_idx = int(np.argmin(np.abs(np.asarray(rel_angles_rad, dtype=float))))
        fixed_codes[center_idx] = np.int8(FIXED_GROUND_CONE_HIT_EARTH)
    return fixed_codes


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
    observer_target_angle_rad: float,
    camera_pixel_ray_samples: int = 96,
    camera_observation_line_n_bins: int | None = None,
    reward_config: RewardConfig | None = None,
) -> SimulationStateSeries:
    """
    Canonical numeric simulation entrypoint for rendering runs.

    Per timestep (conceptually): plant (orbit + reaction-wheel attitude) → camera
    raytracing (strip + 1D observation line) → controller placeholder.

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

    n = int(num_frames)
    n_bins = (
        int(camera_observation_line_n_bins)
        if camera_observation_line_n_bins is not None
        else int(SIMULATION.camera_observation_line_n_bins)
    )
    if n_bins < 1:
        raise ValueError("camera_observation_line_n_bins must be >= 1.")

    body_z_angle_rad = np.empty(n, dtype=float)
    body_z_angle_rad[0] = state.theta.to(ureg.rad).magnitude
    simulation_reward = np.empty(n, dtype=float)

    camera_gsd_m = np.full(n, np.nan, dtype=float)
    camera_ground_left_xy_km = np.full((n, 2), np.nan, dtype=float)
    camera_ground_right_xy_km = np.full((n, 2), np.nan, dtype=float)
    camera_ground_center_xy_km = np.full((n, 2), np.nan, dtype=float)
    camera_center_first_hit_xy_km = np.full((n, 2), np.nan, dtype=float)
    camera_center_first_hit_is_cloud = np.zeros(n, dtype=bool)
    camera_center_ray_observation_code = np.zeros(n, dtype=np.int8)
    camera_cloud_blocked_fraction = np.full(n, np.nan, dtype=float)
    camera_observation_line_codes = np.empty((n, n_bins), dtype=np.int8)
    fixed_ground_line_codes = np.full((n, n_bins), OBSERVATION_LINE_NOT_COMPUTED, dtype=np.int8)

    n_clouds = len(SIMULATION.clouds)
    cloud_arc_radius_km = np.full((n, n_clouds), np.nan, dtype=float)
    cloud_arc_start_rad = np.full((n, n_clouds), np.nan, dtype=float)
    cloud_arc_end_rad = np.full((n, n_clouds), np.nan, dtype=float)

    _, _vf = calculate_fov_angles()
    camera_vertical_fov_rad = float(_vf.to(ureg.rad).magnitude)

    dt = sim_dt_s * ureg.s
    target_angle_rad = float(observer_target_angle_rad)
    reward_cfg = reward_config if reward_config is not None else RewardConfig()

    target_xy_km = np.array(
        [
            r_earth_km * np.cos(target_angle_rad),
            r_earth_km * np.sin(target_angle_rad),
        ],
        dtype=float,
    )
    prev_omega_wheel = state.omega_wheel

    for k in range(n):
        if k > 0:
            prev_omega_wheel = state.omega_wheel
            tau_applied = reaction_wheel.compute_applied_torque(state=state, tau_cmd=wheel_torque_cmd)
            state = propagate_reaction_wheel_attitude_2d(
                state=state,
                wheel_torque=tau_applied,
                sat_inertia=sat_inertia,
                wheel_inertia=wheel_inertia,
                dt=dt,
            )
            body_z_angle_rad[k] = state.theta.to(ureg.rad).magnitude

        sat_pos_xy_km = np.array(
            [
                radius_km[k] * np.cos(theta_orbit_rad[k]),
                radius_km[k] * np.sin(theta_orbit_rad[k]),
            ],
            dtype=float,
        )
        z_ang = float(body_z_angle_rad[k])
        boresight_dir_unit_xy = np.array([np.cos(z_ang), np.sin(z_ang)], dtype=float)

        cam = simulate_camera_strip_2d(
            sat_pos_xy_km=sat_pos_xy_km,
            boresight_dir_unit_xy=boresight_dir_unit_xy,
            altitude=satellite_altitude,
            earth_radius_km=r_earth_km,
            sim_time_s=float(t_s[k]),
            sim_total_s=sim_total_s,
            pixel_ray_samples=int(camera_pixel_ray_samples),
        )
        camera_gsd_m[k] = float(cam.gsd_m)
        camera_ground_left_xy_km[k, :] = cam.ground_left_xy_km
        camera_ground_right_xy_km[k, :] = cam.ground_right_xy_km
        camera_ground_center_xy_km[k, :] = cam.ground_center_xy_km
        camera_cloud_blocked_fraction[k] = float(cam.cloud_blocked_fraction)
        camera_center_ray_observation_code[k] = np.int8(cam.center_ray_observation_code)
        camera_center_first_hit_is_cloud[k] = bool(cam.center_first_hit_is_cloud)
        if cam.center_first_hit_xy_km is not None:
            camera_center_first_hit_xy_km[k, :] = np.asarray(cam.center_first_hit_xy_km, dtype=float)

        line_res = simulate_camera_observation_line_1d(
            sat_pos_xy_km=sat_pos_xy_km,
            boresight_dir_unit_xy=boresight_dir_unit_xy,
            altitude=satellite_altitude,
            earth_radius_km=r_earth_km,
            sim_time_s=float(t_s[k]),
            sim_total_s=sim_total_s,
            target_angle_rad=target_angle_rad,
            n_bins=n_bins,
        )
        camera_observation_line_codes[k, :] = line_res.observation_types
        target_visible = bool(np.any(line_res.observation_types == np.int8(OBSERVATION_TARGET)))
        distance_to_target_km = float(np.linalg.norm(sat_pos_xy_km - target_xy_km))
        signals = RewardSignals(
            distance_to_target=distance_to_target_km * ureg.km,
            picture_taken=True,
            target_visible=target_visible,
            wheel_inertia=wheel_inertia,
            omega_before=prev_omega_wheel,
            omega_after=state.omega_wheel,
        )
        reward_total, _ = canonical_reward(signals=signals, cfg=reward_cfg)
        simulation_reward[k] = float(reward_total)
        fixed_ground_line_codes[k, :] = _fixed_ground_codes_from_observation_line(
            observation_codes=line_res.observation_types,
            rel_angles_rad=line_res.bin_ray_angles_rel_boresight_rad,
            center_ray_code=camera_center_ray_observation_code[k],
        )

        for i, spec in enumerate(
            compute_cloud_arc_specs_at_time(
                sim_time_s=float(t_s[k]),
                sim_total_s=sim_total_s,
                earth_radius_km=r_earth_km,
            )
        ):
            cloud_arc_radius_km[k, i] = float(spec["radius_km"])
            cloud_arc_start_rad[k, i] = float(spec["start_rad"])
            cloud_arc_end_rad[k, i] = float(spec["end_rad"])

        _controller_agent_placeholder_step(frame_index=k, sim_time_s=float(t_s[k]))

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
        simulation_reward=simulation_reward,
        camera_gsd_m=camera_gsd_m,
        camera_vertical_fov_rad=float(camera_vertical_fov_rad),
        camera_ground_left_xy_km=camera_ground_left_xy_km,
        camera_ground_right_xy_km=camera_ground_right_xy_km,
        camera_ground_center_xy_km=camera_ground_center_xy_km,
        camera_center_first_hit_xy_km=camera_center_first_hit_xy_km,
        camera_center_first_hit_is_cloud=camera_center_first_hit_is_cloud,
        camera_center_ray_observation_code=camera_center_ray_observation_code,
        camera_cloud_blocked_fraction=camera_cloud_blocked_fraction,
        camera_observation_line_codes=camera_observation_line_codes,
        fixed_ground_line_codes=fixed_ground_line_codes,
        cloud_arc_radius_km=cloud_arc_radius_km,
        cloud_arc_start_rad=cloud_arc_start_rad,
        cloud_arc_end_rad=cloud_arc_end_rad,
        metadata=metadata,
    )
