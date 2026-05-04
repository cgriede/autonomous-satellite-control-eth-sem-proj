from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation as mpl_animation
from matplotlib.animation import FuncAnimation

from environment_definition.constants import (
    EARTH_RADIUS,
    N_PIXELS_Y,
    RenderMode,
    RENDER,
    SIMULATION,
    UREG as ureg,
)
from environment_definition.constants.MISSION import LON_GLOBAL, OBSERVATION_TARGET_AREAS, primary_observation_target_area
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE, SATELLITE_ALTITUDE
from simulation.state_types import SimulationStateSeries
from utils.geodesics.geodesic_helpers import geodesic_distance

if __package__:
    from ._closeup_view import build_closeup_panel, update_closeup_panel
    from ._controls import RenderControls, build_controls_panel
    from ._fixed_bird_view import build_1d_fixed_bird_view, update_1d_fixed_bird_view
    from ._main_view import build_main_panel, update_main_panel
    from ._reward_plot import build_reward_panel, update_reward_panel
    from ._torque_plot import build_torque_panel, update_torque_panel
    from ._satellite_cam_view import build_1d_sat_view, update_1d_sat_view
    from ._telemetry import build_telemetry_panel, update_telemetry_panel
else:
    from render._closeup_view import build_closeup_panel, update_closeup_panel
    from render._controls import RenderControls, build_controls_panel
    from render._fixed_bird_view import build_1d_fixed_bird_view, update_1d_fixed_bird_view
    from render._main_view import build_main_panel, update_main_panel
    from render._reward_plot import build_reward_panel, update_reward_panel
    from render._torque_plot import build_torque_panel, update_torque_panel
    from render._satellite_cam_view import build_1d_sat_view, update_1d_sat_view
    from render._telemetry import build_telemetry_panel, update_telemetry_panel


SHOW_MAIN_PLOT = True
SHOW_1D_FIXED_BIRD_VIEW = True
SHOW_1D_SAT_VIEW = True
SHOW_CLOSEUP = True
SHOW_TELEMETRY = True
SHOW_REWARD_PLOT = True
SHOW_TORQUE_PLOT = True

R_EARTH_KM = EARTH_RADIUS.to(ureg.km).magnitude
SAT_ALTITUDE_KM = SATELLITE_ALTITUDE.to(ureg.km).magnitude
R_ORBIT_KM = R_EARTH_KM + SAT_ALTITUDE_KM
THETA_CENTER = SIMULATION.theta_center.to(ureg.rad).magnitude
ANIMATION_INTERVAL_MS = RENDER.animation_interval.to(ureg.ms).magnitude
SIM_SPEED_MULTIPLIER = float(RENDER.default_speed_multiplier)
SIMULATION_SERIES: SimulationStateSeries | None = None
N_CLOUDS = 0
N_BINS = 0
STATIC_SCENE: dict[str, object] = {}
FIG: plt.Figure | None = None
SIM_TIME_S = 0.0
PANELS: dict[str, dict] = {}
CONTROLS = RenderControls(sim_speed_multiplier=SIM_SPEED_MULTIPLIER)
CONTROL_ARTISTS: dict | None = None


def _require_runtime() -> SimulationStateSeries:
    if SIMULATION_SERIES is None:
        raise RuntimeError("Renderer runtime has not been configured with simulation data.")
    return SIMULATION_SERIES


def _debug_log_path() -> Path:
    return Path(__file__).resolve().parents[1] / "render_debug.log"


def _render_xy_from_theta(theta_rad: float, radius_km: float) -> np.ndarray:
    render_theta = float(theta_rad) - 0.5 * np.pi
    return np.array([radius_km * np.cos(render_theta), radius_km * np.sin(render_theta)], dtype=float)


def _latlonz_to_render_xy(lat_deg: Any, lon_deg: Any, radius_km: Any) -> np.ndarray:
    """Project geodetic (lat, lon, radius_km) to renderer XY plane centered at the North Pole.

    - radial distance from pole = (pi/2 - lat) * radius
    - azimuth = lon (radians), with lon=0 -> +x, lon increases CCW (eastwards) -> +y at 90deg
    """
    lat_r = float(np.deg2rad(float(lat_deg)))
    lon_r = float(np.deg2rad(float(lon_deg)))
    radial = float((0.5 * np.pi - lat_r) * float(radius_km))
    x = radial * np.cos(lon_r)
    y = radial * np.sin(lon_r)
    return np.array([x, y], dtype=float)


def _configure_runtime_from_series(simulation_series: SimulationStateSeries) -> None:
    global SIMULATION_SERIES, N_CLOUDS, N_BINS, STATIC_SCENE, CONTROLS, FIG, PANELS, CONTROL_ARTISTS
    SIMULATION_SERIES = simulation_series
    N_CLOUDS = int(SIMULATION_SERIES.cloud_arc_radius_km.shape[1])
    N_BINS = int(SIMULATION_SERIES.camera_observation_line_codes.shape[1])
    target_area = OBSERVATION_TARGET_AREAS[0]
    target_lat_min_deg = float(target_area.lat_min.to(ureg.deg).magnitude)
    target_lat_max_deg = float(target_area.lat_max.to(ureg.deg).magnitude)
    target_center_lat_deg = 0.5 * (target_lat_min_deg + target_lat_max_deg)
    # build target arc in lat/lon and project to render XY
    target_lats = np.linspace(target_lat_max_deg, target_lat_min_deg, 256, dtype=float)
    target_xy_x = []
    target_xy_y = []
    for lat in target_lats:
        xy = _latlonz_to_render_xy(lat, 0.0, float(R_EARTH_KM))
        target_xy_x.append(xy[0])
        target_xy_y.append(xy[1])
    target_line_length_km = float(
        geodesic_distance(
            LON_GLOBAL,
            target_area.lat_min,
            LON_GLOBAL,
            target_area.lat_max,
        ).to(ureg.km).magnitude
    )
    STATIC_SCENE = {
        "R_earth": R_EARTH_KM,
        "R_orbit": R_ORBIT_KM,
        "theta_center": THETA_CENTER,
        "start_angle_deg": float(simulation_series.metadata.start_angle_deg),
        "end_angle_deg": float(simulation_series.metadata.end_angle_deg),
        "observer_x": float(_latlonz_to_render_xy(target_center_lat_deg, 0.0, float(R_EARTH_KM))[0]),
        "observer_y": float(_latlonz_to_render_xy(target_center_lat_deg, 0.0, float(R_EARTH_KM))[1]),
        "observer_pos": np.array([*_latlonz_to_render_xy(target_center_lat_deg, 0.0, float(R_EARTH_KM))], dtype=float),
        "target_arc_xy": (np.asarray(target_xy_x, dtype=float), np.asarray(target_xy_y, dtype=float)),
        "target_line_length_km": target_line_length_km,
        "cloud_models": [None] * N_CLOUDS,
        "n_clouds": N_CLOUDS,
        "n_bins": N_BINS,
        "controller_mode": SIMULATION_SERIES.metadata.controller_mode,
    }
    CONTROLS = RenderControls(sim_speed_multiplier=SIM_SPEED_MULTIPLIER)
    FIG = plt.figure(figsize=RENDER.figure_size, facecolor=RENDER.space_background)
    PANELS = {}
    CONTROL_ARTISTS = None
    try:
        log_path = _debug_log_path()
        log_path.write_text(
            "# render debug log\n"
            f"# target_window={float(simulation_series.metadata.start_angle_deg):+.3f} -> {float(simulation_series.metadata.end_angle_deg):+.3f}\n"
        )
    except Exception:
        pass


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
        xs = []
        ys = []
        for t in th:
            xy = _render_xy_from_theta(t, r)
            xs.append(xy[0])
            ys.append(xy[1])
        specs.append({"x": np.asarray(xs, dtype=float), "y": np.asarray(ys, dtype=float)})
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
    # append a diagnostic line to render_debug.log to help trace misalignments
    try:
        sim_series = SIMULATION_SERIES
        if sim_series is not None:
            _write_debug_log(sim_idx, scene, sim_series)
    except Exception:
        pass
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
    # Prefer geodetic satellite position (sat_subpoint_lat_deg, sat_subpoint_lon_deg, sat_altitude_m)
    sat_lat = float(sim_series.sat_subpoint_lat_deg[sim_idx])
    sat_lon = float(sim_series.sat_subpoint_lon_deg[sim_idx])
    sat_alt_km = float(sim_series.sat_altitude_m[sim_idx]) / 1000.0
    sat_pos = _latlonz_to_render_xy(sat_lat, sat_lon, float(R_EARTH_KM) + sat_alt_km)

    z_angle = float(sim_series.body_z_angle_rad[sim_idx])
    z_axis_dir = np.array([np.cos(z_angle), np.sin(z_angle)], dtype=float)

    # build trail from sat subpoint lat/lon series
    k = max(sim_idx + 1, 2)
    trail_lats = np.asarray(sim_series.sat_subpoint_lat_deg[:k], dtype=float)
    trail_lons = np.asarray(sim_series.sat_subpoint_lon_deg[:k], dtype=float)
    trail_alts = [float(v) / 1000.0 for v in sim_series.sat_altitude_m[:k]]
    tx = []
    ty = []
    for la, lo, al in zip(trail_lats, trail_lons, trail_alts):
        p = _latlonz_to_render_xy(float(la), float(lo), float(R_EARTH_KM) + float(al))
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
    camera_swath_height_km = (N_PIXELS_Y * camera_gsd_m) / 1000.0 if np.isfinite(camera_gsd_m) else float("nan")
    blocked_fraction = float(sim_series.camera_cloud_blocked_fraction[sim_idx])
    # prefer geodetic lat/lon ground intersection arrays and project them
    center_hit_lat_lon = np.asarray(sim_series.camera_center_first_hit_xy_km[sim_idx], dtype=float)
    # simulation also stores lat/lon deg arrays for camera ground points; prefer those when present
    try:
        gc_lat, gc_lon = sim_series.camera_ground_center_lat_lon_deg[sim_idx]
        gl_lat, gl_lon = sim_series.camera_ground_left_lat_lon_deg[sim_idx]
        gr_lat, gr_lon = sim_series.camera_ground_right_lat_lon_deg[sim_idx]
        center_first_hit_lat_lon = sim_series.camera_center_first_hit_xy_km[sim_idx]
        center_first_hit_xy = np.array([np.nan, np.nan], dtype=float)
        if not np.isnan(center_first_hit_lat_lon).any():
            # if center-first-hit given in lat/lon deg use that projection
            ch_lat, ch_lon = sim_series.camera_center_first_hit_xy_km[sim_idx]
            center_first_hit_xy = _latlonz_to_render_xy(float(ch_lat), float(ch_lon), R_EARTH_KM)
        ground_center_xy = _latlonz_to_render_xy(float(gc_lat), float(gc_lon), R_EARTH_KM)
        ground_left_xy = _latlonz_to_render_xy(float(gl_lat), float(gl_lon), R_EARTH_KM)
        ground_right_xy = _latlonz_to_render_xy(float(gr_lat), float(gr_lon), R_EARTH_KM)
    except Exception:
        # fall back to any precomputed XY fields if lat/lon not available
        center_first_hit_xy = np.asarray(sim_series.camera_center_first_hit_xy_km[sim_idx], dtype=float)
        ground_center_xy = np.asarray(sim_series.camera_ground_center_xy_km[sim_idx], dtype=float)
        ground_left_xy = np.asarray(sim_series.camera_ground_left_xy_km[sim_idx], dtype=float)
        ground_right_xy = np.asarray(sim_series.camera_ground_right_xy_km[sim_idx], dtype=float)

    nadir_angle = float(sim_series.theta_orbit_rad[sim_idx]) + np.pi
    z_angle_rel_nadir_rad = np.arctan2(np.sin(z_angle - nadir_angle), np.cos(z_angle - nadir_angle))
    sat_to_observer = STATIC_SCENE["observer_pos"] - sat_pos
    los_angle = float(np.arctan2(sat_to_observer[1], sat_to_observer[0]))
    los_rel_nadir_rad = np.arctan2(np.sin(los_angle - nadir_angle), np.cos(los_angle - nadir_angle))

    if np.isnan(center_first_hit_xy).any():
        intersection_text = "none"
    else:
        hit_type = "cloud" if bool(sim_series.camera_center_first_hit_is_cloud[sim_idx]) else "earth"
        hit_distance_km = float(np.linalg.norm(center_first_hit_xy - sat_pos))
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

    return {
        "sim_idx": sim_idx,
        "sat_pos": sat_pos,
        "z_axis_dir": z_axis_dir,
        "trail_xy": trail_xy,
        "observer_x": STATIC_SCENE["observer_x"],
        "observer_y": STATIC_SCENE["observer_y"],
        "orbit_altitude_km": SAT_ALTITUDE_KM,
        "sim_speed_multiplier": CONTROLS.sim_speed_multiplier,
        "edge_l": edge_l,
        "edge_r": edge_r,
        "cloud_world": _cloud_world_xy_for_frame(sim_idx),
        "ground_left": ground_left_xy,
        "ground_right": ground_right_xy,
        "ground_center": ground_center_xy,
        "camera_codes": np.asarray(sim_series.camera_observation_line_codes[sim_idx], dtype=np.int8),
        "fixed_codes": np.asarray(sim_series.fixed_ground_line_codes[sim_idx], dtype=np.int8),
        "center_hit_cloud": bool(sim_series.camera_center_first_hit_is_cloud[sim_idx]),
        "camera_gsd_m": camera_gsd_m,
        "camera_vfov_deg": float(np.rad2deg(sim_series.camera_vertical_fov_rad)),
        "camera_swath_height_km": camera_swath_height_km,
        "cloud_blocked_pct": 100.0 * blocked_fraction if np.isfinite(blocked_fraction) else float("nan"),
        "sat_body_rotation_rate_label": sat_body_rotation_rate_label,
        "z_angle_rel_nadir_deg": float(np.rad2deg(z_angle_rel_nadir_rad)),
        "los_rel_nadir_deg": float(np.rad2deg(los_rel_nadir_rad)),
        "intersection_text": intersection_text,
        "ground_patch_hit_text": ground_patch_hit_text,
        "target_line_length_km": STATIC_SCENE["target_line_length_km"],
        "render_window_text": (
            f"{float(sim_series.metadata.start_angle_deg):+.1f} deg to "
            f"{float(sim_series.metadata.end_angle_deg):+.1f} deg"
        ),
        "controller_mode": sim_series.metadata.controller_mode,
    }


def _write_debug_log(sim_idx: int, scene: dict, sim_series: SimulationStateSeries) -> None:
    try:
        log_path = _debug_log_path()
        parts = [
            f"frame={sim_idx}",
            f"render_window={scene.get('render_window_text', '')}",
        ]
        try:
            sat_lat = float(sim_series.sat_subpoint_lat_deg[sim_idx])
            sat_lon = float(sim_series.sat_subpoint_lon_deg[sim_idx])
            sat_alt = float(sim_series.sat_altitude_m[sim_idx]) / 1000.0
            parts.append(f"sat_lat={sat_lat:.6f}")
            parts.append(f"sat_lon={sat_lon:.6f}")
            parts.append(f"sat_alt_km={sat_alt:.3f}")
        except Exception:
            parts.append("sat_geodetic=n/a")
        try:
            sp = np.asarray(scene.get("sat_pos", np.array([np.nan, np.nan])), dtype=float)
            parts.append(f"sat_x={sp[0]:.3f}")
            parts.append(f"sat_y={sp[1]:.3f}")
        except Exception:
            parts.append("sat_xy=n/a")
        try:
            ta = primary_observation_target_area()
            parts.append(f"target_lat_min={float(ta.lat_min.to(ureg.deg).magnitude):.6f}")
            parts.append(f"target_lat_max={float(ta.lat_max.to(ureg.deg).magnitude):.6f}")
        except Exception:
            parts.append("target_area=n/a")
        try:
            nclouds = int(sim_series.cloud_arc_radius_km.shape[1])
            parts.append(f"n_clouds={nclouds}")
            if nclouds > 0:
                r = float(sim_series.cloud_arc_radius_km[sim_idx, 0])
                s = float(sim_series.cloud_arc_start_rad[sim_idx, 0])
                e = float(sim_series.cloud_arc_end_rad[sim_idx, 0])
                mid = 0.5 * (s + e)
                parts.append(f"cloud0_r_km={r:.3f}")
                parts.append(f"cloud0_mid_rad={mid:.6f}")
        except Exception:
            parts.append("clouds=n/a")
        try:
            codes = np.asarray(sim_series.camera_observation_line_codes[sim_idx], dtype=np.int8)
            unique, counts = np.unique(codes, return_counts=True)
            code_summary = ",".join([f"{int(u)}:{int(c)}" for u, c in zip(unique, counts)])
            parts.append(f"cam_codes={code_summary}")
        except Exception:
            parts.append("cam_codes=n/a")
        with open(log_path, "a") as f:
            f.write(" | ".join(parts) + "\n")
    except Exception:
        return


def init() -> list:
    global SIM_TIME_S
    SIM_TIME_S = 0.0

    if "main" in PANELS:
        a = PANELS["main"]["artists"]
        a["sat"].set_data([], [])
        a["obs_to_sat"].set_data([], [])
        a["trail"].set_data([], [])
        a["cone"].set_xy([[0, 0], [0, 0], [0, 0]])
        a["z_axis_arrow"].set_positions((0, 0), (0, 0))
        a["z_axis_label"].set_position((0, 0))
        for g, c in zip(a["cloud_glow"], a["cloud_core"]):
            g.set_data([], [])
            c.set_data([], [])

    if "closeup" in PANELS:
        a = PANELS["closeup"]["artists"]
        a["cone"].set_xy([[0, 0], [0, 0], [0, 0]])
        a["hit"].set_data([], [])
        a["obs_to_hit"].set_data([], [])
        for g, c in zip(a["cloud_glow"], a["cloud_core"]):
            g.set_data([], [])
            c.set_data([], [])

    if "fixed_bird" in PANELS:
        a = PANELS["fixed_bird"]["artists"]
        a["img"].set_data(np.zeros((a["H"], a["N_BINS"], 4), dtype=float))
        a["observer_line"].set_color("red")

    if "1d_sat_view" in PANELS:
        a = PANELS["1d_sat_view"]["artists"]
        a["img"].set_data(np.zeros((a["H"], a["N_BINS"], 4), dtype=float))

    if "telemetry" in PANELS:
        PANELS["telemetry"]["artists"]["text"].set_text("")
    if "reward" in PANELS:
        a = PANELS["reward"]["artists"]
        a["line"].set_data([], [])
        a["cursor"].set_data([], [])
    if "torque" in PANELS:
        a = PANELS["torque"]["artists"]
        a["line"].set_data([], [])
        a["cursor"].set_data([], [])

    return []


def update_panels(scene: dict) -> None:
    if "main" in PANELS:
        update_main_panel(PANELS["main"]["artists"], scene)
    if "closeup" in PANELS:
        update_closeup_panel(PANELS["closeup"]["artists"], scene)
    if "fixed_bird" in PANELS:
        observer_cloud_covered = bool(scene["center_hit_cloud"])
        update_1d_fixed_bird_view(
            artists=PANELS["fixed_bird"]["artists"],
            fixed_ground_line_codes=scene["fixed_codes"],
            observer_cloud_covered=observer_cloud_covered,
        )
    if "1d_sat_view" in PANELS:
        update_1d_sat_view(PANELS["1d_sat_view"]["artists"], scene["camera_codes"])
    if "telemetry" in PANELS:
        update_telemetry_panel(PANELS["telemetry"]["artists"], scene)
    if "reward" in PANELS:
        update_reward_panel(PANELS["reward"]["artists"], scene["sim_idx"])
    if "torque" in PANELS:
        update_torque_panel(PANELS["torque"]["artists"], scene["sim_idx"])


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
                "libx264",
                "-pix_fmt",
                "yuv420p",
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
    return True, via


def save_one_pass_video_30x(export_path: Path | None = None) -> Path:
    sim_series = _require_runtime()
    if FIG is None:
        raise RuntimeError("Figure has not been initialized.")
    export_speed_multiplier = float(SIMULATION.export_speed_multiplier)
    export_fps = int(RENDER.export_fps)
    sim_total_s = float(sim_series.metadata.sim_total_s)
    dt_sim_s = (ANIMATION_INTERVAL_MS / 1000.0) * export_speed_multiplier
    export_num_frames = max(2, int(np.ceil(sim_total_s / dt_sim_s)) + 1)
    if export_path is None:
        export_path = Path(__file__).resolve().parents[2] / RENDER.export_filename
    export_path.parent.mkdir(parents=True, exist_ok=True)

    def export_update(frame: int) -> list:
        sim_t = min(float(frame) * dt_sim_s, sim_total_s)
        sim_idx = simulation_index_from_time(sim_t, wrap_orbit=False)
        scene = sample_scene(sim_idx)
        update_panels(scene)
        return []

    if mpl_animation.writers.is_available("ffmpeg"):
        export_ani = FuncAnimation(
            FIG,
            export_update,
            init_func=init,
            frames=export_num_frames,
            blit=False,
            interval=1000.0 / export_fps,
            repeat=False,
        )
        export_ani.save(
            str(export_path),
            writer="ffmpeg",
            fps=export_fps,
            dpi=RENDER.export_dpi,
        )
    else:
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        import cv2  # type: ignore[reportMissingImports]

        canvas = FigureCanvasAgg(FIG)
        canvas.draw()
        width, height = canvas.get_width_height()
        writer = cv2.VideoWriter(
            str(export_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            export_fps,
            (width, height),
        )
        if not writer.isOpened():
            raise RuntimeError("Could not open MP4 writer (OpenCV fallback).")
        init()
        for frame in range(export_num_frames):
            export_update(frame)
            canvas.draw()
            rgba = np.asarray(canvas.buffer_rgba())
            bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
            writer.write(bgr)
        writer.release()
        _try_reencode_mp4_h264_for_web(export_path)

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


def _build_panels() -> None:
    sim_series = _require_runtime()
    if FIG is None:
        raise RuntimeError("Figure has not been initialized.")
    if SHOW_TELEMETRY:
        axes, artists = build_telemetry_panel(FIG, STATIC_SCENE)
        PANELS["telemetry"] = {"axes": axes, "artists": artists}
    if SHOW_REWARD_PLOT:
        axes, artists = build_reward_panel(
            FIG, sim_series.t_s, sim_series.simulation_reward
        )
        PANELS["reward"] = {"axes": axes, "artists": artists}
    if SHOW_TORQUE_PLOT:
        axes, artists = build_torque_panel(FIG, sim_series.t_s, sim_series.wheel_torque_cmd_nm)
        PANELS["torque"] = {"axes": axes, "artists": artists}
    if SHOW_MAIN_PLOT:
        axes, artists = build_main_panel(FIG, STATIC_SCENE)
        PANELS["main"] = {"axes": axes, "artists": artists}
    if SHOW_CLOSEUP:
        axes, artists = build_closeup_panel(FIG, STATIC_SCENE)
        PANELS["closeup"] = {"axes": axes, "artists": artists}
    if SHOW_1D_FIXED_BIRD_VIEW:
        axes, artists = build_1d_fixed_bird_view(FIG, STATIC_SCENE)
        PANELS["fixed_bird"] = {"axes": axes, "artists": artists}
    if SHOW_1D_SAT_VIEW:
        axes, artists = build_1d_sat_view(FIG, STATIC_SCENE)
        PANELS["1d_sat_view"] = {"axes": axes, "artists": artists}


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
        0.995,
        f"2D Satellite Orbit around Earth (h={SAT_ALTITUDE_KM:.0f} km, T={simulation_series.metadata.orbit_period_s/60:.1f} min)",
        color="white",
        ha="center",
        va="top",
        fontsize=RENDER.suptitle_fontsize,
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
