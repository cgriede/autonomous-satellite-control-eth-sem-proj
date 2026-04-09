import sys

# Video export must not open a GUI backend (can appear "stuck" or block headless runs).
if "--save-one-pass-30x" in sys.argv:
    import matplotlib

    matplotlib.use("Agg")

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import animation as mpl_animation
from matplotlib.colors import to_rgba
from matplotlib.patches import Circle, Polygon, FancyArrowPatch
from matplotlib.widgets import Button
import argparse
import json
import time
from pathlib import Path

try:
    from tqdm import tqdm  # type: ignore[reportMissingImports]
except ImportError:  # pragma: no cover
    tqdm = None  # type: ignore[assignment]

#local imports
from environment_definition.constants import (
    EARTH_GRAVITATIONAL_PARAMETER,
    EARTH_RADIUS,
    RENDER,
    SIMULATION,
    FOCAL_LENGTH,
    N_PIXELS_Y,
    SENSOR_HEIGHT,
    UREG as ureg,
)
from simulation.camera_optics import pinhole_full_fov_rad
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE, SATELLITE_ALTITUDE
from utils.flight_geometry.line_of_sight import minimum_contact_angle
from simulation.camera_2d import simulate_camera_strip_2d
from simulation.run_simulation import run_simulation

# Lazy camera: samples per frame in renderer (not 7000; not 500×2000 at import).
_RENDER_PIXEL_RAY_SAMPLES = 96

#BUG use these for debugging only
SHOW_MAIN_PLOT = False
SHOW_1D_BIRD_VIEW = True
SHOW_CLOSEUP = True
SHOW_TELEMETRY = True

# --- Parameters ---
# Earth radius in kilometers is needed for all geometric calculations.
R_earth = EARTH_RADIUS.to(ureg.km).magnitude
# Satellite altitude in kilometers positions the orbit above Earth.
sat_altitude = SATELLITE_ALTITUDE.to(ureg.km).magnitude
# Orbit radius defines the circular path used by the animation.
R_orbit = R_earth + sat_altitude
# Standard gravitational parameter sets physically realistic orbital speed.
mu_earth = EARTH_GRAVITATIONAL_PARAMETER.to((ureg.km ** 3) / (ureg.s ** 2)).magnitude
# Window center anchors the viewed snippet around nadir overpass.
theta_center = SIMULATION.theta_center.to(ureg.rad).magnitude
# Contact angle defines minimum geometry needed for direct line-of-sight.
alpha = minimum_contact_angle(observer_height=0.0 * ureg.km, orbit_height=SATELLITE_ALTITUDE)
# Contact half-angle in degrees is easier for window parameterization.
contact_half_angle_deg = alpha.to(ureg.deg).magnitude
# Margin widens the window slightly before and after direct contact.
margin_deg = SIMULATION.contact_margin_angle.to(ureg.deg).magnitude
# Start angle sets lower bound of rendered contact-focused window.
start_angle_deg = -(contact_half_angle_deg + margin_deg)
# End angle sets upper bound of rendered contact-focused window.
end_angle_deg = contact_half_angle_deg + margin_deg
# Motion span scale controls how far satellite moves versus visible window.
sat_motion_span_scale = SIMULATION.sat_motion_span_scale
# Frame count controls temporal resolution of animation and exports.
num_frames = SIMULATION.num_frames
# Initial z-offset defines body-axis orientation at simulation start.
sat_z_offset_deg = SIMULATION.sat_z_offset.to(ureg.deg).magnitude
# Human-readable attitude-mode label is shown in the bottom info bar.
sat_body_rotation_rate_label = "torque cmd: +max"
# UI refresh interval sets rendering cadence in milliseconds.
animation_interval_ms = SIMULATION.animation_interval.to(ureg.ms).magnitude
# Speed multiplier scales simulated time versus wall-clock animation time.
sim_speed_multiplier = SIMULATION.default_speed_multiplier
# Running simulation clock accumulates elapsed simulated seconds.
sim_time_s = 0.0
# Playback control state (Pause freezes sim_time_s advance).
paused = False
simulation = None

# --- Set up the figure ---
fig = plt.figure(figsize=RENDER.figure_size, facecolor=RENDER.space_background)

# Clouds configured in simulation constants:
# - height [km] above Earth's surface
# - start_location [deg/rad] Earth-fixed start angle
# - end_location [deg/rad] Earth-fixed end angle
cloud_rng = np.random.default_rng(20260319)



def _sample_cloud_speed_km_s(height_km):
    # Altitude-stratified speed bounds from user-provided weather guidance.
    if height_km < 2.0:
        speed_kmh = cloud_rng.uniform(16.0, 65.0)
    elif height_km < 6.0:
        speed_kmh = cloud_rng.uniform(32.0, 100.0)
    else:
        speed_kmh = cloud_rng.uniform(80.0, 190.0)
    return speed_kmh / 3600.0


cloud_models = []
for cloud in SIMULATION.clouds:
    cloud_height_km = cloud.height.to(ureg.km).magnitude
    start_rad = cloud.start_location.to(ureg.rad).magnitude
    end_rad = cloud.end_location.to(ureg.rad).magnitude
    radius_km = R_earth + cloud_height_km
    speed_km_s = _sample_cloud_speed_km_s(cloud_height_km)
    omega_rad_s = speed_km_s / max(radius_km, 1e-9)
    cloud_models.append(
        {
            "radius_km": radius_km,
            "start_rad_0": start_rad,
            "end_rad_0": end_rad,
            "omega_rad_s": omega_rad_s,
            "noise_amp": float(cloud_rng.uniform(0.12, 0.30)),
            "noise_freq_rad_s": float(cloud_rng.uniform(0.015, 0.05)),
            "noise_phase": float(cloud_rng.uniform(0.0, 2.0 * np.pi)),
        }
    )

# Observer point at Earth's north pole
observer_x, observer_y = 0.0, R_earth
swiss_map = SIMULATION.switzerland_map
swiss_center_lat_deg = float(swiss_map.lat_center_deg)
swiss_center_lon_deg = float(swiss_map.lon_center_deg)
# Observer reference in Swiss inset frame matches observer-relative km (origin).
observer_cross_local = np.array([0.0, 0.0])

#######################################################################################
#END OF CONSTANTS DEFINITION
#######################################################################################

#define the scene dictionary
SCENE = dict(
    R_earth=R_earth,
    R_orbit=R_orbit,
    theta_center=theta_center,
    start_angle_deg=start_angle_deg,
    end_angle_deg=end_angle_deg,
    observer_x=observer_x,
    observer_y=observer_y,
    cloud_models=cloud_models,
    swiss_center_lat_deg= float(swiss_map.lat_center_deg),
    swiss_center_lon_deg= float(swiss_map.lon_center_deg),
    swiss_half_km= float(RENDER.swiss_inset_half_extent_km.to(ureg.km).magnitude),
    observer_pos = np.array([observer_x, observer_y], dtype=float)

)

main_ax = None

def build_main_panel(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.main_axes_rect)

    axes = {"main": ax}
    artists: dict = {}

    R_earth = scene["R_earth"]
    R_orbit = scene["R_orbit"]
    theta_center = scene["theta_center"]
    start_angle_deg = scene["start_angle_deg"]
    end_angle_deg = scene["end_angle_deg"]
    observer_x = scene["observer_x"]
    observer_y = scene["observer_y"]
    cloud_models = scene["cloud_models"]

    # framing
    theta_window = np.linspace(
        theta_center + np.deg2rad(start_angle_deg),
        theta_center + np.deg2rad(end_angle_deg),
        721,
    )
    x_render = R_orbit * np.cos(theta_window)
    y_render = R_orbit * np.sin(theta_window)
    x_min_orbit = float(np.min(x_render))
    x_max_orbit = float(np.max(x_render))
    x_min_earth = float(np.clip(x_min_orbit, -R_earth, R_earth))
    x_max_earth = float(np.clip(x_max_orbit, -R_earth, R_earth))
    earth_cap_y_min = min(
        np.sqrt(max(R_earth**2 - x_min_earth**2, 0.0)),
        np.sqrt(max(R_earth**2 - x_max_earth**2, 0.0)),
    )
    zoom_pad_x = RENDER.zoom_pad_x.to(ureg.km).magnitude
    zoom_pad_y_bottom = RENDER.zoom_pad_y_bottom.to(ureg.km).magnitude
    zoom_pad_y_top = RENDER.zoom_pad_y_top.to(ureg.km).magnitude

    ax.set_xlim(x_min_orbit - zoom_pad_x, x_max_orbit + zoom_pad_x)
    ax.set_ylim(earth_cap_y_min - zoom_pad_y_bottom, float(np.max(y_render)) + zoom_pad_y_top)
    ax.set_aspect("equal", adjustable="box")
    ax.set_facecolor(RENDER.space_background)
    ax.axis("off")

    # static legend (leave as-is)
    legend_x0, legend_y0 = 0.05, 0.08
    legend_len_x, legend_len_y = 0.11, 0.095
    legend_z_dot_x = legend_x0 - 0.042
    ax.annotate(
        "", xy=(legend_x0 + legend_len_x, legend_y0), xycoords=ax.transAxes,
        xytext=(legend_x0, legend_y0), textcoords=ax.transAxes,
        arrowprops=dict(arrowstyle="->", color=RENDER.info_text_color, lw=1.5),
        zorder=RENDER.zorder_info,
    )
    ax.annotate(
        "", xy=(legend_x0, legend_y0 + legend_len_y), xycoords=ax.transAxes,
        xytext=(legend_x0, legend_y0), textcoords=ax.transAxes,
        arrowprops=dict(arrowstyle="->", color=RENDER.info_text_color, lw=1.5),
        zorder=RENDER.zorder_info,
    )
    ax.plot([legend_z_dot_x], [legend_y0 + 0.012], marker="o", linestyle="None",
            markersize=6, markerfacecolor="none", markeredgecolor=RENDER.info_text_color,
            transform=ax.transAxes, zorder=RENDER.zorder_info)
    ax.plot([legend_z_dot_x], [legend_y0 - 0.034], marker="x", linestyle="None",
            markersize=6, color=RENDER.info_text_color, transform=ax.transAxes,
            zorder=RENDER.zorder_info)
    ax.text(legend_z_dot_x - 0.028, legend_y0 - 0.01, "z", transform=ax.transAxes,
            color=RENDER.info_text_color, fontsize=8, ha="right", va="center",
            zorder=RENDER.zorder_info)
    ax.text(legend_x0 + legend_len_x + 0.005, legend_y0, "x", transform=ax.transAxes,
            color=RENDER.info_text_color, fontsize=8, ha="left", va="bottom",
            zorder=RENDER.zorder_info)
    ax.text(legend_x0, legend_y0 + legend_len_y + 0.005, "y", transform=ax.transAxes,
            color=RENDER.info_text_color, fontsize=8, ha="left", va="bottom",
            zorder=RENDER.zorder_info)
    ax.text(legend_x0 + legend_len_x * 0.45, legend_y0 - 0.038, "XY plane (z=0)",
            transform=ax.transAxes, color=RENDER.info_text_color, fontsize=7,
            ha="left", va="top", zorder=RENDER.zorder_info)

    # static stars
    star_rng = np.random.default_rng(RENDER.star_rng_seed)
    num_stars = RENDER.num_stars
    star_x = star_rng.uniform(ax.get_xlim()[0], ax.get_xlim()[1], num_stars)
    star_y = star_rng.uniform(ax.get_ylim()[0], ax.get_ylim()[1], num_stars)
    star_sizes = star_rng.uniform(RENDER.star_size_min, RENDER.star_size_max, num_stars)
    star_alpha = star_rng.uniform(RENDER.star_alpha_min, RENDER.star_alpha_max, num_stars)
    star_colors = np.ones((num_stars, 4))
    star_colors[:, :3] = RENDER.star_color_rgb
    star_colors[:, 3] = star_alpha
    ax.scatter(star_x, star_y, s=star_sizes, c=star_colors, linewidths=0, zorder=RENDER.zorder_stars)

    # static earth
    earth_res = RENDER.earth_res
    earth_x = np.linspace(-R_earth, R_earth, earth_res)
    earth_y = np.linspace(-R_earth, R_earth, earth_res)
    earth_X, earth_Y = np.meshgrid(earth_x, earth_y)
    earth_r2 = (earth_X / R_earth) ** 2 + (earth_Y / R_earth) ** 2
    earth_mask = earth_r2 <= 1.0
    earth_Z = np.sqrt(np.clip(1.0 - earth_r2, 0.0, 1.0))
    light_dir = np.array(RENDER.light_dir)
    light_dir = light_dir / np.linalg.norm(light_dir)
    earth_intensity = np.clip(
        earth_X / R_earth * light_dir[0] + earth_Y / R_earth * light_dir[1] + earth_Z * light_dir[2],
        0.0, 1.0
    )
    earth_dark = np.array(RENDER.earth_dark_rgb)
    earth_bright = np.array(RENDER.earth_bright_rgb)
    earth_rgb = earth_dark + earth_intensity[..., None] * (earth_bright - earth_dark)
    earth_alpha = earth_mask.astype(float)
    earth_rgba = np.dstack((earth_rgb, earth_alpha))
    ax.imshow(
        earth_rgba, extent=(-R_earth, R_earth, -R_earth, R_earth),
        origin="lower", interpolation="bilinear", zorder=RENDER.zorder_earth
    )
    ax.add_patch(Circle(
        (0, 0), R_earth, fill=False, edgecolor=RENDER.earth_outline_color,
        linewidth=RENDER.earth_outline_linewidth, alpha=RENDER.earth_outline_alpha,
        zorder=RENDER.zorder_earth_outline
    ))

    # static observer marker
    ax.plot([observer_x], [observer_y], marker="x", color=RENDER.observer_color,
            markersize=RENDER.observer_marker_size * RENDER.observer_marker_render_scale,
            markeredgewidth=RENDER.observer_marker_edge_width, zorder=RENDER.zorder_observer)

    # dynamic artists (returned)
    artists["sat"], = ax.plot([], [], RENDER.sat_marker_style, markersize=RENDER.sat_marker_size)
    artists["obs_to_sat"], = ax.plot([], [], linestyle="--", color=RENDER.los_color,
                                     linewidth=RENDER.los_linewidth, alpha=RENDER.los_alpha,
                                     zorder=RENDER.zorder_los)
    artists["trail"], = ax.plot([], [], RENDER.trail_style, linewidth=RENDER.trail_linewidth,
                                alpha=RENDER.trail_alpha)

    # cone placeholder (update with .set_xy in set_scene_at_index)
    artists["cone"] = Polygon([[0, 0], [0, 0], [0, 0]], closed=True,
                              facecolor=RENDER.cone_color, edgecolor=RENDER.cone_color,
                              alpha=RENDER.cone_alpha, zorder=RENDER.zorder_los)
    ax.add_patch(artists["cone"])
        
    # --- dynamic artists (returned) ---
    artists["sat"], = ax.plot([], [], RENDER.sat_marker_style,
                            markersize=RENDER.sat_marker_size, label="Satellite")

    artists["obs_to_sat"], = ax.plot([], [], linestyle="--", color=RENDER.los_color,
                                    linewidth=RENDER.los_linewidth, alpha=RENDER.los_alpha,
                                    zorder=RENDER.zorder_los)

    artists["trail"], = ax.plot([], [], RENDER.trail_style,
                                linewidth=RENDER.trail_linewidth, alpha=RENDER.trail_alpha)

    # cone params should be stored (needed in update)
    _vertical_fov_rad = pinhole_full_fov_rad(sensor_dim=SENSOR_HEIGHT, focal_length=FOCAL_LENGTH)
    artists["cone_half_angle_rad"] = float(_vertical_fov_rad.to(ureg.rad).magnitude / 2.0)
    artists["cone_length_km"] = SIMULATION.cone_length.to(ureg.km).magnitude * RENDER.cone_length_render_scale

    artists["cone"] = Polygon([[0, 0], [0, 0], [0, 0]],
                            closed=True, facecolor=RENDER.cone_color, edgecolor=RENDER.cone_color,
                            alpha=RENDER.cone_alpha)
    ax.add_patch(artists["cone"])

    # z-axis indicator (also dynamic)
    artists["z_axis_length_km"] = SIMULATION.z_axis_length.to(ureg.km).magnitude
    artists["z_axis_arrow"] = FancyArrowPatch((0, 0), (0, 0),
                                            arrowstyle="-|>", mutation_scale=RENDER.z_arrow_mutation_scale,
                                            linewidth=RENDER.z_arrow_linewidth,
                                            color=RENDER.z_arrow_color, alpha=RENDER.z_arrow_alpha,
                                            zorder=RENDER.zorder_z_axis)
    ax.add_patch(artists["z_axis_arrow"])

    artists["z_axis_label"] = ax.text(0, 0, RENDER.z_label_text,
                                    color=RENDER.z_label_color, fontsize=RENDER.z_label_fontsize,
                                    weight=RENDER.z_label_weight, zorder=RENDER.zorder_z_label)

    # clouds (dynamic lines)
    artists["cloud_glow"] = []
    artists["cloud_core"] = []
    for _ in cloud_models:
        glow, = ax.plot([], [], color="#cfefff",
                        linewidth=RENDER.cloud_linewidth * 2.4,
                        alpha=min(1.0, RENDER.cloud_alpha * 0.23),
                        solid_capstyle="round",
                        zorder=RENDER.zorder_cloud - 1)
        core, = ax.plot([], [], color=RENDER.cloud_color,
                        linewidth=RENDER.cloud_linewidth,
                        alpha=RENDER.cloud_alpha,
                        solid_capstyle="round",
                        zorder=RENDER.zorder_cloud)
        artists["cloud_glow"].append(glow)
        artists["cloud_core"].append(core)

    return axes, artists

def build_1d_bird_view(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.swiss_inset_axes_rect)

    axes = {"swiss": ax}
    artists: dict = {}

    cloud_models = scene["cloud_models"]
    swiss_center_lat_deg = scene["swiss_center_lat_deg"]
    swiss_center_lon_deg = scene["swiss_center_lon_deg"]
    observer_cross_local = scene.get("observer_cross_local", np.array([0.0, 0.0], dtype=float))

    swiss_half_km = float(RENDER.swiss_inset_half_extent_km.to(ureg.km).magnitude)
    swiss_full_km = int(round(2.0 * swiss_half_km))
    inset_range_km = float(swiss_half_km)

    ax.set_facecolor(RENDER.space_background)
    ax.set_aspect("auto", adjustable="box")
    ax.set_xlim(-inset_range_km, inset_range_km)
    ax.set_ylim(-inset_range_km, inset_range_km)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor(RENDER.info_text_color)
        spine.set_linewidth(1.0)

    # 1D strip config (keep in artists so update code can access)
    artists["BINS"] = 240
    artists["H"] = 20  # stripe thickness in pixels
    artists["BAND_HALF_KM"] = 20.0
    artists["RANGE_KM"] = inset_range_km

    artists["RGBA_GROUND"] = to_rgba(RENDER.closeup_ground_line_color, 1.0)
    artists["RGBA_CONE"] = to_rgba("#1E90FF", 1.0)
    artists["RGBA_CLOUD"] = to_rgba("white", 1.0)
    artists["RGBA_OBSERVER"] = to_rgba(RENDER.observer_color, 1.0)

    bins = artists["BINS"]
    H = artists["H"]
    band_half = artists["BAND_HALF_KM"]

    artists["img"] = ax.imshow(
        np.zeros((H, bins, 4), dtype=float),
        extent=(-inset_range_km, inset_range_km, -band_half, band_half),
        origin="lower",
        interpolation="none",
        aspect="auto",
        zorder=1,
    )

    artists["obs_bin"] = int(round((bins - 1) * 0.5))
    artists["x_bins"] = np.linspace(-inset_range_km, inset_range_km, bins)
    artists["cloud_x_samples"] = [None for _ in cloud_models]
    artists["cloud_y_samples"] = [None for _ in cloud_models]

    label_z = max(RENDER.zorder_inset_cloud_core, RENDER.zorder_info) + 1
    ax.text(
        0.02, 0.98,
        f"Swiss {swiss_full_km}×{swiss_full_km} km\n{swiss_center_lat_deg:.2f}N {swiss_center_lon_deg:.2f}E",
        transform=ax.transAxes,
        color=RENDER.info_text_color,
        fontsize=8,
        va="top",
        ha="left",
        linespacing=1.12,
        zorder=label_z,
    )
    ax.text(
        0.02, 0.02,
        "1D view (in-plane y)",
        transform=ax.transAxes,
        color=RENDER.info_text_color,
        fontsize=7,
        va="bottom",
        ha="left",
        zorder=label_z,
    )

    # optional marker (kept hidden; observer is drawn into strip)
    artists["observer_marker"], = ax.plot(
        [observer_cross_local[0]],
        [observer_cross_local[1]],
        marker="x",
        color=RENDER.observer_color,
        markersize=6 * RENDER.observer_marker_render_scale,
        markeredgewidth=1.2,
        zorder=RENDER.zorder_inset_observer,
    )
    artists["observer_marker"].set_visible(False)

    # footprint/hit/centerline placeholders (kept hidden for now)
    artists["footprint"] = Polygon(
        np.zeros((4, 2)),
        closed=True,
        facecolor=to_rgba(RENDER.cone_color, RENDER.inset_footprint_fill_alpha),
        edgecolor=RENDER.cone_color,
        linewidth=RENDER.inset_footprint_edge_linewidth,
        alpha=1.0,
        zorder=RENDER.zorder_inset_footprint,
    )
    ax.add_patch(artists["footprint"])
    artists["footprint"].set_visible(False)

    artists["hit"], = ax.plot([], [], marker="o", color="yellow", markersize=4,
                              linestyle="None", zorder=RENDER.zorder_inset_hit)
    artists["hit"].set_visible(False)

    artists["centerline"], = ax.plot([], [], color=RENDER.z_arrow_color, linewidth=1.2,
                                     alpha=0.0, zorder=RENDER.zorder_inset_centerline)
    artists["centerline"].set_visible(False)

    # inset cloud artists (kept hidden until you want to show them)
    artists["cloud_glow"] = []
    artists["cloud_core"] = []
    for _ in cloud_models:
        g, = ax.plot([], [], color="#cfefff",
                     linewidth=RENDER.cloud_linewidth * 2.0,
                     alpha=min(1.0, RENDER.cloud_alpha * 0.25),
                     solid_capstyle="round",
                     zorder=RENDER.zorder_inset_cloud_glow)
        c, = ax.plot([], [], color=RENDER.cloud_color,
                     linewidth=RENDER.cloud_linewidth,
                     alpha=RENDER.cloud_alpha,
                     solid_capstyle="round",
                     zorder=RENDER.zorder_inset_cloud_core)
        g.set_visible(False)
        c.set_visible(False)
        artists["cloud_glow"].append(g)
        artists["cloud_core"].append(c)

    return axes, artists

def build_closeup_panel(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.closeup_axes_rect)

    axes = {"closeup": ax}
    artists: dict = {}

    observer_x = scene["observer_x"]
    observer_y = scene["observer_y"]
    cloud_models = scene["cloud_models"]

    ax.set_facecolor(RENDER.space_background)
    ax.set_aspect("equal", adjustable="box")

    closeup_half_window = (30.0 * ureg.km).to(ureg.km).magnitude
    ax.set_xlim(-closeup_half_window, closeup_half_window)
    ax.set_ylim(-5.0, 25.0)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor(RENDER.info_text_color)
        spine.set_linewidth(1.0)

    ax.axhline(
        0.0,
        color=RENDER.closeup_ground_line_color,
        linewidth=RENDER.closeup_ground_line_linewidth,
        zorder=RENDER.zorder_closeup_ground,
    )

    # store projector so update code can reuse it
    def project_xy_to_closeup(x_world_km: float, y_world_km: float):
        return (x_world_km - observer_x, y_world_km - observer_y)

    artists["project"] = project_xy_to_closeup

    ax.text(
        0.02, 0.98, "Observer + Cloud Plane Close-up",
        transform=ax.transAxes, color=RENDER.info_text_color,
        fontsize=8, va="top", ha="left",
    )
    ax.text(
        0.02, 0.02, "YZ plane (x=0)",
        transform=ax.transAxes, color=RENDER.info_text_color,
        fontsize=7, va="bottom", ha="left",
    )

    # static observer at origin in closeup coords
    ax.plot(
        [0.0], [0.0],
        marker="x", color=RENDER.observer_color,
        markersize=RENDER.observer_marker_size * RENDER.observer_marker_render_scale,
        markeredgewidth=RENDER.observer_marker_edge_width,
        zorder=RENDER.zorder_closeup_observer,
    )

    # dynamic: cone + hit marker + LOS
    artists["cone"] = Polygon(
        [[0, 0], [0, 0], [0, 0]],
        closed=True,
        facecolor=RENDER.cone_color,
        edgecolor=RENDER.cone_color,
        linewidth=1.0,
        alpha=RENDER.cone_alpha,
        zorder=RENDER.zorder_closeup_cone,
    )
    ax.add_patch(artists["cone"])

    artists["hit"], = ax.plot(
        [], [], marker="o", color="yellow", markersize=4,
        linestyle="None", zorder=RENDER.zorder_closeup_hit,
    )

    artists["obs_to_hit"], = ax.plot(
        [], [], linestyle="--", color=RENDER.los_color,
        linewidth=RENDER.los_linewidth, alpha=RENDER.los_alpha,
        zorder=RENDER.zorder_closeup_hit,
    )

    # dynamic: cloud arcs in closeup
    artists["cloud_glow"] = []
    artists["cloud_core"] = []
    for _ in cloud_models:
        g, = ax.plot(
            [], [],
            color="#cfefff",
            linewidth=RENDER.cloud_linewidth * 1.8,
            alpha=0.0,
            zorder=RENDER.zorder_closeup_cloud_glow,
        )
        c, = ax.plot(
            [], [],
            color=RENDER.cloud_color,
            linewidth=RENDER.cloud_linewidth,
            alpha=RENDER.cloud_alpha,
            zorder=RENDER.zorder_closeup_cloud_core,
        )
        artists["cloud_glow"].append(g)
        artists["cloud_core"].append(c)

    return axes, artists

def build_telemetry_panel(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.telemetry_axes_rect)

    axes = {"telemetry": ax}
    artists: dict = {}

    ax.set_facecolor(RENDER.space_background)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor(RENDER.info_text_color)
        sp.set_linewidth(0.8)

    artists["text"] = ax.text(
        0.04,
        0.98,
        "",
        transform=ax.transAxes,
        color=RENDER.info_text_color,
        fontsize=RENDER.info_panel_fontsize,
        family=RENDER.info_panel_fontfamily,
        va="top",
        ha="left",
        linespacing=1.14,
    )

    return axes, artists

def set_sim_speed(multiplier):
    global sim_speed_multiplier
    sim_speed_multiplier = float(multiplier)

def toggle_pause(_event=None):
    global paused, pause_button
    paused = not paused
    # Update label text if the button object exists yet.
    if pause_button is not None:
        pause_button.label.set_text("Resume" if paused else "Pause")

def set_sat_body_rotation_rate(rate, unit="arcsec"):
    """Assign constant body rotation speed for +z axis."""
    global sat_body_rotation_rate_rad_s, sat_body_rotation_rate_label
    if unit == "arcsec":
        sat_body_rotation_rate_rad_s = np.deg2rad(float(rate) / 3600.0)
        sat_body_rotation_rate_label = f"{float(rate):.1f} arcsec/s"
    elif unit == "arcmin":
        sat_body_rotation_rate_rad_s = np.deg2rad(float(rate) / 60.0)
        sat_body_rotation_rate_label = f"{float(rate):.1f} arcmin/s"
    elif unit == "deg":
        sat_body_rotation_rate_rad_s = np.deg2rad(float(rate))
        sat_body_rotation_rate_label = f"{float(rate):.3f} deg/s"
    else:
        raise ValueError("unit must be one of: arcsec, arcmin, deg")


simulation = run_simulation(
    earth_radius=EARTH_RADIUS,
    earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
    satellite=SATELLITE,
    satellite_altitude=SATELLITE_ALTITUDE,
    theta_center_rad=float(theta_center),
    start_angle_deg=float(start_angle_deg),
    end_angle_deg=float(end_angle_deg),
    sat_motion_span_scale=float(sat_motion_span_scale),
    num_frames=int(num_frames),
    sat_z_offset_deg=float(sat_z_offset_deg),
    ureg=ureg,
)
orbit_period_s = simulation.metadata.orbit_period_s

def build_controls_panel(fig: plt.Figure) -> dict:
    artists = {}

    button_specs = list(RENDER.speed_button_specs)

    _transport = RENDER.transport_bar_rect
    _btn_h = RENDER.speed_button_height
    _btn_w = RENDER.speed_button_width
    _pause_w = 0.072
    _btn_gap = 0.008

    _n_speed = len(button_specs)
    _total_w = _pause_w + _n_speed * _btn_w + _n_speed * _btn_gap
    _start_x = _transport[0] + max(0.0, (_transport[2] - _total_w) * 0.5)
    _btn_y = _transport[1] + max(0.0, (_transport[3] - _btn_h) * 0.5)

    cx = _start_x

    # Pause button
    pause_ax = fig.add_axes([cx, _btn_y, _pause_w, _btn_h])
    pause_ax.set_facecolor(RENDER.space_background)
    artists["pause"] = Button(
        pause_ax,
        "Pause",
        color=RENDER.speed_button_color,
        hovercolor=RENDER.speed_button_hover_color,
    )
    artists["pause"].label.set_color(RENDER.speed_button_label_color)
    artists["pause"].label.set_fontsize(RENDER.speed_button_label_fontsize)
    artists["pause"].on_clicked(toggle_pause)

    cx += _pause_w + _btn_gap

    # Speed buttons
    artists["speed"] = []
    for label, multiplier, _ in button_specs:
        ax_btn = fig.add_axes([cx, _btn_y, _btn_w, _btn_h])
        ax_btn.set_facecolor(RENDER.space_background)

        btn = Button(
            ax_btn,
            label,
            color=RENDER.speed_button_color,
            hovercolor=RENDER.speed_button_hover_color,
        )
        btn.label.set_color(RENDER.speed_button_label_color)
        btn.label.set_fontsize(RENDER.speed_button_label_fontsize)
        btn.on_clicked(lambda _event, m=multiplier: set_sim_speed(m))

        artists["speed"].append(btn)
        cx += _btn_w + _btn_gap

    return artists

def simulation_index_from_time(sim_time_local, wrap_orbit=True):
    sim_total_s = simulation.metadata.sim_total_s
    if wrap_orbit:
        normalized = (sim_time_local / sim_total_s) % 1.0
    else:
        normalized = np.clip(sim_time_local / sim_total_s, 0.0, 1.0)
    return int(np.floor(normalized * (num_frames - 1)))


def _angle_in_arc(angle_rad, start_rad, end_rad):
    two_pi = 2.0 * np.pi
    angle = angle_rad % two_pi
    start = start_rad % two_pi
    end = end_rad % two_pi
    if start <= end:
        return start <= angle <= end
    return angle >= start or angle <= end


def _ray_circle_intersection_distance(ray_origin, ray_dir, radius_km):
    b = 2.0 * float(np.dot(ray_origin, ray_dir))
    c = float(np.dot(ray_origin, ray_origin) - radius_km**2)
    disc = b * b - 4.0 * c
    if disc < 0.0:
        return None
    sqrt_disc = float(np.sqrt(disc))
    t1 = (-b - sqrt_disc) / 2.0
    t2 = (-b + sqrt_disc) / 2.0
    candidates = [t for t in (t1, t2) if t > 1e-9]
    if not candidates:
        return None
    return min(candidates)



def observer_local_km_to_geo(
    local_xy_km: np.ndarray[np.floating],
    lat0_deg: float,
    lon0_deg: float,
) -> tuple[float, float]:
    east_km, north_km = float(local_xy_km[0]), float(local_xy_km[1])
    lat_deg = lat0_deg + north_km / 110.574
    lon_scale_km = max(111.320 * np.cos(np.deg2rad(lat_deg)), 1e-6)
    lon_deg = lon0_deg + east_km / lon_scale_km
    return lat_deg, lon_deg


def project_to_frame(
    local_xy_km: np.ndarray[np.floating],
    half_extent_km: float,
) -> np.ndarray[np.floating]:
    h = float(half_extent_km)
    return np.array([np.clip(local_xy_km[0], -h, h), np.clip(local_xy_km[1], -h, h)], dtype=float)



def _inset_swiss_footprint_vertices_xy(left_local_km, right_local_km, half_swath_km):
    """Rectangle in observer-local km: chord = left→right, half-width along perpendicular (swath/2).

    Note: returns *unclipped* observer-local vertices (do not project/clip to the swiss inset range here).
    The caller (1D inset rendering) can decide how to clip/map to pixels.
    """
    chord = np.asarray(right_local_km, dtype=float) - np.asarray(left_local_km, dtype=float)
    L = float(np.linalg.norm(chord))
    if L < 1e-9:
        return None
    e = chord / L
    e_perp = np.array([-e[1], e[0]])
    h = float(half_swath_km)
    p0 = np.asarray(left_local_km, dtype=float) + h * e_perp
    p1 = np.asarray(right_local_km, dtype=float) + h * e_perp
    p2 = np.asarray(right_local_km, dtype=float) - h * e_perp
    p3 = np.asarray(left_local_km, dtype=float) - h * e_perp
    return np.array([p0, p1, p2, p3], dtype=float)


def _sample_swiss_elevation_m(lat_deg, lon_deg):
    # Deterministic terrain sampler over the Swiss patch (replace with DEM lookup later).
    peaks = [
        (46.55, 8.00, 2100.0, 0.28),
        (46.30, 9.10, 1600.0, 0.22),
        (46.85, 7.60, 1300.0, 0.25),
    ]
    elev_m = 450.0
    for peak_lat, peak_lon, amplitude_m, sigma_deg in peaks:
        d2 = (lat_deg - peak_lat) ** 2 + (lon_deg - peak_lon) ** 2
        elev_m += amplitude_m * np.exp(-d2 / (2.0 * sigma_deg**2))
    return float(elev_m)


from typing import List, Dict
import numpy as np
from numpy.typing import NDArray


def _compute_cloud_arcs_at_time(
    sim_time_s: float,
    cloud_models: List[dict],
    observer_pos_xy_km: NDArray[np.floating],
    sim_total_s: float,
) -> List[Dict[str, object]]:
    """
    Compute cloud arc geometry at a given simulation time.

    Returns per-cloud specs used by renderers (main / inset / closeup).
    No rendering side-effects.
    """

    growth_phase = sim_time_s / max(sim_total_s, 1e-9)
    cloud_growth = 1.0 + (RENDER.cloud_growth_max_span_scale - 1.0) * np.clip(growth_phase, 0.0, 1.0)
    cloud_thickness = 1.0 + (RENDER.cloud_growth_linewidth_scale - 1.0) * np.clip(growth_phase, 0.0, 1.0)

    observer_angle_rad = float(np.arctan2(observer_pos_xy_km[1], observer_pos_xy_km[0]))

    cloud_arc_specs: List[Dict[str, object]] = []

    for model in cloud_models:
        base_start = model["start_rad_0"]
        base_end = model["end_rad_0"]

        angular_width = float(base_end - base_start) * cloud_growth
        start = observer_angle_rad - 0.5 * angular_width
        end = observer_angle_rad + 0.5 * angular_width

        theta = np.linspace(start, end, RENDER.cloud_segment_points)
        radius = float(model["radius_km"])

        x = radius * np.cos(theta)
        y = radius * np.sin(theta)

        cloud_arc_specs.append(
            {
                "radius": radius,
                "theta": theta,
                "x": x,
                "y": y,
                "start": start,
                "end": end,
                "growth": cloud_thickness,
            }
        )

    return cloud_arc_specs



def _nearest_surface_hit(ray_origin, ray_dir, cloud_arc_specs):
    best_t = _ray_circle_intersection_distance(ray_origin, ray_dir, R_earth)
    best_point = ray_origin + best_t * ray_dir if best_t is not None else None
    for cloud_spec in cloud_arc_specs:
        t_cloud = _ray_circle_intersection_distance(ray_origin, ray_dir, cloud_spec["radius"])
        if t_cloud is None:
            continue
        hit_point = ray_origin + t_cloud * ray_dir
        hit_angle = np.arctan2(hit_point[1], hit_point[0])
        if _angle_in_arc(hit_angle, cloud_spec["start"], cloud_spec["end"]):
            if best_t is None or t_cloud < best_t:
                best_t = t_cloud
                best_point = hit_point
    return best_t, best_point

def init():
    global sim_time_s
    sim_time_s = 0.0

    # --- MAIN PANEL ---
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

    # --- SWISS INSET ---
    if "1d_bird" in PANELS:
        a = PANELS["1d_bird"]["artists"]

        img = np.zeros((a["H"], a["BINS"], 4), dtype=float)
        img[:, :, :] = np.array(a["RGBA_GROUND"], dtype=float)
        img[:, a["obs_bin"], :] = np.array(a["RGBA_OBSERVER"], dtype=float)
        a["img"].set_data(img)

        a["footprint"].set_visible(False)
        a["hit"].set_data([], [])
        a["centerline"].set_data([], [])

        for g, c in zip(a["cloud_glow"], a["cloud_core"]):
            g.set_data([], [])
            c.set_data([], [])

    # --- CLOSEUP ---
    if "closeup" in PANELS:
        a = PANELS["closeup"]["artists"]
        a["cone"].set_xy([[0, 0], [0, 0], [0, 0]])
        a["hit"].set_data([], [])
        a["obs_to_hit"].set_data([], [])
        for g, c in zip(a["cloud_glow"], a["cloud_core"]):
            g.set_data([], [])
            c.set_data([], [])

    # --- TELEMETRY ---
    if "telemetry" in PANELS:
        PANELS["telemetry"]["artists"]["text"].set_text("")

    return []

def set_scene_at_index(sim_idx: int, speed_label=None):
    sim_time_local = float(simulation.t_s[sim_idx])

    sat_r = simulation.radius_km[sim_idx]
    sat_theta = simulation.theta_orbit_rad[sim_idx]
    sat_pos = np.array([sat_r * np.cos(sat_theta), sat_r * np.sin(sat_theta)], dtype=float)

    cloud_arc_specs = _compute_cloud_arcs_at_time(
        sim_time_local,
        SCENE["cloud_models"],
        SCENE["observer_pos"],
        simulation.metadata.sim_total_s
        )

    # body z dir (simulated)
    z_angle_rad = float(simulation.body_z_angle_rad[sim_idx])
    z_axis_dir = np.array([np.cos(z_angle_rad), np.sin(z_angle_rad)], dtype=float)



    # camera sim (shared state, no artists)
    try:
        cam = simulate_camera_strip_2d(
            sat_pos_xy_km=sat_pos,
            boresight_dir_unit_xy=z_axis_dir,
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=SCENE["R_earth"],
            sim_time_s=sim_time_local,
            sim_total_s=float(simulation.metadata.sim_total_s),
            pixel_ray_samples=_RENDER_PIXEL_RAY_SAMPLES,
        )
    except Exception:
        cam = None
    
    if cam is not None:
        center_local = cam.ground_center_xy_km
        half_km = SCENE["swiss_half_km"]
        center_local_frame = project_to_frame(center_local, half_km)

    # ---- MAIN panel artists ----
    if "main" in PANELS:
        a = PANELS["main"]["artists"]
        a["sat"].set_data([sat_pos[0]], [sat_pos[1]])
        a["obs_to_sat"].set_data([SCENE["observer_x"], sat_pos[0]], [SCENE["observer_y"], sat_pos[1]])

        trail_end = max(sim_idx + 1, 2)
        tt = simulation.theta_orbit_rad[:trail_end]
        rr = simulation.radius_km[:trail_end]
        a["trail"].set_data(rr * np.cos(tt), rr * np.sin(tt))

        # cone
        cos_h, sin_h = np.cos(a["cone_half_angle_rad"]), np.sin(a["cone_half_angle_rad"])
        rot_l = np.array([[cos_h, -sin_h], [sin_h, cos_h]])
        rot_r = np.array([[cos_h, sin_h], [-sin_h, cos_h]])
        edge_l = sat_pos + a["cone_length_km"] * (rot_l @ z_axis_dir)
        edge_r = sat_pos + a["cone_length_km"] * (rot_r @ z_axis_dir)
        a["cone"].set_xy([sat_pos, edge_l, edge_r])

        # z axis
        tip = sat_pos + a["z_axis_length_km"] * z_axis_dir
        a["z_axis_arrow"].set_positions((sat_pos[0], sat_pos[1]), (tip[0], tip[1]))
        label_pos = tip + float(RENDER.z_label_offset.to(ureg.km).magnitude) * z_axis_dir
        a["z_axis_label"].set_position((label_pos[0], label_pos[1]))

        # main clouds
        for i, spec in enumerate(cloud_arc_specs):
            th = spec["theta"]
            r = spec["radius"]
            x = r * np.cos(th)
            y = r * np.sin(th)
            a["cloud_glow"][i].set_data(x, y)
            a["cloud_core"][i].set_data(x, y)

    # ---- CLOSEUP panel artists ----
    if "closeup" in PANELS:
        a = PANELS["closeup"]["artists"]
        proj = a["project"]

        # cone in closeup coords (use same edges if main exists; else recompute)
        if "main" in PANELS:
            y0, z0 = proj(sat_pos[0], sat_pos[1])
            yl, zl = proj(edge_l[0], edge_l[1])
            yr, zr = proj(edge_r[0], edge_r[1])
            a["cone"].set_xy([[y0, z0], [yl, zl], [yr, zr]])

        # LOS (observer->satellite in this projection)
        y0, z0 = proj(sat_pos[0], sat_pos[1])
        a["obs_to_hit"].set_data([0.0, float(y0)], [0.0, float(z0)])

        # clouds in closeup (project points)
        for i, spec in enumerate(cloud_arc_specs):
            th = spec["theta"]
            r = spec["radius"]
            x = r * np.cos(th)
            y = r * np.sin(th)
            yl, zl = proj(x, y)
            a["cloud_glow"][i].set_data(yl, zl)
            a["cloud_core"][i].set_data(yl, zl)

    # ---- 1D bird view panel artists ----
    if "1d_bird" in PANELS:
        a = PANELS["1d_bird"]["artists"]
        # keep your existing 1D update logic, just replace globals by a[...] and SCENE[...]
        # minimum “looks alive” reset/update:
        img = np.zeros((a["H"], a["BINS"], 4), dtype=float)
        img[:, :, :] = np.array(a["RGBA_GROUND"], dtype=float)
        img[:, a["obs_bin"], :] = np.array(a["RGBA_OBSERVER"], dtype=float)
        a["img"].set_data(img)

    # ---- TELEMETRY ----
    if "telemetry" in PANELS:
        t = PANELS["telemetry"]["artists"]["text"]
        speed_for_text = sim_speed_multiplier if speed_label is None else speed_label
        t.set_text(f"t={sim_time_local:8.2f}s\nspeed={speed_for_text:.0f}x\nsat=({sat_pos[0]:.1f},{sat_pos[1]:.1f})")

    return []

def update(frame):
    global sim_time_s
    if not paused:
        sim_time_s += (animation_interval_ms / 1000.0) * sim_speed_multiplier
    sim_idx = simulation_index_from_time(sim_time_s, wrap_orbit=True)
    return set_scene_at_index(sim_idx)

def save_one_pass_video_30x_to_project_root():
    export_speed_multiplier = SIMULATION.export_speed_multiplier
    export_fps = RENDER.export_fps
    sim_total_s = simulation.metadata.sim_total_s
    # Match interactive playback: each output frame advances simulated time by the same
    # step as one FuncAnimation tick at `export_speed_multiplier` (see `update()`).
    dt_sim_s = (animation_interval_ms / 1000.0) * export_speed_multiplier
    export_num_frames = max(2, int(np.ceil(sim_total_s / dt_sim_s)) + 1)
    export_path = Path(__file__).resolve().parents[2] / RENDER.export_filename

    pbar = None
    if tqdm is not None:
        pbar = tqdm(total=export_num_frames, desc="Exporting 30x MP4", unit="frame")

    def export_update(frame):
        sim_t = min(float(frame) * dt_sim_s, sim_total_s)
        sim_idx = simulation_index_from_time(sim_t, wrap_orbit=False)
        if pbar is not None:
            pbar.update(1)
        return set_scene_at_index(sim_idx, speed_label=export_speed_multiplier)

    try:
        if mpl_animation.writers.is_available("ffmpeg"):
            export_ani = FuncAnimation(
                fig,
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
            # Fallback path when ffmpeg binary is not available.
            from matplotlib.backends.backend_agg import FigureCanvasAgg
            import cv2  # type: ignore[reportMissingImports]

            canvas = FigureCanvasAgg(fig)
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
    finally:
        if pbar is not None:
            pbar.close()
    return export_path

def _maximize_interactive_window():
    if not RENDER.interactive_start_maximized:
        return
    mgr = getattr(fig.canvas, "manager", None)
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
        # TkAgg: toplevel may expose wm_state on the canvas widget
        top = getattr(win, "winfo_toplevel", lambda: win)()
        if hasattr(top, "wm_state"):
            top.wm_state("zoomed")
    except Exception:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Satellite render and video export")
    parser.add_argument(
        "--save-one-pass-30x",
        action="store_true",
        help="Save one-pass MP4 at 30x speed to project root",
    )
    args = parser.parse_args()

    fig.text(
        0.5,
        0.995,
        f"2D Satellite Orbit around Earth (h={sat_altitude:.0f} km, T={orbit_period_s/60:.1f} min)",
        color="white",
        ha="center",
        va="top",
        fontsize=RENDER.suptitle_fontsize,
    )
    
    PANELS = {}

    CONTROLS = build_controls_panel(fig)

    if SHOW_TELEMETRY:
        axes, artists = build_telemetry_panel(fig, SCENE)
        PANELS["telemetry"] = {"axes": axes, "artists": artists}

    if SHOW_MAIN_PLOT:
        axes, artists = build_main_panel(fig, SCENE)
        PANELS["main"] = {"axes": axes, "artists": artists}

    if SHOW_CLOSEUP:
        axes, artists = build_closeup_panel(fig, SCENE)
        PANELS["closeup"] = {"axes": axes, "artists": artists}

    if SHOW_1D_BIRD_VIEW:
        axes, artists = build_1d_bird_view(fig, SCENE)
        PANELS["1d_bird"] = {"axes": axes, "artists": artists}


    if args.save_one_pass_30x:
        output_path = save_one_pass_video_30x_to_project_root()
        print(f"Saved one-pass video to: {output_path}")
    else:
        # Live animation
        ani = FuncAnimation(
            fig,
            update,
            init_func=init,
            blit=False,
            interval=animation_interval_ms,
            cache_frame_data=False,
        )  # ~33 fps
        _maximize_interactive_window()
        plt.show()