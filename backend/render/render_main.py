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
from utils.geodesics.geodesic_helpers import (
    east_north_km_to_lon_lat,
    geodesic_distance,
    sigma_deg_to_meters_north,
)
from simulation.observation_line_constants import OBSERVATION_LINE_NOT_COMPUTED
from simulation.run_simulation import run_simulation

#BUG use these for debugging only
SHOW_MAIN_PLOT = True
SHOW_1D_BIRD_VIEW = True
SHOW_1D_SAT_VIEW = True
SHOW_FIXED_BIRD_VIEW = True
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
pause_button = None  # Button instance set in build_controls_panel
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
_ground_patch_geo = SIMULATION.switzerland_map
# Observer reference in the 1D bird-view frame matches observer-relative km (origin).
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
    bird_view_1d_center_lat_deg=float(_ground_patch_geo.lat_center_deg),
    bird_view_1d_center_lon_deg=float(_ground_patch_geo.lon_center_deg),
    bird_view_1d_half_extent_km=float(RENDER.bird_view_1d_half_extent_km.to(ureg.km).magnitude),
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
        glow, = ax.plot([], [], color=to_rgba(RENDER.cloud_grey_rgb, 0.35),
                        linewidth=RENDER.cloud_linewidth * 2.4,
                        alpha=min(1.0, RENDER.cloud_alpha * 0.23),
                        solid_capstyle="round",
                        zorder=RENDER.zorder_cloud - 1)
        core, = ax.plot([], [], color=RENDER.cloud_grey_rgb,
                        linewidth=RENDER.cloud_linewidth,
                        alpha=RENDER.cloud_alpha,
                        solid_capstyle="round",
                        zorder=RENDER.zorder_cloud)
        artists["cloud_glow"].append(glow)
        artists["cloud_core"].append(core)

    return axes, artists


def _rgba_for_observation_line_code(code: int) -> np.ndarray:
    """Map simulation observation codes to RGBA for the 1d_sat_view strip."""
    c = int(code)
    if c == int(OBSERVATION_LINE_NOT_COMPUTED):
        return np.array([0.28, 0.28, 0.32, 1.0], dtype=float)
    if c == 0:  # space
        return np.array([0.04, 0.06, 0.12, 1.0], dtype=float)
    if c == 1:  # earth
        return np.array([*RENDER.earth_green_rgb, 1.0], dtype=float)
    if c == 2:  # cloud
        return np.array([0.78, 0.78, 0.80, 1.0], dtype=float)
    if c == 3:  # target
        return np.array([0.95, 0.15, 0.12, 1.0], dtype=float)
    return np.array([0.5, 0.0, 0.5, 1.0], dtype=float)


def build_1d_sat_view(fig: plt.Figure, _scene: dict) -> tuple[dict, dict]:
    l, b, w, h = RENDER.sat_view_1d_axes_rect
    title_frac = 0.26
    h_title = h * title_frac
    h_strip = h * (1.0 - title_frac)

    ax_title = fig.add_axes([l, b + h_strip, w, h_title])
    ax_strip = fig.add_axes([l, b, w, h_strip])

    axes = {"1d_sat_view": ax_strip, "1d_sat_view_title": ax_title}
    artists: dict = {}

    n_bins = int(simulation.camera_observation_line_codes.shape[1])
    h_pix = 24
    artists["H"] = h_pix
    artists["N_BINS"] = n_bins

    img = np.zeros((h_pix, n_bins, 4), dtype=float)
    artists["img"] = ax_strip.imshow(
        img,
        extent=(0, n_bins, 0, 1),
        origin="lower",
        interpolation="none",
        aspect="auto",
        zorder=1,
    )

    ax_strip.set_facecolor(RENDER.space_background)
    ax_strip.set_xlim(0, n_bins)
    ax_strip.set_ylim(0, 1)
    ax_strip.set_xticks([])
    ax_strip.set_yticks([])
    ax_strip.set_frame_on(False)

    ax_title.set_facecolor("black")
    ax_title.set_xticks([])
    ax_title.set_yticks([])
    ax_title.set_frame_on(False)
    artists["title_text"] = ax_title.text(
        0.5,
        0.5,
        "1d_sat_view",
        transform=ax_title.transAxes,
        color="white",
        fontsize=9,
        fontweight="bold",
        ha="center",
        va="center",
    )

    return axes, artists


def build_fixed_bird_view(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    """Observer-centered top-down panel: ±bird_view_1d_half_extent_km (500 km default)."""
    l, b, w, h = RENDER.fixed_bird_view_axes_rect
    title_frac = 0.22
    h_title = h * title_frac
    h_plot = h * (1.0 - title_frac)
    ax_title = fig.add_axes([l, b + h_plot, w, h_title])
    ax = fig.add_axes([l, b, w, h_plot])

    axes = {"fixed_bird": ax, "fixed_bird_title": ax_title}
    artists: dict = {}

    n_clouds = int(simulation.cloud_arc_radius_km.shape[1])
    h_km = float(scene["bird_view_1d_half_extent_km"])
    obs = scene["observer_pos"]
    ox, oy = float(obs[0]), float(obs[1])
    earth_center_local = (float(-ox), float(-oy))
    r_earth = float(scene["R_earth"])

    ax_title.set_facecolor("black")
    ax_title.set_xticks([])
    ax_title.set_yticks([])
    ax_title.set_frame_on(False)
    artists["title_text"] = ax_title.text(
        0.5,
        0.5,
        "fixed bird (500 km)",
        transform=ax_title.transAxes,
        color="white",
        fontsize=9,
        fontweight="bold",
        ha="center",
        va="center",
    )

    ax.set_facecolor(RENDER.earth_green_rgb)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-h_km, h_km)
    ax.set_ylim(-h_km, h_km)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor(RENDER.info_text_color)
        spine.set_linewidth(1.0)

    artists["earth_circle"] = Circle(
        earth_center_local,
        r_earth,
        facecolor=RENDER.earth_green_rgb,
        edgecolor=to_rgba(RENDER.earth_green_rgb, 0.95),
        linewidth=0.8,
        zorder=RENDER.zorder_earth,
    )
    ax.add_patch(artists["earth_circle"])

    artists["footprint"] = Polygon(
        np.zeros((4, 2)),
        closed=True,
        facecolor=to_rgba(RENDER.fov_turquoise_rgba[:3], RENDER.fov_turquoise_rgba[3]),
        edgecolor=to_rgba(RENDER.fov_turquoise_rgba[:3], 0.85),
        linewidth=RENDER.inset_footprint_edge_linewidth,
        zorder=RENDER.zorder_inset_footprint,
    )
    ax.add_patch(artists["footprint"])
    artists["footprint"].set_visible(False)

    artists["cloud_glow"] = []
    artists["cloud_core"] = []
    for _ in range(n_clouds):
        g, = ax.plot(
            [],
            [],
            color=to_rgba(RENDER.cloud_grey_rgb, 0.38),
            linewidth=RENDER.cloud_linewidth * 2.0,
            solid_capstyle="round",
            zorder=RENDER.zorder_inset_cloud_glow,
        )
        c, = ax.plot(
            [],
            [],
            color=RENDER.cloud_grey_rgb,
            linewidth=RENDER.cloud_linewidth,
            solid_capstyle="round",
            zorder=RENDER.zorder_inset_cloud_core,
        )
        artists["cloud_glow"].append(g)
        artists["cloud_core"].append(c)

    artists["observer"], = ax.plot(
        [0.0],
        [0.0],
        marker="x",
        color=RENDER.observer_color,
        markersize=6.0 * RENDER.observer_marker_render_scale,
        markeredgewidth=1.2,
        zorder=RENDER.zorder_inset_observer,
    )

    return axes, artists


def build_1d_bird_view(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.bird_view_1d_axes_rect)

    axes = {"1d_bird": ax}
    artists: dict = {}

    cloud_models = scene["cloud_models"]
    center_lat_deg = scene["bird_view_1d_center_lat_deg"]
    center_lon_deg = scene["bird_view_1d_center_lon_deg"]
    observer_cross_local = scene.get("observer_cross_local", np.array([0.0, 0.0], dtype=float))

    half_extent_km = float(RENDER.bird_view_1d_half_extent_km.to(ureg.km).magnitude)
    full_extent_km = int(round(2.0 * half_extent_km))
    inset_range_km = float(half_extent_km)

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
        f"1D bird view {full_extent_km}×{full_extent_km} km\n{center_lat_deg:.2f}N {center_lon_deg:.2f}E",
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
        g, = ax.plot([], [], color=to_rgba(RENDER.cloud_grey_rgb, 0.38),
                     linewidth=RENDER.cloud_linewidth * 2.0,
                     alpha=min(1.0, RENDER.cloud_alpha * 0.25),
                     solid_capstyle="round",
                     zorder=RENDER.zorder_inset_cloud_glow)
        c, = ax.plot([], [], color=RENDER.cloud_grey_rgb,
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
            color=to_rgba(RENDER.cloud_grey_rgb, 0.38),
            linewidth=RENDER.cloud_linewidth * 1.8,
            alpha=0.0,
            zorder=RENDER.zorder_closeup_cloud_glow,
        )
        c, = ax.plot(
            [], [],
            color=RENDER.cloud_grey_rgb,
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
    observer_target_angle_rad=float(np.arctan2(R_earth, 0.0)),
    camera_pixel_ray_samples=SIMULATION.camera_pixel_ray_samples,
)
orbit_period_s = simulation.metadata.orbit_period_s

def build_controls_panel(fig: plt.Figure) -> dict:
    global pause_button
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
    pause_button = artists["pause"]

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



def project_to_frame(
    local_xy_km: np.ndarray[np.floating],
    half_extent_km: float,
) -> np.ndarray[np.floating]:
    h = float(half_extent_km)
    return np.array([np.clip(local_xy_km[0], -h, h), np.clip(local_xy_km[1], -h, h)], dtype=float)



def _bird_view_1d_footprint_vertices_xy(left_local_km, right_local_km, half_swath_km):
    """Rectangle in observer-local km: chord = left→right, half-width along perpendicular (swath/2).

    Note: returns *unclipped* observer-local vertices (do not project/clip to the 1D bird-view extent here).
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


def _sample_bird_view_1d_terrain_elevation_m(lat_deg, lon_deg):
    # Deterministic terrain sampler over the ground patch (replace with DEM lookup later).
    peaks = [
        (46.55, 8.00, 2100.0, 0.28),
        (46.30, 9.10, 1600.0, 0.22),
        (46.85, 7.60, 1300.0, 0.25),
    ]
    hit_lat = lat_deg * ureg.deg
    hit_lon = lon_deg * ureg.deg
    elev_m = 450.0
    for peak_lat, peak_lon, amplitude_m, sigma_deg in peaks:
        plon = peak_lon * ureg.deg
        plat = peak_lat * ureg.deg
        sigma_m = sigma_deg_to_meters_north(plon, plat, sigma_deg * ureg.deg)
        d = geodesic_distance(hit_lon, hit_lat, plon, plat)
        d_m = float(d.to(ureg.m).magnitude)
        sigma_m_val = float(sigma_m.to(ureg.m).magnitude)
        elev_m += amplitude_m * np.exp(-(d_m**2) / (2.0 * sigma_m_val**2))
    return float(elev_m)


def _cloud_arc_specs_from_simulation(sim_idx: int) -> list[dict[str, object]]:
    """Build per-cloud plot specs from `SimulationStateSeries` (filled in `run_simulation`)."""
    sim_time_local = float(simulation.t_s[sim_idx])
    growth_phase = sim_time_local / max(simulation.metadata.sim_total_s, 1e-9)
    cloud_thickness = 1.0 + (RENDER.cloud_growth_linewidth_scale - 1.0) * np.clip(growth_phase, 0.0, 1.0)
    r = simulation.cloud_arc_radius_km[sim_idx, :]
    s0 = simulation.cloud_arc_start_rad[sim_idx, :]
    s1 = simulation.cloud_arc_end_rad[sim_idx, :]
    n_clouds = int(r.shape[0])
    specs: list[dict[str, object]] = []
    for i in range(n_clouds):
        radius = float(r[i])
        start = float(s0[i])
        end = float(s1[i])
        if not (np.isfinite(radius) and np.isfinite(start) and np.isfinite(end)):
            specs.append(
                {
                    "radius": float("nan"),
                    "theta": np.array([], dtype=float),
                    "x": np.array([], dtype=float),
                    "y": np.array([], dtype=float),
                    "start": 0.0,
                    "end": 0.0,
                    "growth": cloud_thickness,
                }
            )
            continue
        theta = np.linspace(start, end, RENDER.cloud_segment_points)
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        specs.append(
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
    return specs



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

    # --- 1D BIRD VIEW PANEL ---
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

    # --- 1D SAT VIEW (camera observation line) ---
    if "1d_sat_view" in PANELS:
        a = PANELS["1d_sat_view"]["artists"]
        img = np.zeros((a["H"], a["N_BINS"], 4), dtype=float)
        a["img"].set_data(img)

    # --- CLOSEUP ---
    if "closeup" in PANELS:
        a = PANELS["closeup"]["artists"]
        a["cone"].set_xy([[0, 0], [0, 0], [0, 0]])
        a["hit"].set_data([], [])
        a["obs_to_hit"].set_data([], [])
        for g, c in zip(a["cloud_glow"], a["cloud_core"]):
            g.set_data([], [])
            c.set_data([], [])

    # --- FIXED BIRD (observer-local top-down) ---
    if "fixed_bird" in PANELS:
        a = PANELS["fixed_bird"]["artists"]
        a["footprint"].set_visible(False)
        for g, c in zip(a["cloud_glow"], a["cloud_core"]):
            g.set_data([], [])
            c.set_data([], [])

    # --- TELEMETRY ---
    if "telemetry" in PANELS:
        PANELS["telemetry"]["artists"]["text"].set_text("")

    return []

def set_scene_at_index(sim_idx: int, speed_label=None):
    sat_r = simulation.radius_km[sim_idx]
    sat_theta = simulation.theta_orbit_rad[sim_idx]
    sat_pos = np.array([sat_r * np.cos(sat_theta), sat_r * np.sin(sat_theta)], dtype=float)

    cloud_arc_specs = _cloud_arc_specs_from_simulation(sim_idx)

    # body z dir (simulated)
    z_angle_rad = float(simulation.body_z_angle_rad[sim_idx])
    z_axis_dir = np.array([np.cos(z_angle_rad), np.sin(z_angle_rad)], dtype=float)



    # Camera outputs from precomputed simulation series (see simulation.run_simulation).
    ground_center_xy_km = simulation.camera_ground_center_xy_km[sim_idx]
    center_first_hit_xy_km = simulation.camera_center_first_hit_xy_km[sim_idx]
    center_first_hit_is_cloud = bool(simulation.camera_center_first_hit_is_cloud[sim_idx])
    camera_gsd_m = float(simulation.camera_gsd_m[sim_idx])
    strip_cloud_blocked_fraction = float(simulation.camera_cloud_blocked_fraction[sim_idx])

    observer_pos = SCENE["observer_pos"]
    observer_x = SCENE["observer_x"]
    observer_y = SCENE["observer_y"]
    half_km = SCENE["bird_view_1d_half_extent_km"]

    if not np.isnan(ground_center_xy_km).any():
        center_local = ground_center_xy_km - observer_pos
        center_local_frame = project_to_frame(center_local, half_km)
        hit_lat_q, hit_lon_q = east_north_km_to_lon_lat(
            SCENE["bird_view_1d_center_lon_deg"] * ureg.deg,
            SCENE["bird_view_1d_center_lat_deg"] * ureg.deg,
            center_local_frame[0] * ureg.km,
            center_local_frame[1] * ureg.km,
        )
        hit_lat_deg = float(hit_lat_q.to(ureg.deg).magnitude)
        hit_lon_deg = float(hit_lon_q.to(ureg.deg).magnitude)
        hit_elevation_m = _sample_bird_view_1d_terrain_elevation_m(hit_lat_deg, hit_lon_deg)
        if not np.isnan(center_first_hit_xy_km).any():
            nearest_intersection_km = float(np.linalg.norm(center_first_hit_xy_km - sat_pos))
        else:
            nearest_intersection_km = None
    else:
        hit_lat_deg, hit_lon_deg, hit_elevation_m = None, None, None
        nearest_intersection_km = None
        center_first_hit_is_cloud = False

    nadir_angle_rad = sat_theta + np.pi
    z_angle_rel_nadir_rad = np.arctan2(
        np.sin(np.arctan2(z_axis_dir[1], z_axis_dir[0]) - nadir_angle_rad),
        np.cos(np.arctan2(z_axis_dir[1], z_axis_dir[0]) - nadir_angle_rad),
    )
    z_angle_deg = float(np.rad2deg(z_angle_rel_nadir_rad))
    sat_to_observer = np.array([observer_x, observer_y], dtype=float) - sat_pos
    los_angle_rad = float(np.arctan2(sat_to_observer[1], sat_to_observer[0]))
    los_rel_nadir_rad = np.arctan2(
        np.sin(los_angle_rad - nadir_angle_rad),
        np.cos(los_angle_rad - nadir_angle_rad),
    )
    los_rel_nadir_deg = float(np.rad2deg(los_rel_nadir_rad))

    if nearest_intersection_km is None:
        intersection_text = "none"
    else:
        hit_type_label = "cloud" if center_first_hit_is_cloud else "earth"
        intersection_text = f"{nearest_intersection_km:.1f} km ({hit_type_label})"
    if hit_lat_deg is None:
        geo_hit_text = "none"
    else:
        geo_hit_text = f"{hit_lat_deg:.3f}N {hit_lon_deg:.3f}E @ {hit_elevation_m:.0f}m"

    camera_vertical_fov_deg = float(np.rad2deg(simulation.camera_vertical_fov_rad))
    camera_swath_height_km = (
        (N_PIXELS_Y * camera_gsd_m) / 1000.0 if not np.isnan(camera_gsd_m) else float("nan")
    )
    strip_cloud_blocked_pct = (
        100.0 * strip_cloud_blocked_fraction
        if np.isfinite(strip_cloud_blocked_fraction)
        else float("nan")
    )
    speed_for_text = sim_speed_multiplier if speed_label is None else speed_label
    gsd_txt = f"{camera_gsd_m:.2f} m" if np.isfinite(camera_gsd_m) else "n/a"
    swath_txt = (
        f"{camera_swath_height_km:.1f} km"
        if np.isfinite(camera_swath_height_km)
        else "n/a"
    )
    blocked_txt = (
        f"{strip_cloud_blocked_pct:.0f}%"
        if np.isfinite(strip_cloud_blocked_fraction)
        else "n/a"
    )

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

    # ---- fixed bird (observer-local top-down) ----
    if "fixed_bird" in PANELS:
        a = PANELS["fixed_bird"]["artists"]
        obs = SCENE["observer_pos"]
        ground_left = simulation.camera_ground_left_xy_km[sim_idx]
        ground_right = simulation.camera_ground_right_xy_km[sim_idx]
        gsd_m = float(simulation.camera_gsd_m[sim_idx])
        swath_half_km = (N_PIXELS_Y * gsd_m) / 2000.0
        if np.isnan(ground_left).any() or np.isnan(ground_right).any() or not np.isfinite(swath_half_km):
            a["footprint"].set_visible(False)
        else:
            ll = ground_left - obs
            rr = ground_right - obs
            verts = _bird_view_1d_footprint_vertices_xy(ll, rr, swath_half_km)
            if verts is None:
                a["footprint"].set_visible(False)
            else:
                a["footprint"].set_xy(verts)
                a["footprint"].set_visible(True)
        for i, spec in enumerate(cloud_arc_specs):
            xloc = np.asarray(spec["x"], dtype=float) - obs[0]
            yloc = np.asarray(spec["y"], dtype=float) - obs[1]
            a["cloud_glow"][i].set_data(xloc, yloc)
            a["cloud_core"][i].set_data(xloc, yloc)

    # ---- 1D bird view panel artists ----
    if "1d_bird" in PANELS:
        a = PANELS["1d_bird"]["artists"]
        # keep your existing 1D update logic, just replace globals by a[...] and SCENE[...]
        # minimum “looks alive” reset/update:
        img = np.zeros((a["H"], a["BINS"], 4), dtype=float)
        img[:, :, :] = np.array(a["RGBA_GROUND"], dtype=float)
        img[:, a["obs_bin"], :] = np.array(a["RGBA_OBSERVER"], dtype=float)
        a["img"].set_data(img)

    # ---- 1d_sat_view (precomputed camera observation line) ----
    if "1d_sat_view" in PANELS:
        a = PANELS["1d_sat_view"]["artists"]
        codes = np.asarray(simulation.camera_observation_line_codes[sim_idx], dtype=np.int8)
        h_strip = int(a["H"])
        n_bins = int(a["N_BINS"])
        row = np.empty((n_bins, 4), dtype=float)
        for j in range(n_bins):
            row[j, :] = _rgba_for_observation_line_code(int(codes[j]))
        img = np.tile(row[np.newaxis, :, :], (h_strip, 1, 1))
        a["img"].set_data(img)

    # ---- TELEMETRY ----
    if "telemetry" in PANELS:
        t = PANELS["telemetry"]["artists"]["text"]
        telemetry_body = "\n\n".join(
            [
                "\n".join(
                    [
                        "Orbit / attitude",
                        f"  Orbit height: {sat_altitude:.1f} km",
                        f"  Body spin: {sat_body_rotation_rate_label}",
                        f"  z angle rel nadir: {z_angle_deg:+.1f}°",
                        f"  LOS rel nadir: {los_rel_nadir_deg:+.1f}°",
                        f"  Render window: {start_angle_deg:+.1f}° to {end_angle_deg:+.1f}°",
                    ]
                ),
                "\n".join(
                    [
                        "Camera / strip",
                        f"  GSD: {gsd_txt}, V-FOV: {camera_vertical_fov_deg:.2f}°",
                        f"  Swath height: {swath_txt}",
                        f"  Strip cloud blocked: {blocked_txt}",
                    ]
                ),
                "\n".join(
                    [
                        "Hits",
                        f"  Centerline hit: {intersection_text}",
                        f"  Ground patch hit: {geo_hit_text}",
                    ]
                ),
                "\n".join(
                    [
                        "Playback",
                        f"  Speed: {speed_for_text:.0f}x",
                    ]
                ),
            ]
        )
        t.set_text(telemetry_body)

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

    if SHOW_1D_SAT_VIEW:
        axes, artists = build_1d_sat_view(fig, SCENE)
        PANELS["1d_sat_view"] = {"axes": axes, "artists": artists}

    if SHOW_FIXED_BIRD_VIEW:
        axes, artists = build_fixed_bird_view(fig, SCENE)
        PANELS["fixed_bird"] = {"axes": axes, "artists": artists}

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