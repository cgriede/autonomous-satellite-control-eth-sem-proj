import json
import time
from pathlib import Path
from typing import Self

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation as mpl_animation
from matplotlib.animation import FuncAnimation
from tqdm import tqdm

from environment_definition.constants import (
    EARTH_RADIUS,
    N_PIXELS_Y,
    RenderMode,
    RENDER,
    SIMULATION,
    UREG as ureg,
)
from environment_definition.constants.MISSION import los_theta_offsets_deg
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE, SATELLITE_ALTITUDE
from simulation.camera_2d import boresight_dir_for_mount
from simulation.capture_reward import (
    applied_capture_reward_series,
    captured_target_indices_at_step,
    latent_capture_reward_series,
)
from simulation.state_types import SimulationStateSeries
from utils.geometry.mission_stripe_disk import (
    primary_stripe_midpoint_disk_xy_km_on_sphere,
    primary_stripe_disk_phi_bounds_deg,
)
from utils.video_archive import archive_existing_video

if __package__:
    from ._closeup_view import build_closeup_panel, update_closeup_panel
    from ._controls import RenderControls, build_controls_panel
    from ._main_view import build_main_panel, update_main_panel
    from ._reward_plot import build_reward_panel, update_reward_panel
    from ._torque_plot import build_torque_panel, update_torque_panel
    from ._pointing_plot import build_pointing_panel, update_pointing_panel
    from ._capture_plot import build_capture_panel, update_capture_panel
    from ._satellite_cam_view import build_1d_sat_view, update_1d_sat_view
    from ._telemetry import build_telemetry_panel, update_telemetry_panel
    from .episode_series_plotting import (
        agent_pointing_offnadir_deg_for_plot,
        series_uses_obc_pointing,
        torque_agent_series_for_plot,
    )
else:
    from render._closeup_view import build_closeup_panel, update_closeup_panel
    from render._controls import RenderControls, build_controls_panel
    from render._main_view import build_main_panel, update_main_panel
    from render._reward_plot import build_reward_panel, update_reward_panel
    from render._torque_plot import build_torque_panel, update_torque_panel
    from render._pointing_plot import build_pointing_panel, update_pointing_panel
    from render._capture_plot import build_capture_panel, update_capture_panel
    from render._satellite_cam_view import build_1d_sat_view, update_1d_sat_view
    from render._telemetry import build_telemetry_panel, update_telemetry_panel
    from render.episode_series_plotting import (
        agent_pointing_offnadir_deg_for_plot,
        series_uses_obc_pointing,
        torque_agent_series_for_plot,
    )


SHOW_MAIN_PLOT = True
SHOW_1D_SAT_VIEW = True
SHOW_1D_SAT_VIEW_SECONDARY = True
SHOW_CLOSEUP = True
SHOW_TELEMETRY = True
SHOW_REWARD_PLOT = True
SHOW_TORQUE_PLOT = True
SHOW_POINTING_PLOT = True
SHOW_CAPTURE_PLOT = True

R_EARTH_KM = EARTH_RADIUS.to(ureg.km).magnitude
SAT_ALTITUDE_KM = SATELLITE_ALTITUDE.to(ureg.km).magnitude
R_ORBIT_KM = R_EARTH_KM + SAT_ALTITUDE_KM
THETA_CENTER = SIMULATION.theta_center.to(ureg.rad).magnitude
MARGIN_DEG = SIMULATION.contact_margin_angle.to(ureg.deg).magnitude
START_ANGLE_DEG, END_ANGLE_DEG = los_theta_offsets_deg(
    orbit_height=SATELLITE_ALTITUDE,
    margin_deg=float(MARGIN_DEG),
)
ANIMATION_INTERVAL_MS = RENDER.animation_interval.to(ureg.ms).magnitude
SIM_SPEED_MULTIPLIER = float(RENDER.default_speed_multiplier)
SIMULATION_SERIES: SimulationStateSeries | None = None
N_CLOUDS = 0
N_BINS = 0
N_BINS_SECONDARY = 0
STATIC_SCENE: dict[str, object] = {}
FIG: plt.Figure | None = None
SIM_TIME_S = 0.0
PANELS: dict[str, dict] = {}
CONTROLS = RenderControls(sim_speed_multiplier=SIM_SPEED_MULTIPLIER)
CONTROL_ARTISTS: dict | None = None


def export_canvas_geometry() -> tuple[float, float, int, int]:
    """Export pixel size: ``figure_size`` at ``export_dpi`` (matches legacy FFMpegWriter)."""
    w_in, h_in = float(RENDER.figure_size[0]), float(RENDER.figure_size[1])
    dpi = int(RENDER.export_dpi)
    return w_in, h_in, int(round(w_in * dpi)), int(round(h_in * dpi))


def _require_runtime() -> SimulationStateSeries:
    if SIMULATION_SERIES is None:
        raise RuntimeError("Renderer runtime has not been configured with simulation data.")
    return SIMULATION_SERIES


def _island_phi_bounds_deg_from_series(simulation_series: SimulationStateSeries) -> list[tuple[float, float]]:
    """Angular wedge on the orbit disk covering targets and cloud arcs (main-view island gimmick)."""
    meta = simulation_series.metadata
    intervals: list[tuple[float, float]] = []
    if meta.target_region_bounds_deg:
        intervals.extend((float(lo), float(hi)) for lo, hi in meta.target_region_bounds_deg)
    else:
        intervals.append(primary_stripe_disk_phi_bounds_deg())

    cloud_starts = simulation_series.cloud_arc_start_rad
    cloud_ends = simulation_series.cloud_arc_end_rad
    if cloud_starts.size > 0:
        starts_deg = np.rad2deg(cloud_starts)
        ends_deg = np.rad2deg(cloud_ends)
        valid = np.isfinite(starts_deg) & np.isfinite(ends_deg)
        if valid.any():
            intervals.append((float(np.min(starts_deg[valid])), float(np.max(ends_deg[valid]))))

    if not intervals:
        return []

    pad_deg = float(RENDER.island_phi_pad_deg)
    lo_deg = min(a for a, _ in intervals) - pad_deg
    hi_deg = max(b for _, b in intervals) + pad_deg
    return [(lo_deg, hi_deg)]


def _configure_runtime_from_series(simulation_series: SimulationStateSeries) -> None:
    global SIMULATION_SERIES, N_CLOUDS, N_BINS, N_BINS_SECONDARY, STATIC_SCENE, CONTROLS, FIG, PANELS, CONTROL_ARTISTS
    SIMULATION_SERIES = simulation_series
    N_CLOUDS = int(SIMULATION_SERIES.cloud_arc_radius_km.shape[1])
    N_BINS = int(SIMULATION_SERIES.camera_observation_line_codes.shape[1])
    N_BINS_SECONDARY = int(SIMULATION_SERIES.secondary_camera_observation_line_codes.shape[1])
    # Main-panel framing: symmetric LOS window ∪ actual orbit-plane sweep so the big
    # cross-section is never clipped when the episode arc extends past LOS margins.
    theta_rel = np.arctan2(
        np.sin(simulation_series.theta_orbit_rad - THETA_CENTER),
        np.cos(simulation_series.theta_orbit_rad - THETA_CENTER),
    )
    traj_off_deg_lo = float(np.rad2deg(np.min(theta_rel)))
    traj_off_deg_hi = float(np.rad2deg(np.max(theta_rel)))
    frame_lo_deg = min(START_ANGLE_DEG, END_ANGLE_DEG, traj_off_deg_lo, traj_off_deg_hi)
    frame_hi_deg = max(START_ANGLE_DEG, END_ANGLE_DEG, traj_off_deg_lo, traj_off_deg_hi)
    meta = simulation_series.metadata
    region_bounds = meta.target_region_bounds_deg
    if region_bounds:
        tgt_lo_deg = min(lo for lo, _ in region_bounds)
        tgt_hi_deg = max(hi for _, hi in region_bounds)
        if meta.view_anchor_xy_km is not None:
            view_anchor_xy = np.asarray(meta.view_anchor_xy_km, dtype=float)
        else:
            view_anchor_xy = primary_stripe_midpoint_disk_xy_km_on_sphere(earth_radius_km=R_EARTH_KM)
    else:
        tgt_lo_deg, tgt_hi_deg = primary_stripe_disk_phi_bounds_deg()
        view_anchor_xy = primary_stripe_midpoint_disk_xy_km_on_sphere(earth_radius_km=R_EARTH_KM)
    STATIC_SCENE = {
        "R_earth": R_EARTH_KM,
        "R_orbit": R_ORBIT_KM,
        "theta_center": THETA_CENTER,
        "start_angle_deg": frame_lo_deg,
        "end_angle_deg": frame_hi_deg,
        "target_region_start_angle_deg": float(tgt_lo_deg),
        "target_region_end_angle_deg": float(tgt_hi_deg),
        "target_region_bounds_deg": list(region_bounds) if region_bounds else None,
        "island_phi_bounds_deg": _island_phi_bounds_deg_from_series(simulation_series),
        "view_anchor_x": float(view_anchor_xy[0]),
        "view_anchor_y": float(view_anchor_xy[1]),
        "view_anchor_pos": np.asarray(view_anchor_xy, dtype=float),
        "cloud_models": [None] * N_CLOUDS,
        "n_clouds": N_CLOUDS,
        "n_bins": N_BINS,
        "n_bins_secondary": N_BINS_SECONDARY,
        "controller_mode": SIMULATION_SERIES.metadata.controller_mode,
    }
    CONTROLS = RenderControls(sim_speed_multiplier=SIM_SPEED_MULTIPLIER)
    FIG = plt.figure(figsize=RENDER.figure_size, facecolor=RENDER.space_background)
    PANELS = {}
    CONTROL_ARTISTS = None


def _baseline_shutter_steps(sim_series: SimulationStateSeries) -> tuple[int, ...]:
    steps = sim_series.metadata.baseline_shutter_cmd_steps
    if not steps:
        return ()
    return tuple(int(s) for s in steps)


def _take_picture_cmd_steps(sim_series: SimulationStateSeries) -> tuple[int, ...]:
    meta = sim_series.metadata
    if meta.take_picture_cmd_steps:
        return tuple(int(s) for s in meta.take_picture_cmd_steps)
    baseline = _baseline_shutter_steps(sim_series)
    if baseline:
        return baseline
    cmd = sim_series.baseline_take_picture_cmd
    if cmd is not None:
        return tuple(int(i) for i in np.flatnonzero(np.asarray(cmd, dtype=bool)))
    return ()


def _take_picture_cmd_times_s(sim_series: SimulationStateSeries) -> tuple[float, ...]:
    steps = _take_picture_cmd_steps(sim_series)
    if not steps:
        return ()
    t_s = np.asarray(sim_series.t_s, dtype=float)
    return tuple(float(t_s[int(k)]) for k in steps if 0 <= int(k) < t_s.shape[0])


def _shutter_cmd_active(sim_idx: int, shutter_steps: tuple[int, ...], *, tol_steps: int = 3) -> bool:
    if not shutter_steps:
        return False
    k = int(sim_idx)
    return any(abs(k - int(s)) <= int(tol_steps) for s in shutter_steps)


def _cloud_world_xy_for_frame(sim_idx: int) -> list[dict[str, np.ndarray]]:
    sim_series = _require_runtime()
    specs: list[dict[str, np.ndarray]] = []
    radii = sim_series.cloud_arc_radius_km[sim_idx]
    starts = sim_series.cloud_arc_start_rad[sim_idx]
    ends = sim_series.cloud_arc_end_rad[sim_idx]
    for i in range(N_CLOUDS):
        r = float(radii[i])
        s = float(starts[i])
        e = float(ends[i])
        if not (np.isfinite(r) and np.isfinite(s) and np.isfinite(e)):
            specs.append({"x": np.array([], dtype=float), "y": np.array([], dtype=float)})
            continue
        th = np.linspace(s, e, int(RENDER.cloud_segment_points), dtype=float)
        specs.append({"x": r * np.cos(th), "y": r * np.sin(th)})
    return specs


def simulation_index_from_time(sim_time_s: float, wrap_orbit: bool = True) -> int:
    sim_series = _require_runtime()
    sim_total_s = float(sim_series.metadata.sim_total_s)
    if wrap_orbit:
        normalized = (sim_time_s / sim_total_s) % 1.0
    else:
        normalized = np.clip(sim_time_s / sim_total_s, 0.0, 1.0)
    return int(np.floor(normalized * (sim_series.t_s.shape[0] - 1)))


def _set_time_from_index(sim_idx: int) -> None:
    global SIM_TIME_S
    sim_series = _require_runtime()
    n = int(sim_series.t_s.shape[0])
    clamped_idx = int(np.clip(sim_idx, 0, max(0, n - 1)))
    SIM_TIME_S = float(sim_series.t_s[clamped_idx])


def _refresh_current_scene() -> None:
    sim_idx = simulation_index_from_time(SIM_TIME_S, wrap_orbit=False)
    scene = sample_scene(sim_idx)
    update_panels(scene)
    if FIG is not None:
        FIG.canvas.draw_idle()


def _step_backward_one_frame() -> None:
    current_idx = simulation_index_from_time(SIM_TIME_S, wrap_orbit=False)
    new_idx = max(0, current_idx - 1)
    _set_time_from_index(new_idx)
    _refresh_current_scene()


def _step_forward_one_frame() -> None:
    n = int(_require_runtime().t_s.shape[0])
    current_idx = simulation_index_from_time(SIM_TIME_S, wrap_orbit=False)
    new_idx = min(n - 1, current_idx + 1)
    _set_time_from_index(new_idx)
    _refresh_current_scene()


def sample_scene(sim_idx: int) -> dict:
    sim_series = _require_runtime()
    idx_theta = float(sim_series.theta_orbit_rad[sim_idx])
    r_orbit_km = float(sim_series.radius_km[sim_idx])
    sat_pos = np.array([r_orbit_km * np.cos(idx_theta), r_orbit_km * np.sin(idx_theta)], dtype=float)

    z_angle = float(sim_series.body_z_angle_rad[sim_idx])
    z_axis_dir = np.array([np.cos(z_angle), np.sin(z_angle)], dtype=float)

    # build trail from orbit-plane XY (matches ``camera_2d`` Earth-disk kinematics)
    k = max(sim_idx + 1, 2)
    tx = []
    ty = []
    for i in range(k):
        th = float(sim_series.theta_orbit_rad[i])
        rk = float(sim_series.radius_km[i])
        p = np.array([rk * np.cos(th), rk * np.sin(th)], dtype=float)
        tx.append(p[0])
        ty.append(p[1])
    trail_xy = (np.asarray(tx, dtype=float), np.asarray(ty, dtype=float))

    cone_len = float(SIMULATION.cone_length.to(ureg.km).magnitude * RENDER.cone_length_render_scale)
    cone_half = float(sim_series.camera_vertical_fov_rad / 2.0)
    cos_h, sin_h = np.cos(cone_half), np.sin(cone_half)
    rot_l = np.array([[cos_h, -sin_h], [sin_h, cos_h]], dtype=float)
    rot_r = np.array([[cos_h, sin_h], [-sin_h, cos_h]], dtype=float)
    edge_l = sat_pos + cone_len * (rot_l @ z_axis_dir)
    edge_r = sat_pos + cone_len * (rot_r @ z_axis_dir)

    camera_gsd_m = float(sim_series.camera_gsd_m[sim_idx])
    camera_image_smear_px = float(sim_series.camera_image_smear_px[sim_idx])
    camera_image_quality = float(sim_series.camera_image_quality[sim_idx])
    camera_swath_height_km = (N_PIXELS_Y * camera_gsd_m) / 1000.0 if np.isfinite(camera_gsd_m) else float("nan")
    blocked_fraction = float(sim_series.camera_cloud_blocked_fraction[sim_idx])
    center_first_hit_xy_km = np.asarray(sim_series.camera_center_first_hit_xy_km[sim_idx], dtype=float)
    ground_center_xy = np.asarray(sim_series.camera_ground_center_xy_km[sim_idx], dtype=float)
    ground_left_xy = np.asarray(sim_series.camera_ground_left_xy_km[sim_idx], dtype=float)
    ground_right_xy = np.asarray(sim_series.camera_ground_right_xy_km[sim_idx], dtype=float)

    nadir_angle = float(sim_series.theta_orbit_rad[sim_idx]) + np.pi
    z_angle_rel_nadir_rad = np.arctan2(np.sin(z_angle - nadir_angle), np.cos(z_angle - nadir_angle))
    view_anchor_x = float(STATIC_SCENE["view_anchor_x"])
    view_anchor_y = float(STATIC_SCENE["view_anchor_y"])
    active_target_idx = -1
    if sim_series.baseline_view_anchor_xy_km is not None:
        anchor_xy = np.asarray(sim_series.baseline_view_anchor_xy_km[sim_idx], dtype=float)
        if np.all(np.isfinite(anchor_xy)):
            view_anchor_x = float(anchor_xy[0])
            view_anchor_y = float(anchor_xy[1])
    if sim_series.baseline_active_target_idx is not None:
        active_target_idx = int(sim_series.baseline_active_target_idx[sim_idx])
    sat_to_view_anchor = np.array([view_anchor_x, view_anchor_y], dtype=float) - sat_pos
    los_angle = float(np.arctan2(sat_to_view_anchor[1], sat_to_view_anchor[0]))
    los_rel_nadir_rad = np.arctan2(np.sin(los_angle - nadir_angle), np.cos(los_angle - nadir_angle))

    if np.isnan(center_first_hit_xy_km).any():
        intersection_text = "none"
    else:
        hit_type = "cloud" if bool(sim_series.camera_center_first_hit_is_cloud[sim_idx]) else "earth"
        hit_distance_km = float(np.linalg.norm(center_first_hit_xy_km - sat_pos))
        intersection_text = f"{hit_distance_km:.1f} km ({hit_type})"

    if np.isnan(ground_center_xy).any():
        ground_patch_hit_text = "none"
    else:
        ground_patch_hit_text = f"x={ground_center_xy[0]:.1f} km, y={ground_center_xy[1]:.1f} km"

    dt_s = float(sim_series.metadata.sim_dt_s)
    if sim_idx > 0 and dt_s > 0.0:
        raw_delta = float(sim_series.body_z_angle_rad[sim_idx] - sim_series.body_z_angle_rad[sim_idx - 1])
        wrapped_delta = float(np.arctan2(np.sin(raw_delta), np.cos(raw_delta)))
        body_spin_deg_s = float(np.rad2deg(wrapped_delta / dt_s))
    else:
        body_spin_deg_s = 0.0

    sat_body_rotation_rate_label = f"{body_spin_deg_s:+.2f} deg/s"

    # Secondary camera cone edges (degenerate/invisible when no secondary camera configured).
    sec_fov_rad = float(sim_series.secondary_camera_vertical_fov_rad)
    sec_tilt_rad = float(sim_series.secondary_camera_tilt_off_nadir_rad)
    if sec_fov_rad > 0.0:
        sec_boresight = boresight_dir_for_mount(z_angle, sec_tilt_rad)
        sec_half = sec_fov_rad / 2.0
        cos_s, sin_s = np.cos(sec_half), np.sin(sec_half)
        rot_sl = np.array([[cos_s, -sin_s], [sin_s, cos_s]], dtype=float)
        rot_sr = np.array([[cos_s, sin_s], [-sin_s, cos_s]], dtype=float)
        sec_edge_l = sat_pos + cone_len * (rot_sl @ sec_boresight)
        sec_edge_r = sat_pos + cone_len * (rot_sr @ sec_boresight)
    else:
        sec_edge_l = sat_pos.copy()
        sec_edge_r = sat_pos.copy()

    secondary_codes: np.ndarray | None = None
    if N_BINS_SECONDARY > 0:
        secondary_codes = np.asarray(sim_series.secondary_camera_observation_line_codes[sim_idx], dtype=np.int8)

    cmd_steps = _take_picture_cmd_steps(sim_series)
    captured_target_indices = captured_target_indices_at_step(
        sim_series, sim_idx, cmd_steps=cmd_steps
    )

    sat_subpoint_lat_deg = float(sim_series.sat_subpoint_lat_deg[sim_idx])
    sat_subpoint_lon_deg = float(sim_series.sat_subpoint_lon_deg[sim_idx])
    sat_altitude_km = float(sim_series.sat_altitude_m[sim_idx]) / 1000.0
    target_intersection_pct = 100.0 * float(sim_series.target_area_intersection_ratio[sim_idx])
    target_novelty_pct = 100.0 * float(sim_series.target_area_novelty_ratio[sim_idx])
    theta_orbit_deg = float(np.rad2deg(idx_theta))

    scene_out = {
        "sim_idx": sim_idx,
        "sat_pos": sat_pos,
        "z_axis_dir": z_axis_dir,
        "sat_subpoint_lat_deg": sat_subpoint_lat_deg,
        "sat_subpoint_lon_deg": sat_subpoint_lon_deg,
        "sat_altitude_km": sat_altitude_km,
        "target_intersection_pct": target_intersection_pct,
        "target_novelty_pct": target_novelty_pct,
        "theta_orbit_deg": theta_orbit_deg,
        "trail_xy": trail_xy,
        "view_anchor_x": view_anchor_x,
        "view_anchor_y": view_anchor_y,
        "baseline_active_target_idx": active_target_idx,
        "orbit_altitude_km": SAT_ALTITUDE_KM,
        "sim_speed_multiplier": CONTROLS.sim_speed_multiplier,
        "edge_l": edge_l,
        "edge_r": edge_r,
        "sec_edge_l": sec_edge_l,
        "sec_edge_r": sec_edge_r,
        "cloud_world": _cloud_world_xy_for_frame(sim_idx),
        "ground_left": ground_left_xy,
        "ground_right": ground_right_xy,
        "ground_center": ground_center_xy,
        "camera_codes": np.asarray(sim_series.camera_observation_line_codes[sim_idx], dtype=np.int8),
        "secondary_camera_codes": secondary_codes,
        "captured_target_indices": captured_target_indices,
        "center_hit_cloud": bool(sim_series.camera_center_first_hit_is_cloud[sim_idx]),
        "camera_gsd_m": camera_gsd_m,
        "camera_image_smear_px": camera_image_smear_px,
        "camera_image_quality": camera_image_quality,
        "camera_vfov_deg": float(np.rad2deg(sim_series.camera_vertical_fov_rad)),
        "camera_swath_height_km": camera_swath_height_km,
        "cloud_blocked_pct": 100.0 * blocked_fraction if np.isfinite(blocked_fraction) else float("nan"),
        "sat_body_rotation_rate_label": sat_body_rotation_rate_label,
        "z_angle_rel_nadir_deg": float(np.rad2deg(z_angle_rel_nadir_rad)),
        "los_rel_nadir_deg": float(np.rad2deg(los_rel_nadir_rad)),
        "intersection_text": intersection_text,
        "ground_patch_hit_text": ground_patch_hit_text,
        "render_window_text": (
            f"{float(STATIC_SCENE['start_angle_deg']):+.1f} deg to "
            f"{float(STATIC_SCENE['end_angle_deg']):+.1f} deg"
        ),
        "controller_mode": sim_series.metadata.controller_mode,
        "safe_mode_activation_count": (
            int(sim_series.safe_mode_activation_count[sim_idx])
            if getattr(sim_series, "safe_mode_activation_count", None) is not None
            else 0
        ),
    }
    shutter_steps = _take_picture_cmd_steps(sim_series)
    if shutter_steps:
        shutter_active = _shutter_cmd_active(sim_idx, shutter_steps)
        latent_val = applied_val = 0.0
        if "reward" in PANELS:
            reward_artists = PANELS["reward"]["artists"]
            latent_arr = reward_artists.get("latent_reward")
            applied_arr = reward_artists.get("applied_reward")
            if latent_arr is not None and 0 <= sim_idx < latent_arr.shape[0]:
                latent_val = float(latent_arr[sim_idx])
            if applied_arr is not None and 0 <= sim_idx < applied_arr.shape[0]:
                applied_val = float(applied_arr[sim_idx])
        scene_out["baseline_shutter_text"] = (
            f"  SHUTTER  latent {latent_val:.2f}  applied {applied_val:.2f}"
            if shutter_active
            else ""
        )
        scene_out["baseline_latent_reward_text"] = (
            f"  capture reward  latent {latent_val:.2f}  applied {applied_val:.2f}"
        )
        if active_target_idx >= 0:
            scene_out["baseline_target_text"] = f"  active target {active_target_idx}"
        else:
            scene_out["baseline_target_text"] = "  nadir coast (no target lock)"
    return {**STATIC_SCENE, **scene_out}


def init() -> list:
    global SIM_TIME_S
    SIM_TIME_S = 0.0

    if "main" in PANELS:
        a = PANELS["main"]["artists"]
        a["sat"].set_data([], [])
        a["anchor_to_sat"].set_data([], [])
        a["trail"].set_data([], [])
        a["cone"].set_xy([[0, 0], [0, 0], [0, 0]])
        a["secondary_cone"].set_xy([[0, 0], [0, 0], [0, 0]])
        a["z_axis_arrow"].set_positions((0, 0), (0, 0))
        a["z_axis_arrow"].set_visible(False)
        a["z_axis_label"].set_position((0, 0))
        a["z_axis_label"].set_visible(False)
        for g, c in zip(a["cloud_glow"], a["cloud_core"]):
            g.set_data([], [])
            c.set_data([], [])

    if "closeup" in PANELS:
        a = PANELS["closeup"]["artists"]
        a["cone"].set_xy([[0, 0], [0, 0], [0, 0]])
        a["secondary_cone"].set_xy([[0, 0], [0, 0], [0, 0]])
        if "ground_footprint" in a:
            a["ground_footprint"].set_data([], [])
        a["anchor_to_sat"].set_data([], [])
        for g, c in zip(a["cloud_glow"], a["cloud_core"]):
            g.set_data([], [])
            c.set_data([], [])

    if "1d_sat_view" in PANELS:
        a = PANELS["1d_sat_view"]["artists"]
        a["img"].set_data(np.zeros((a["N_BINS"], a["W"], 4), dtype=float))

    if "1d_sat_view_secondary" in PANELS:
        a = PANELS["1d_sat_view_secondary"]["artists"]
        a["img"].set_data(np.zeros((a["N_BINS"], a["W"], 4), dtype=float))

    if "telemetry" in PANELS:
        PANELS["telemetry"]["artists"]["text"].set_text("")
        if "safe_mode_text" in PANELS["telemetry"]["artists"]:
            PANELS["telemetry"]["artists"]["safe_mode_text"].set_text("")
    if "reward" in PANELS:
        a = PANELS["reward"]["artists"]
        a["latent_line"].set_data([], [])
        a["applied_line"].set_data([], [])
        a["cursor"].set_data([], [])
    if "torque" in PANELS:
        a = PANELS["torque"]["artists"]
        a["line_applied"].set_data([], [])
        if "line_agent" in a:
            a["line_agent"].set_data([], [])
        a["cursor"].set_data([], [])
    if "pointing" in PANELS:
        a = PANELS["pointing"]["artists"]
        a["line_z"].set_data([], [])
        if "line_los" in a:
            a["line_los"].set_data([], [])
        a["cursor"].set_data([], [])
    if "capture" in PANELS:
        a = PANELS["capture"]["artists"]
        a["line_quality"].set_data([], [])
        a["line_cloud"].set_data([], [])
        a["cursor"].set_data([], [])

    return []


def update_panels(scene: dict) -> None:
    if "main" in PANELS:
        update_main_panel(PANELS["main"]["artists"], scene)
    if "closeup" in PANELS:
        update_closeup_panel(PANELS["closeup"]["artists"], scene)
    if "1d_sat_view" in PANELS:
        update_1d_sat_view(
            PANELS["1d_sat_view"]["artists"],
            scene["camera_codes"],
            captured_target_indices=scene.get("captured_target_indices"),
        )
    if "1d_sat_view_secondary" in PANELS and scene["secondary_camera_codes"] is not None:
        update_1d_sat_view(
            PANELS["1d_sat_view_secondary"]["artists"],
            scene["secondary_camera_codes"],
            captured_target_indices=scene.get("captured_target_indices"),
        )
    if "telemetry" in PANELS:
        update_telemetry_panel(PANELS["telemetry"]["artists"], scene)
    if "reward" in PANELS:
        update_reward_panel(PANELS["reward"]["artists"], scene["sim_idx"])
    if "torque" in PANELS:
        update_torque_panel(PANELS["torque"]["artists"], scene["sim_idx"])
    if "pointing" in PANELS:
        update_pointing_panel(PANELS["pointing"]["artists"], scene["sim_idx"])
    if "capture" in PANELS:
        update_capture_panel(PANELS["capture"]["artists"], scene["sim_idx"])


def update(_frame: int) -> list:
    global SIM_TIME_S
    if not CONTROLS.paused:
        SIM_TIME_S += (ANIMATION_INTERVAL_MS / 1000.0) * CONTROLS.sim_speed_multiplier
    # Finite episode scrubbing: clamp to [0, sim_total_s] (matches export + step buttons).
    sim_idx = simulation_index_from_time(SIM_TIME_S, wrap_orbit=False)
    scene = sample_scene(sim_idx)
    update_panels(scene)
    return []


def _resolve_ffmpeg_executable() -> tuple[str | None, str]:
    """Return (executable path, source hint) for a usable ffmpeg binary."""
    import shutil

    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and Path(exe).exists():
            return str(exe), "imageio_ffmpeg"
    except Exception:
        pass
    path_which = shutil.which("ffmpeg")
    if path_which:
        return path_which, "path_which"
    return None, "none"


_FFMPEG_ENCODER_CACHE: dict[str, frozenset[str]] = {}


def _ffmpeg_encoder_names(ffmpeg_exe: str) -> frozenset[str]:
    """Return encoder short names reported by ``ffmpeg -encoders`` (cached per binary)."""
    import subprocess

    cached = _FFMPEG_ENCODER_CACHE.get(ffmpeg_exe)
    if cached is not None:
        return cached
    proc = subprocess.run(
        [ffmpeg_exe, "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        check=False,
    )
    names: set[str] = set()
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].startswith("V"):
            names.add(parts[1])
    result = frozenset(names)
    _FFMPEG_ENCODER_CACHE[ffmpeg_exe] = result
    return result


def _resolve_h264_export_codec(ffmpeg_exe: str) -> tuple[str, list[str], str]:
    """Pick H.264 encoder: GPU ``h264_nvenc`` when available, else CPU ``libx264``."""
    encoders = _ffmpeg_encoder_names(ffmpeg_exe)
    if "h264_nvenc" in encoders:
        return (
            "h264_nvenc",
            ["-pix_fmt", "yuv420p", "-preset", "p4", "-rc", "vbr", "-cq", "23"],
            "h264_nvenc",
        )
    return "libx264", ["-pix_fmt", "yuv420p", "-preset", "veryfast"], "libx264"


class _FfmpegRawVideoPipeWriter:
    """Pipe RGBA frames to ffmpeg stdin (NVENC when available)."""

    def __init__(
        self,
        export_path: Path,
        *,
        width: int,
        height: int,
        fps: int,
        ffmpeg_exe: str,
        codec: str,
        extra_args: list[str],
    ) -> None:
        import subprocess

        self._export_path = export_path
        self._width = width
        self._height = height
        self._subprocess = subprocess
        cmd = [
            ffmpeg_exe,
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            f"{width}x{height}",
            "-pix_fmt",
            "rgba",
            "-r",
            str(fps),
            "-i",
            "pipe:0",
            "-an",
            "-c:v",
            codec,
            *extra_args,
            "-movflags",
            "+faststart",
            str(export_path),
        ]
        self._cmd = cmd
        self._proc: subprocess.Popen[bytes] | None = None

    def __enter__(self) -> Self:
        self._proc = self._subprocess.Popen(
            self._cmd,
            stdin=self._subprocess.PIPE,
            stdout=self._subprocess.DEVNULL,
            stderr=self._subprocess.PIPE,
        )
        return self

    def write_rgba_frame(self, rgba: np.ndarray) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise RuntimeError("ffmpeg pipe writer is not open")
        self._proc.stdin.write(np.ascontiguousarray(rgba).tobytes())

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._proc is None:
            return
        if self._proc.stdin is not None:
            self._proc.stdin.close()
        stderr = self._proc.stderr.read().decode("utf-8", errors="replace") if self._proc.stderr else ""
        rc = self._proc.wait()
        self._proc = None
        if exc_type is None and rc != 0:
            raise RuntimeError(
                f"ffmpeg export failed (exit {rc}) for {self._export_path}: {stderr.strip()}"
            )


def _try_reencode_mp4_h264_for_web(path: Path) -> tuple[bool, str]:
    """Re-encode MP4 to H.264 yuv420p for HTML5 playback in notebook/desktop browsers.

    OpenCV's ``mp4v`` output is often MPEG-4 Part 2, which many browsers won't play
    in ``<video>`` elements; this pass produces a widely supported stream when an
    ffmpeg executable is available (bundled ``imageio-ffmpeg`` preferred).
    """
    import subprocess

    ffmpeg_exe, via = _resolve_ffmpeg_executable()
    if ffmpeg_exe is None:
        return False, "no_ffmpeg_exe"
    codec, extra_args, codec_label = _resolve_h264_export_codec(ffmpeg_exe)
    tmp = path.with_name(path.stem + "._h264_tmp" + path.suffix)
    try:
        subprocess.run(
            [
                ffmpeg_exe,
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(path),
                "-c:v",
                codec,
                *extra_args,
                "-movflags",
                "+faststart",
                "-an",
                str(tmp),
            ],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, OSError):
        try:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return False, f"ffmpeg_failed:{via}"
    try:
        path.unlink()
    except OSError:
        try:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return False, f"unlink_failed:{via}"
    try:
        tmp.rename(path)
    except OSError:
        return False, f"rename_failed:{via}"
    return True, f"{via}:{codec_label}"


def save_one_pass_video_30x(export_path: Path | None = None) -> Path:
    """
    Export video by rendering frames in a single pass at 30x real-time speed,
    piping RGBA frames to ffmpeg (``h264_nvenc`` when available, else ``libx264``).

    Uses parallel CPU draw when ``RENDER.export_workers`` > 1 (default 8).
    Override worker count with env ``VIDEO_EXPORT_WORKERS``.
    """
    from render.video_export_parallel import (
        compute_export_frame_indices,
        resolve_export_worker_count,
        save_one_pass_video_parallel,
    )

    sim_series = _require_runtime()
    if FIG is None:
        raise RuntimeError("Figure has not been initialized.")
    n_workers = resolve_export_worker_count()
    frame_indices = compute_export_frame_indices(float(sim_series.metadata.sim_total_s))
    if n_workers > 1 and len(frame_indices) >= n_workers:
        return save_one_pass_video_parallel(export_path, n_workers=n_workers)

    from matplotlib.backends.backend_agg import FigureCanvasAgg

    ffmpeg_exe, ffmpeg_via = _resolve_ffmpeg_executable()
    if ffmpeg_exe is None:
        raise SystemError(
            "ffmpeg is not available; cannot export video. "
            "Install ffmpeg or the Python package 'imageio-ffmpeg'."
        )

    export_speed_multiplier = float(SIMULATION.export_speed_multiplier)
    export_fps = int(RENDER.export_fps)
    sim_total_s = float(sim_series.metadata.sim_total_s)
    dt_sim_s = (ANIMATION_INTERVAL_MS / 1000.0) * export_speed_multiplier
    frame_indices = compute_export_frame_indices(sim_total_s)
    if export_path is None:
        export_path = Path(__file__).resolve().parents[2] / RENDER.export_filename
    export_path = Path(export_path).resolve()
    export_path.parent.mkdir(parents=True, exist_ok=True)
    archived = archive_existing_video(export_path)
    if archived is not None:
        print(f"[video] archived previous export -> {archived}")

    codec, extra_args, codec_label = _resolve_h264_export_codec(ffmpeg_exe)
    print(f"[video] ffmpeg encoder={codec_label} via={ffmpeg_via} fps={export_fps}")

    def export_update(frame: int) -> list:
        sim_t = min(float(frame) * dt_sim_s, sim_total_s)
        sim_idx = simulation_index_from_time(sim_t, wrap_orbit=False)
        scene = sample_scene(sim_idx)
        update_panels(scene)
        return []

    init()

    fig_w_in, fig_h_in, width, height = export_canvas_geometry()
    FIG.set_size_inches(fig_w_in, fig_h_in)
    FIG.set_dpi(RENDER.export_dpi)
    canvas = FigureCanvasAgg(FIG)
    canvas.draw()

    def _frame_iter() -> tqdm:
        return tqdm(
            frame_indices,
            desc="Writing video",
            unit="frame",
        )

    def _export_with_codec(active_codec: str, active_extra: list[str]) -> None:
        with _FfmpegRawVideoPipeWriter(
            export_path,
            width=width,
            height=height,
            fps=export_fps,
            ffmpeg_exe=ffmpeg_exe,
            codec=active_codec,
            extra_args=active_extra,
        ) as pipe_writer:
            for frame in _frame_iter():
                export_update(frame)
                canvas.draw()
                rgba = np.asarray(canvas.buffer_rgba())
                pipe_writer.write_rgba_frame(rgba)

    try:
        _export_with_codec(codec, extra_args)
    except RuntimeError as exc:
        if codec != "h264_nvenc":
            raise
        print(f"[video] h264_nvenc failed ({exc}); falling back to libx264")
        _export_with_codec("libx264", ["-pix_fmt", "yuv420p", "-preset", "veryfast"])

    return export_path


def _maximize_interactive_window() -> None:
    if FIG is None:
        raise RuntimeError("Figure has not been initialized.")
    if not RENDER.interactive_start_maximized:
        return
    mgr = getattr(FIG.canvas, "manager", None)
    if mgr is None:
        return
    try:
        win = getattr(mgr, "window", None)
        if win is None:
            return
        if hasattr(win, "showMaximized"):
            win.showMaximized()
            return
        if hasattr(win, "wm_state"):
            win.wm_state("zoomed")
            return
        top = getattr(win, "winfo_toplevel", lambda: win)()
        if hasattr(top, "wm_state"):
            top.wm_state("zoomed")
    except Exception:
        pass


_DEBUG_LAYOUT_LOG = Path(__file__).resolve().parents[2] / "debug-b36892.log"


def _rect_overlap_area(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    ax0, ay0, aw, ah = a
    bx0, by0, bw, bh = b
    ix0 = max(ax0, bx0)
    iy0 = max(ay0, by0)
    ix1 = min(ax0 + aw, bx0 + bw)
    iy1 = min(ay0 + ah, by0 + bh)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    return float((ix1 - ix0) * (iy1 - iy0))


def _audit_dashboard_layout(*, run_id: str = "layout") -> None:
    """Log figure-axis bounds and pairwise overlaps (debug session b36892)."""
    if FIG is None:
        return
    gutter = float(RENDER.figure_inset_gutter_frac)

    def _collect_declared_rects() -> list[dict[str, object]]:
        declared: list[dict[str, object]] = []
        specs = [
            ("telemetry", RENDER.telemetry_axes_rect),
            ("reward", RENDER.reward_axes_rect),
            ("torque", RENDER.torque_axes_rect),
            ("main", RENDER.main_axes_rect),
            ("closeup", RENDER.closeup_axes_rect),
            ("pointing", RENDER.pointing_axes_rect),
            ("capture", RENDER.capture_axes_rect),
            ("transport", RENDER.transport_bar_rect),
        ]
        for name, rect in specs:
            declared.append({"name": name, "bounds": list(rect)})
        for name, rect in (
            ("sat_view_1d", RENDER.sat_view_1d_axes_rect),
            ("sat_view_1d_secondary", RENDER.sat_view_1d_secondary_axes_rect),
        ):
            l, b, w, h = rect
            title_frac = 0.26
            h_strip = h * (1.0 - title_frac)
            declared.append({"name": f"{name}_strip", "bounds": [l, b, w, h_strip]})
            declared.append({"name": f"{name}_title", "bounds": [l, b + h_strip, w, h * title_frac]})
        return declared

    def _find_overlaps(entries: list[dict[str, object]]) -> list[dict[str, object]]:
        out: list[dict[str, object]] = []
        for i, a in enumerate(entries):
            for j, b in enumerate(entries):
                if j <= i:
                    continue
                area = _rect_overlap_area(tuple(a["bounds"]), tuple(b["bounds"]))
                if area <= 1e-9:
                    continue
                out.append(
                    {
                        "a": a["name"],
                        "b": b["name"],
                        "overlap_area": area,
                        "a_bounds": a["bounds"],
                        "b_bounds": b["bounds"],
                    }
                )
        return out

    entries: list[dict[str, object]] = []
    for ax in FIG.axes:
        name = getattr(ax, "get_label", lambda: "")() or repr(ax)
        l, b, w, h = ax.get_position().bounds
        entries.append({"name": name, "bounds": [l, b, w, h]})

    declared = _collect_declared_rects()
    overlaps_actual = _find_overlaps(entries)
    overlaps_declared = _find_overlaps(declared)

  #region agent log
    payload = {
        "sessionId": "b36892",
        "runId": run_id,
        "hypothesisId": "layout-overlap",
        "location": "render_main.py:_audit_dashboard_layout",
        "message": "dashboard panel bounds and overlaps",
        "data": {
            "gutter_frac": gutter,
            "n_axes": len(entries),
            "overlaps_actual": overlaps_actual,
            "overlaps_declared": overlaps_declared,
            "panels_actual": entries,
            "panels_declared": declared,
        },
        "timestamp": int(time.time() * 1000),
    }
    try:
        with _DEBUG_LAYOUT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except OSError:
        pass
  #endregion


def _build_panels() -> None:
    sim_series = _require_runtime()
    if FIG is None:
        raise RuntimeError("Figure has not been initialized.")
    if SHOW_TELEMETRY:
        axes, artists = build_telemetry_panel(FIG, STATIC_SCENE)
        PANELS["telemetry"] = {"axes": axes, "artists": artists}
    if SHOW_REWARD_PLOT:
        cmd_steps = _take_picture_cmd_steps(sim_series)
        latent = latent_capture_reward_series(sim_series)
        applied = applied_capture_reward_series(sim_series, cmd_steps=cmd_steps)
        axes, artists = build_reward_panel(
            FIG,
            sim_series.t_s,
            latent_reward=latent,
            applied_reward=applied,
            title="Reward",
            cmd_times_s=_take_picture_cmd_times_s(sim_series),
        )
        PANELS["reward"] = {"axes": axes, "artists": artists}
    if SHOW_TORQUE_PLOT:
        use_obc = series_uses_obc_pointing(sim_series)
        torque_agent = torque_agent_series_for_plot(sim_series)
        applied_label = "OBC pointing (RW)" if use_obc else "applied (RW)"
        axes, artists = build_torque_panel(
            FIG,
            sim_series.t_s,
            sim_series.wheel_torque_cmd_nm,
            torque_agent_nm=torque_agent,
            applied_label=applied_label,
        )
        PANELS["torque"] = {"axes": axes, "artists": artists}
    if SHOW_POINTING_PLOT:
        nadir_angle = sim_series.theta_orbit_rad + np.pi
        z_offnadir_rad = np.arctan2(
            np.sin(sim_series.body_z_angle_rad - nadir_angle),
            np.cos(sim_series.body_z_angle_rad - nadir_angle),
        )
        offnadir_deg = np.rad2deg(z_offnadir_rad)
        agent_offnadir_deg = agent_pointing_offnadir_deg_for_plot(sim_series)
        axes, artists = build_pointing_panel(
            FIG,
            sim_series.t_s,
            offnadir_deg,
            los_offnadir_deg=None,
            agent_offnadir_deg=agent_offnadir_deg,
        )
        PANELS["pointing"] = {"axes": axes, "artists": artists}
    if SHOW_CAPTURE_PLOT:
        cloud_blocked_pct = 100.0 * np.asarray(sim_series.camera_cloud_blocked_fraction, dtype=float)
        axes, artists = build_capture_panel(
            FIG,
            sim_series.t_s,
            sim_series.camera_image_quality,
            cloud_blocked_pct,
        )
        PANELS["capture"] = {"axes": axes, "artists": artists}
    if SHOW_MAIN_PLOT:
        axes, artists = build_main_panel(FIG, STATIC_SCENE)
        PANELS["main"] = {"axes": axes, "artists": artists}
    if SHOW_CLOSEUP:
        axes, artists = build_closeup_panel(FIG, STATIC_SCENE)
        PANELS["closeup"] = {"axes": axes, "artists": artists}
    if SHOW_1D_SAT_VIEW:
        axes, artists = build_1d_sat_view(FIG, STATIC_SCENE)
        PANELS["1d_sat_view"] = {"axes": axes, "artists": artists}
    if SHOW_1D_SAT_VIEW_SECONDARY and int(STATIC_SCENE["n_bins_secondary"]) > 0:
        axes, artists = build_1d_sat_view(
            FIG,
            STATIC_SCENE,
            axes_rect=RENDER.sat_view_1d_secondary_axes_rect,
            n_bins_override=int(STATIC_SCENE["n_bins_secondary"]),
            title="Secondary Camera",
        )
        PANELS["1d_sat_view_secondary"] = {"axes": axes, "artists": artists}
    _audit_dashboard_layout(run_id="post-build")


def render_from_series(
    *,
    simulation_series: SimulationStateSeries,
    render_mode: RenderMode,
    output_path: Path | None = None,
) -> Path | None:
    global CONTROL_ARTISTS, FIG
    _configure_runtime_from_series(simulation_series)
    if FIG is None:
        raise RuntimeError("Figure has not been initialized.")

    FIG.text(
        0.5,
        0.988,
        "SATELLITE OVERFLIGHT \u2014 ORBIT & IMAGING DASHBOARD",
        color=RENDER.title_color,
        ha="center",
        va="top",
        fontsize=RENDER.suptitle_fontsize + 2,
        fontweight="bold",
    )
    FIG.text(
        0.5,
        0.963,
        f"altitude {SAT_ALTITUDE_KM:.0f} km   \u00b7   period {simulation_series.metadata.orbit_period_s/60:.1f} min"
        f"   \u00b7   control: {simulation_series.metadata.controller_mode}",
        color=RENDER.subtitle_color,
        ha="center",
        va="top",
        fontsize=RENDER.suptitle_fontsize - 3,
    )

    _build_panels()
    CONTROLS.step_backward_cb = _step_backward_one_frame
    CONTROLS.step_forward_cb = _step_forward_one_frame
    CONTROL_ARTISTS = build_controls_panel(FIG, CONTROLS)

    if render_mode == RenderMode.EXPORT:
        try:
            return save_one_pass_video_30x(export_path=output_path)
        finally:
            if FIG is not None:
                plt.close(FIG)
            FIG = None
    if render_mode == RenderMode.HEADLESS:
        init()
        scene = sample_scene(0)
        update_panels(scene)
        return None

    _ani = FuncAnimation(
        FIG,
        update,
        init_func=init,
        blit=False,
        interval=ANIMATION_INTERVAL_MS,
        cache_frame_data=False,
    )
    _maximize_interactive_window()
    plt.show()
    return None
