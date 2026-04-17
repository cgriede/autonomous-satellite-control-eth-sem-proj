import argparse
import sys
from pathlib import Path

# Video export must not open a GUI backend.
if "--save-one-pass-30x" in sys.argv:
    import matplotlib

    matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation as mpl_animation
from matplotlib.animation import FuncAnimation

from environment_definition.constants import (
    EARTH_GRAVITATIONAL_PARAMETER,
    EARTH_RADIUS,
    N_PIXELS_Y,
    RENDER,
    SIMULATION,
    UREG as ureg,
)
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE, SATELLITE_ALTITUDE
from simulation.observation_line_constants import OBSERVATION_CLOUD
from simulation.run_simulation import run_simulation
from utils.flight_geometry.line_of_sight import minimum_contact_angle

from ._closeup_view import build_closeup_panel, update_closeup_panel
from ._fixed_bird_view import build_1d_fixed_bird_view, update_1d_fixed_bird_view
from ._main_view import build_main_panel, update_main_panel
from ._satellite_cam_view import build_1d_sat_view, update_1d_sat_view
from ._telemetry import build_telemetry_panel, update_telemetry_panel


SHOW_MAIN_PLOT = True
SHOW_1D_FIXED_BIRD_VIEW = True
SHOW_1D_SAT_VIEW = True
SHOW_CLOSEUP = True
SHOW_TELEMETRY = True

R_EARTH_KM = EARTH_RADIUS.to(ureg.km).magnitude
SAT_ALTITUDE_KM = SATELLITE_ALTITUDE.to(ureg.km).magnitude
R_ORBIT_KM = R_EARTH_KM + SAT_ALTITUDE_KM
THETA_CENTER = SIMULATION.theta_center.to(ureg.rad).magnitude
ALPHA = minimum_contact_angle(observer_height=0.0 * ureg.km, orbit_height=SATELLITE_ALTITUDE)
CONTACT_HALF_ANGLE_DEG = ALPHA.to(ureg.deg).magnitude
MARGIN_DEG = SIMULATION.contact_margin_angle.to(ureg.deg).magnitude
START_ANGLE_DEG = -(CONTACT_HALF_ANGLE_DEG + MARGIN_DEG)
END_ANGLE_DEG = CONTACT_HALF_ANGLE_DEG + MARGIN_DEG
ANIMATION_INTERVAL_MS = SIMULATION.animation_interval.to(ureg.ms).magnitude
SIM_SPEED_MULTIPLIER = float(SIMULATION.default_speed_multiplier)


SIMULATION_SERIES = run_simulation(
    earth_radius=EARTH_RADIUS,
    earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
    satellite=SATELLITE,
    satellite_altitude=SATELLITE_ALTITUDE,
    theta_center_rad=float(THETA_CENTER),
    start_angle_deg=float(START_ANGLE_DEG),
    end_angle_deg=float(END_ANGLE_DEG),
    sat_motion_span_scale=float(SIMULATION.sat_motion_span_scale),
    num_frames=int(SIMULATION.num_frames),
    sat_z_offset_deg=float(SIMULATION.sat_z_offset.to(ureg.deg).magnitude),
    ureg=ureg,
    observer_target_angle_rad=float(np.arctan2(R_EARTH_KM, 0.0)),
    camera_pixel_ray_samples=SIMULATION.camera_pixel_ray_samples,
)

N_CLOUDS = int(SIMULATION_SERIES.cloud_arc_radius_km.shape[1])
N_BINS = int(SIMULATION_SERIES.camera_observation_line_codes.shape[1])

STATIC_SCENE = {
    "R_earth": R_EARTH_KM,
    "R_orbit": R_ORBIT_KM,
    "theta_center": THETA_CENTER,
    "start_angle_deg": START_ANGLE_DEG,
    "end_angle_deg": END_ANGLE_DEG,
    "observer_x": 0.0,
    "observer_y": R_EARTH_KM,
    "observer_pos": np.array([0.0, R_EARTH_KM], dtype=float),
    "cloud_models": [None] * N_CLOUDS,
    "n_clouds": N_CLOUDS,
    "n_bins": N_BINS,
}

FIG = plt.figure(figsize=RENDER.figure_size, facecolor=RENDER.space_background)
SIM_TIME_S = 0.0
PANELS: dict[str, dict] = {}


def _cloud_world_xy_for_frame(sim_idx: int) -> list[dict[str, np.ndarray]]:
    specs: list[dict[str, np.ndarray]] = []
    radii = SIMULATION_SERIES.cloud_arc_radius_km[sim_idx]
    starts = SIMULATION_SERIES.cloud_arc_start_rad[sim_idx]
    ends = SIMULATION_SERIES.cloud_arc_end_rad[sim_idx]
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
    sim_total_s = float(SIMULATION_SERIES.metadata.sim_total_s)
    if wrap_orbit:
        normalized = (sim_time_s / sim_total_s) % 1.0
    else:
        normalized = np.clip(sim_time_s / sim_total_s, 0.0, 1.0)
    return int(np.floor(normalized * (SIMULATION_SERIES.t_s.shape[0] - 1)))


def sample_scene(sim_idx: int) -> dict:
    sat_r = float(SIMULATION_SERIES.radius_km[sim_idx])
    sat_theta = float(SIMULATION_SERIES.theta_orbit_rad[sim_idx])
    sat_pos = np.array([sat_r * np.cos(sat_theta), sat_r * np.sin(sat_theta)], dtype=float)

    z_angle = float(SIMULATION_SERIES.body_z_angle_rad[sim_idx])
    z_axis_dir = np.array([np.cos(z_angle), np.sin(z_angle)], dtype=float)

    k = max(sim_idx + 1, 2)
    theta = SIMULATION_SERIES.theta_orbit_rad[:k]
    radius = SIMULATION_SERIES.radius_km[:k]
    trail_xy = (radius * np.cos(theta), radius * np.sin(theta))

    cone_len = float(SIMULATION.cone_length.to(ureg.km).magnitude * RENDER.cone_length_render_scale)
    cone_half = float(SIMULATION_SERIES.camera_vertical_fov_rad / 2.0)
    cos_h, sin_h = np.cos(cone_half), np.sin(cone_half)
    rot_l = np.array([[cos_h, -sin_h], [sin_h, cos_h]], dtype=float)
    rot_r = np.array([[cos_h, sin_h], [-sin_h, cos_h]], dtype=float)
    edge_l = sat_pos + cone_len * (rot_l @ z_axis_dir)
    edge_r = sat_pos + cone_len * (rot_r @ z_axis_dir)

    camera_gsd_m = float(SIMULATION_SERIES.camera_gsd_m[sim_idx])
    camera_swath_height_km = (N_PIXELS_Y * camera_gsd_m) / 1000.0 if np.isfinite(camera_gsd_m) else float("nan")
    blocked_fraction = float(SIMULATION_SERIES.camera_cloud_blocked_fraction[sim_idx])

    return {
        "sim_idx": sim_idx,
        "sat_pos": sat_pos,
        "z_axis_dir": z_axis_dir,
        "trail_xy": trail_xy,
        "observer_x": STATIC_SCENE["observer_x"],
        "observer_y": STATIC_SCENE["observer_y"],
        "orbit_altitude_km": SAT_ALTITUDE_KM,
        "sim_speed_multiplier": SIM_SPEED_MULTIPLIER,
        "edge_l": edge_l,
        "edge_r": edge_r,
        "cloud_world": _cloud_world_xy_for_frame(sim_idx),
        "ground_left": np.asarray(SIMULATION_SERIES.camera_ground_left_xy_km[sim_idx], dtype=float),
        "ground_right": np.asarray(SIMULATION_SERIES.camera_ground_right_xy_km[sim_idx], dtype=float),
        "camera_codes": np.asarray(SIMULATION_SERIES.camera_observation_line_codes[sim_idx], dtype=np.int8),
        "fixed_codes": np.asarray(SIMULATION_SERIES.fixed_ground_line_codes[sim_idx], dtype=np.int8),
        "center_hit_cloud": bool(SIMULATION_SERIES.camera_center_first_hit_is_cloud[sim_idx]),
        "camera_gsd_m": camera_gsd_m,
        "camera_vfov_deg": float(np.rad2deg(SIMULATION_SERIES.camera_vertical_fov_rad)),
        "camera_swath_height_km": camera_swath_height_km,
        "cloud_blocked_pct": 100.0 * blocked_fraction if np.isfinite(blocked_fraction) else float("nan"),
    }


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


def update(_frame: int) -> list:
    global SIM_TIME_S
    SIM_TIME_S += (ANIMATION_INTERVAL_MS / 1000.0) * SIM_SPEED_MULTIPLIER
    sim_idx = simulation_index_from_time(SIM_TIME_S, wrap_orbit=True)
    scene = sample_scene(sim_idx)
    update_panels(scene)
    return []


def save_one_pass_video_30x_to_project_root() -> Path:
    export_speed_multiplier = float(SIMULATION.export_speed_multiplier)
    export_fps = int(RENDER.export_fps)
    sim_total_s = float(SIMULATION_SERIES.metadata.sim_total_s)
    dt_sim_s = (ANIMATION_INTERVAL_MS / 1000.0) * export_speed_multiplier
    export_num_frames = max(2, int(np.ceil(sim_total_s / dt_sim_s)) + 1)
    export_path = Path(__file__).resolve().parents[2] / RENDER.export_filename

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

    return export_path


def _maximize_interactive_window() -> None:
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
    if SHOW_TELEMETRY:
        axes, artists = build_telemetry_panel(FIG, STATIC_SCENE)
        PANELS["telemetry"] = {"axes": axes, "artists": artists}
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Satellite render and video export")
    parser.add_argument(
        "--save-one-pass-30x",
        action="store_true",
        help="Save one-pass MP4 at 30x speed to project root",
    )
    args = parser.parse_args()

    FIG.text(
        0.5,
        0.995,
        f"2D Satellite Orbit around Earth (h={SAT_ALTITUDE_KM:.0f} km, T={SIMULATION_SERIES.metadata.orbit_period_s/60:.1f} min)",
        color="white",
        ha="center",
        va="top",
        fontsize=RENDER.suptitle_fontsize,
    )

    _build_panels()

    if args.save_one_pass_30x:
        output_path = save_one_pass_video_30x_to_project_root()
        print(f"Saved one-pass video to: {output_path}")
    else:
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
