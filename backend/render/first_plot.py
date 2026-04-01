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

#region agent log helper
_DEBUG_LOG_PATH = Path(__file__).resolve().parents[2] / "debug-5dbcb6.log"
_DEBUG_SESSION_ID = "5dbcb6"
_DEBUG_RUN_ID = "overlay-diagonal-debug"

def _agent_debug_log(hypothesisId, location, message, data):
    payload = {
        "sessionId": _DEBUG_SESSION_ID,
        "runId": _DEBUG_RUN_ID,
        "hypothesisId": hypothesisId,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        # Logging must never break rendering.
        pass
#endregion

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
ax = fig.add_axes(RENDER.main_axes_rect)
plot_margin = RENDER.plot_margin.to(ureg.km).magnitude
plot_limit = R_orbit + plot_margin
# Show only the selected angular snippet and make it fill the window.
# Use the full angular arc for framing (not only endpoints), otherwise
# symmetric windows around nadir can collapse y-bounds.
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
    np.sqrt(max(R_earth ** 2 - x_min_earth ** 2, 0.0)),
    np.sqrt(max(R_earth ** 2 - x_max_earth ** 2, 0.0)),
)
zoom_pad_x = RENDER.zoom_pad_x.to(ureg.km).magnitude
zoom_pad_y_bottom = RENDER.zoom_pad_y_bottom.to(ureg.km).magnitude
zoom_pad_y_top = RENDER.zoom_pad_y_top.to(ureg.km).magnitude
ax.set_xlim(x_min_orbit - zoom_pad_x, x_max_orbit + zoom_pad_x)
ax.set_ylim(earth_cap_y_min - zoom_pad_y_bottom, float(np.max(y_render)) + zoom_pad_y_top)
ax.set_aspect('equal', adjustable='box')
ax.set_facecolor(RENDER.space_background)  # Space background
ax.axis('off')             # Hide axes for clean look

# 3D coordinate-frame legend (visual only). Main axes plot world (x, y) in the
# equatorial plane (z = 0): screen horizontal = world +x, vertical = world +y;
# world +z is normal to the plane (dot = toward viewer, x marker = away).
# Anchor lower-left of main axes so it stays clear of the right-hand column.
legend_x0, legend_y0 = 0.05, 0.08
legend_len_x = 0.11
legend_len_y = 0.095
# z-depth glyphs sit left of the in-plane origin to avoid crowding the x/y arrows.
legend_z_dot_x = legend_x0 - 0.042
ax.annotate(
    "",
    xy=(legend_x0 + legend_len_x, legend_y0),
    xycoords=ax.transAxes,
    xytext=(legend_x0, legend_y0),
    textcoords=ax.transAxes,
    arrowprops=dict(arrowstyle="->", color=RENDER.info_text_color, lw=1.5),
    zorder=RENDER.zorder_info,
)
ax.annotate(
    "",
    xy=(legend_x0, legend_y0 + legend_len_y),
    xycoords=ax.transAxes,
    xytext=(legend_x0, legend_y0),
    textcoords=ax.transAxes,
    arrowprops=dict(arrowstyle="->", color=RENDER.info_text_color, lw=1.5),
    zorder=RENDER.zorder_info,
)
# z axis (normal to the plot plane): dot = toward viewer, x marker = away
ax.plot(
    [legend_z_dot_x],
    [legend_y0 + 0.012],
    marker="o",
    linestyle="None",
    markersize=6,
    markerfacecolor="none",
    markeredgecolor=RENDER.info_text_color,
    transform=ax.transAxes,
    zorder=RENDER.zorder_info,
)
ax.plot(
    [legend_z_dot_x],
    [legend_y0 - 0.034],
    marker="x",
    linestyle="None",
    markersize=6,
    color=RENDER.info_text_color,
    transform=ax.transAxes,
    zorder=RENDER.zorder_info,
)
ax.text(
    legend_z_dot_x - 0.028,
    legend_y0 - 0.01,
    "z",
    transform=ax.transAxes,
    color=RENDER.info_text_color,
    fontsize=8,
    ha="right",
    va="center",
    zorder=RENDER.zorder_info,
)
ax.text(
    legend_x0 + legend_len_x + 0.005,
    legend_y0,
    "x",
    transform=ax.transAxes,
    color=RENDER.info_text_color,
    fontsize=8,
    ha="left",
    va="bottom",
    zorder=RENDER.zorder_info,
)
ax.text(
    legend_x0,
    legend_y0 + legend_len_y + 0.005,
    "y",
    transform=ax.transAxes,
    color=RENDER.info_text_color,
    fontsize=8,
    ha="left",
    va="bottom",
    zorder=RENDER.zorder_info,
)
ax.text(
    legend_x0 + legend_len_x * 0.45,
    legend_y0 - 0.038,
    "XY plane (z=0)",
    transform=ax.transAxes,
    color=RENDER.info_text_color,
    fontsize=7,
    ha="left",
    va="top",
    zorder=RENDER.zorder_info,
)

# Static star field for visual depth
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

# Earth (shaded blue ball)
earth_res = RENDER.earth_res
earth_x = np.linspace(-R_earth, R_earth, earth_res)
earth_y = np.linspace(-R_earth, R_earth, earth_res)
earth_X, earth_Y = np.meshgrid(earth_x, earth_y)
earth_r2 = (earth_X / R_earth) ** 2 + (earth_Y / R_earth) ** 2
earth_mask = earth_r2 <= 1.0

# Simple sphere shading with a top-left light source.
earth_Z = np.sqrt(np.clip(1.0 - earth_r2, 0.0, 1.0))
light_dir = np.array(RENDER.light_dir)
light_dir = light_dir / np.linalg.norm(light_dir)
earth_intensity = np.clip(
    earth_X / R_earth * light_dir[0]
    + earth_Y / R_earth * light_dir[1]
    + earth_Z * light_dir[2],
    0.0,
    1.0,
)

earth_dark = np.array(RENDER.earth_dark_rgb)
earth_bright = np.array(RENDER.earth_bright_rgb)
earth_rgb = earth_dark + earth_intensity[..., None] * (earth_bright - earth_dark)
earth_alpha = earth_mask.astype(float)
earth_rgba = np.dstack((earth_rgb, earth_alpha))

ax.imshow(
    earth_rgba,
    extent=(-R_earth, R_earth, -R_earth, R_earth),
    origin='lower',
    interpolation='bilinear',
    zorder=RENDER.zorder_earth,
)
earth_outline = Circle(
    (0, 0),
    R_earth,
    fill=False,
    edgecolor=RENDER.earth_outline_color,
    linewidth=RENDER.earth_outline_linewidth,
    alpha=RENDER.earth_outline_alpha,
    zorder=RENDER.zorder_earth_outline,
)
ax.add_patch(earth_outline)


# Observer point at Earth's north pole
observer_x, observer_y = 0.0, R_earth
observer_pos = np.array([observer_x, observer_y], dtype=float)
swiss_map = SIMULATION.switzerland_map
swiss_center_lat_deg = float(swiss_map.lat_center_deg)
swiss_center_lon_deg = float(swiss_map.lon_center_deg)
# Observer reference in Swiss inset frame matches observer-relative km (origin).
observer_cross_local = np.array([0.0, 0.0])
ax.plot(
    [observer_x],
    [observer_y],
    marker='x',
    color=RENDER.observer_color,
    markersize=RENDER.observer_marker_size * RENDER.observer_marker_render_scale,
    markeredgewidth=RENDER.observer_marker_edge_width,
    zorder=RENDER.zorder_observer,
)

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

cloud_main_glow_artists = []
cloud_main_core_artists = []
for _ in cloud_models:
    glow, = ax.plot(
        [],
        [],
        color="#cfefff",
        linewidth=RENDER.cloud_linewidth * 2.4,
        alpha=min(1.0, RENDER.cloud_alpha * 0.23),
        solid_capstyle='round',
        zorder=RENDER.zorder_cloud - 1,
    )
    core, = ax.plot(
        [],
        [],
        color=RENDER.cloud_color,
        linewidth=RENDER.cloud_linewidth,
        alpha=RENDER.cloud_alpha,
        solid_capstyle='round',
        zorder=RENDER.zorder_cloud,
    )
    cloud_main_glow_artists.append(glow)
    cloud_main_core_artists.append(core)

_swiss_inset_half_km = float(RENDER.swiss_inset_half_extent_km.to(ureg.km).magnitude)
_swiss_inset_full_km = int(round(2.0 * _swiss_inset_half_km))
_INSET_1D_RANGE_KM = float(_swiss_inset_half_km)

# Observer-local weather/capture inset (square km window from RENDER.swiss_inset_half_extent_km)
inset_ax = fig.add_axes(RENDER.swiss_inset_axes_rect)
inset_ax.set_facecolor(RENDER.space_background)
inset_ax.set_aspect('auto', adjustable='box')
inset_ax.set_xlim(-_INSET_1D_RANGE_KM, _INSET_1D_RANGE_KM)
inset_ax.set_ylim(-_INSET_1D_RANGE_KM, _INSET_1D_RANGE_KM)
inset_ax.set_xticks([])
inset_ax.set_yticks([])
for spine in inset_ax.spines.values():
    spine.set_edgecolor(RENDER.info_text_color)
    spine.set_linewidth(1.0)

_INSET_1D_BINS = 240
_INSET_1D_BAND_HALF_KM = 7.5
_INSET_1D_EARTH_RGBA = to_rgba(RENDER.closeup_ground_line_color, 1.0)
_INSET_1D_CONE_RGBA = to_rgba("#1E90FF", 1.0)
_INSET_1D_CLOUD_RGBA = to_rgba("white", 1.0)
_INSET_1D_OBSERVER_RGBA = to_rgba(RENDER.observer_color, 1.0)

inset_1d_img = inset_ax.imshow(
    np.zeros((1, _INSET_1D_BINS, 4), dtype=float),
    extent=(
        -_INSET_1D_RANGE_KM,
        _INSET_1D_RANGE_KM,
        -_INSET_1D_BAND_HALF_KM,
        _INSET_1D_BAND_HALF_KM,
    ),
    origin="lower",
    interpolation="nearest",
    aspect="auto",
    zorder=1,
)

# 1D view overlay for the main XY axes.
# We render an opaque 1×N RGBA strip over the entire panel so the main XY
# "diagonal ray" overlays from the 2D geometry cannot show through.
main_1d_img = ax.imshow(
    np.zeros((1, _INSET_1D_BINS, 4), dtype=float),
    extent=(
        ax.get_xlim()[0],
        ax.get_xlim()[1],
        ax.get_ylim()[0],
        ax.get_ylim()[1],
    ),
    origin="lower",
    interpolation="nearest",
    aspect="auto",
    zorder=200,
)

_inset_1d_obs_bin = int(round((_INSET_1D_BINS - 1) * 0.5))  # x_local=0
_inset_1d_x_bins = np.linspace(-_INSET_1D_RANGE_KM, _INSET_1D_RANGE_KM, _INSET_1D_BINS)
cloud_inset_x_samples = [None for _ in cloud_models]
cloud_inset_y_samples = [None for _ in cloud_models]
_inset_swiss_label_z = max(RENDER.zorder_inset_cloud_core, RENDER.zorder_info) + 1
inset_ax.text(
    0.02,
    0.98,
    f"Swiss {_swiss_inset_full_km}×{_swiss_inset_full_km} km\n{swiss_center_lat_deg:.2f}N {swiss_center_lon_deg:.2f}E",
    transform=inset_ax.transAxes,
    color=RENDER.info_text_color,
    fontsize=8,
    va="top",
    ha="left",
    linespacing=1.12,
    zorder=_inset_swiss_label_z,
)
inset_ax.text(
    0.02,
    0.02,
    "1D view (in-plane y)",
    transform=inset_ax.transAxes,
    color=RENDER.info_text_color,
    fontsize=7,
    va="bottom",
    ha="left",
    zorder=_inset_swiss_label_z,
)
inset_observer_marker, = inset_ax.plot(
    [observer_cross_local[0]],
    [observer_cross_local[1]],
    marker='x',
    color=RENDER.observer_color,
    markersize=6 * RENDER.observer_marker_render_scale,
    markeredgewidth=1.2,
    zorder=RENDER.zorder_inset_observer,
)
inset_observer_marker.set_visible(False)  # observer is rendered into the 1D image
inset_footprint_poly = Polygon(
    np.zeros((4, 2)),
    closed=True,
    facecolor=to_rgba(RENDER.cone_color, RENDER.inset_footprint_fill_alpha),
    edgecolor=RENDER.cone_color,
    linewidth=RENDER.inset_footprint_edge_linewidth,
    alpha=1.0,
    zorder=RENDER.zorder_inset_footprint,
)
inset_ax.add_patch(inset_footprint_poly)
inset_footprint_poly.set_visible(False)  # replaced by the 1D image
inset_hit_marker, = inset_ax.plot(
    [],
    [],
    marker='o',
    color='yellow',
    markersize=4,
    linestyle='None',
    zorder=RENDER.zorder_inset_hit,
)
inset_hit_marker.set_visible(False)
inset_centerline, = inset_ax.plot(
    [],
    [],
    color=RENDER.z_arrow_color,
    linewidth=1.2,
    alpha=0.0,  # Keep endpoints computed but do not render the diagonal overlay line.
    zorder=RENDER.zorder_inset_centerline,
)
inset_centerline.set_visible(False)
cloud_inset_glow_artists = []
cloud_inset_core_artists = []
for _ in cloud_models:
    inset_glow, = inset_ax.plot(
        [],
        [],
        color="#cfefff",
        linewidth=RENDER.cloud_linewidth * 2.0,
        alpha=min(1.0, RENDER.cloud_alpha * 0.25),
        solid_capstyle='round',
        zorder=RENDER.zorder_inset_cloud_glow,
    )
    inset_core, = inset_ax.plot(
        [],
        [],
        color=RENDER.cloud_color,
        linewidth=RENDER.cloud_linewidth,
        alpha=RENDER.cloud_alpha,
        solid_capstyle='round',
        zorder=RENDER.zorder_inset_cloud_core,
    )
    cloud_inset_glow_artists.append(inset_glow)
    cloud_inset_core_artists.append(inset_core)
    inset_glow.set_visible(False)
    inset_core.set_visible(False)

# Observer/cloud close-up in the same 2D orbital plane.
closeup_ax = fig.add_axes(RENDER.closeup_axes_rect)
closeup_ax.set_facecolor(RENDER.space_background)
closeup_ax.set_aspect('equal', adjustable='box')
# Close-up axes represent the YZ plane with the observer placed at the origin.
# In this projection:
#   - closeup x-axis  := y_local = x_world - observer_x
#   - closeup y-axis  := z_local = y_world - observer_y
# so that the observer at (observer_x, observer_y) maps to (0, 0).
closeup_half_window = (30.0 * ureg.km).to(ureg.km).magnitude  # ±30 km sideways in YZ panel
closeup_ax.set_xlim(-closeup_half_window, closeup_half_window)
closeup_ax.set_ylim(-5.0, 25.0)  # z in [-5,+25] km
closeup_ax.set_xticks([])
closeup_ax.set_yticks([])
for spine in closeup_ax.spines.values():
    spine.set_edgecolor(RENDER.info_text_color)
    spine.set_linewidth(1.0)

closeup_ax.axhline(
    0.0,
    color=RENDER.closeup_ground_line_color,
    linewidth=RENDER.closeup_ground_line_linewidth,
    zorder=RENDER.zorder_closeup_ground,
)

# Helper: project big-frame XY points (x_world, y_world) into close-up YZ coordinates (y_local, z_local).
def _project_big_xy_to_closeup_yz(x_world_km, y_world_km):
    y_local = x_world_km - observer_x
    z_local = y_world_km - observer_y
    return y_local, z_local

closeup_ax.text(
    0.02,
    0.98,
    "Observer + Cloud Plane Close-up",
    transform=closeup_ax.transAxes,
    color=RENDER.info_text_color,
    fontsize=8,
    va="top",
    ha="left",
)
closeup_ax.text(
    0.02,
    0.02,
    "YZ plane (x=0)",
    transform=closeup_ax.transAxes,
    color=RENDER.info_text_color,
    fontsize=7,
    va="bottom",
    ha="left",
)
closeup_ax.plot(
    [0.0],
    [0.0],
    marker='x',
    color=RENDER.observer_color,
    markersize=RENDER.observer_marker_size * RENDER.observer_marker_render_scale,
    markeredgewidth=RENDER.observer_marker_edge_width,
    zorder=RENDER.zorder_closeup_observer,
)
# Filled cone in the YZ close-up reads as a solid grey/cyan band; keep geometry
# updated for potential future use but do not draw fill/edge in this panel.
closeup_cone = Polygon(
    [[0, 0], [0, 0], [0, 0]],
    closed=True,
    # Make the camera view cone visible in the close-up panel.
    facecolor=RENDER.cone_color,
    edgecolor=RENDER.cone_color,
    linewidth=1.0,
    alpha=RENDER.cone_alpha,
    zorder=RENDER.zorder_closeup_cone,
)
closeup_ax.add_patch(closeup_cone)
closeup_hit_marker, = closeup_ax.plot(
    [],
    [],
    marker='o',
    color='yellow',
    markersize=4,
    linestyle='None',
    zorder=RENDER.zorder_closeup_hit,
)

# Observer-to-hit line of sight (close-up YZ).
closeup_obs_to_hit_line, = closeup_ax.plot(
    [],
    [],
    linestyle='--',
    color=RENDER.los_color,
    linewidth=RENDER.los_linewidth,
    alpha=RENDER.los_alpha,
    zorder=RENDER.zorder_closeup_hit,
)
closeup_cloud_glow_artists = []
closeup_cloud_core_artists = []
for _ in cloud_models:
    closeup_glow, = closeup_ax.plot(
        [],
        [],
        color="#cfefff",
        linewidth=RENDER.cloud_linewidth * 1.8,
        alpha=0.0,
        zorder=RENDER.zorder_closeup_cloud_glow,
    )
    closeup_core, = closeup_ax.plot(
        [],
        [],
        color=RENDER.cloud_color,
        linewidth=RENDER.cloud_linewidth,
        alpha=RENDER.cloud_alpha,
        zorder=RENDER.zorder_closeup_cloud_core,
    )
    closeup_cloud_glow_artists.append(closeup_glow)
    closeup_cloud_core_artists.append(closeup_core)

# Satellite (red dot)
sat, = ax.plot([], [], RENDER.sat_marker_style, markersize=RENDER.sat_marker_size, label='Satellite')

# Observer-to-satellite line of sight
obs_to_sat_line, = ax.plot([], [], linestyle='--', color=RENDER.los_color, linewidth=RENDER.los_linewidth, alpha=RENDER.los_alpha, zorder=RENDER.zorder_los)


# Optional: faint orbit trail line
trail, = ax.plot([], [], RENDER.trail_style, linewidth=RENDER.trail_linewidth, alpha=RENDER.trail_alpha)


# Cone beam parameters (2D instrument footprint)
# Use the camera sensor vertical FOV in the renderer's in-plane 2D convention.
_vertical_fov_rad = pinhole_full_fov_rad(
    sensor_dim=SENSOR_HEIGHT, focal_length=FOCAL_LENGTH
)
cone_half_angle_rad = float(_vertical_fov_rad.to(ureg.rad).magnitude / 2.0)
cone_length = SIMULATION.cone_length.to(ureg.km).magnitude * RENDER.cone_length_render_scale
cone = Polygon([[0, 0], [0, 0], [0, 0]], closed=True, color=RENDER.cone_color, alpha=RENDER.cone_alpha)
ax.add_patch(cone)


# Satellite body-frame Z axis in nadir mode (towards Earth center)
z_axis_length = SIMULATION.z_axis_length.to(ureg.km).magnitude
z_axis_arrow = FancyArrowPatch(
    (0, 0),
    (0, 0),
    arrowstyle='-|>',
    mutation_scale=RENDER.z_arrow_mutation_scale,
    linewidth=RENDER.z_arrow_linewidth,
    color=RENDER.z_arrow_color,
    alpha=RENDER.z_arrow_alpha,
    zorder=RENDER.zorder_z_axis,
)
ax.add_patch(z_axis_arrow)
z_axis_label = ax.text(
    0,
    0,
    RENDER.z_label_text,
    color=RENDER.z_label_color,
    fontsize=RENDER.z_label_fontsize,
    weight=RENDER.z_label_weight,
    zorder=RENDER.zorder_z_label,
)
telemetry_ax = fig.add_axes(RENDER.telemetry_axes_rect)
telemetry_ax.set_facecolor(RENDER.space_background)
telemetry_ax.set_xlim(0.0, 1.0)
telemetry_ax.set_ylim(0.0, 1.0)
telemetry_ax.set_xticks([])
telemetry_ax.set_yticks([])
for _sp in telemetry_ax.spines.values():
    _sp.set_edgecolor(RENDER.info_text_color)
    _sp.set_linewidth(0.8)
info_telemetry_text = telemetry_ax.text(
    0.04,
    0.98,
    "",
    transform=telemetry_ax.transAxes,
    color=RENDER.info_text_color,
    fontsize=RENDER.info_panel_fontsize,
    family=RENDER.info_panel_fontfamily,
    va="top",
    ha="left",
    linespacing=1.14,
)

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

button_specs = list(RENDER.speed_button_specs)
speed_buttons = []
pause_button = None

_transport = RENDER.transport_bar_rect
_btn_h = RENDER.speed_button_height
_btn_w = RENDER.speed_button_width
_pause_w = 0.072
_btn_gap = 0.008
# Pause + Real-time + 3 speed buttons with gaps
_n_speed = len(button_specs)
_total_w = _pause_w + _n_speed * _btn_w + _n_speed * _btn_gap
_start_x = _transport[0] + max(0.0, (_transport[2] - _total_w) * 0.5)
_btn_y = _transport[1] + max(0.0, (_transport[3] - _btn_h) * 0.5)
_cx = _start_x
pause_ax = fig.add_axes([_cx, _btn_y, _pause_w, _btn_h])
pause_ax.set_facecolor(RENDER.space_background)
pause_button = Button(
    pause_ax,
    "Pause",
    color=RENDER.speed_button_color,
    hovercolor=RENDER.speed_button_hover_color,
)
pause_button.label.set_color(RENDER.speed_button_label_color)
pause_button.label.set_fontsize(RENDER.speed_button_label_fontsize)
pause_button.on_clicked(toggle_pause)
_cx += _pause_w + _btn_gap

for label, multiplier, _unused_left in button_specs:
    button_ax = fig.add_axes([_cx, _btn_y, _btn_w, _btn_h])
    button_ax.set_facecolor(RENDER.space_background)
    button = Button(
        button_ax,
        label,
        color=RENDER.speed_button_color,
        hovercolor=RENDER.speed_button_hover_color,
    )
    button.label.set_color(RENDER.speed_button_label_color)
    button.label.set_fontsize(RENDER.speed_button_label_fontsize)
    button.on_clicked(lambda _event, m=multiplier: set_sim_speed(m))
    speed_buttons.append(button)
    _cx += _btn_w + _btn_gap


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


def _observer_local_km_to_geo(local_xy_km):
    east_km, north_km = float(local_xy_km[0]), float(local_xy_km[1])
    lat_deg = swiss_center_lat_deg + north_km / 110.574
    lon_scale_km = max(111.320 * np.cos(np.deg2rad(lat_deg)), 1e-6)
    lon_deg = swiss_center_lon_deg + east_km / lon_scale_km
    return lat_deg, lon_deg


def _project_to_swiss_frame(local_xy_km):
    h = _swiss_inset_half_km
    return np.array(
        [
            float(np.clip(local_xy_km[0], -h, h)),
            float(np.clip(local_xy_km[1], -h, h)),
        ]
    )


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


def _compute_cloud_arcs_at_time(sim_time_local):
    growth_phase = sim_time_local / max(simulation.metadata.sim_total_s, 1e-9)
    cloud_growth = 1.0 + (RENDER.cloud_growth_max_span_scale - 1.0) * np.clip(growth_phase, 0.0, 1.0)
    cloud_thickness = 1.0 + (RENDER.cloud_growth_linewidth_scale - 1.0) * np.clip(growth_phase, 0.0, 1.0)
    cloud_arc_specs = []
    for idx, model in enumerate(cloud_models):
        omega = model["omega_rad_s"]
        mod = 1.0 + model["noise_amp"] * np.sin(
            model["noise_freq_rad_s"] * sim_time_local + model["noise_phase"]
        )
        # Keep clouds angular placement fixed for the 2D geometry view,
        # so observer/cloud relationships remain consistent.
        shift = 0.0
        base_start = model["start_rad_0"] + shift
        base_end = model["end_rad_0"] + shift
        # Center the arc on the observer radial so the ground observer and cloud
        # share the same polar angle (same vertical line in the XY plot).
        observer_angle_rad = float(np.arctan2(observer_pos[1], observer_pos[0]))
        angular_width = float(base_end - base_start) * cloud_growth
        start = observer_angle_rad - 0.5 * angular_width
        end = observer_angle_rad + 0.5 * angular_width
        theta = np.linspace(start, end, RENDER.cloud_segment_points)
        radius = model["radius_km"]
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)

        cloud_main_glow_artists[idx].set_linewidth(RENDER.cloud_linewidth * 2.4 * cloud_thickness)
        cloud_main_core_artists[idx].set_linewidth(RENDER.cloud_linewidth * cloud_thickness)
        cloud_main_glow_artists[idx].set_data(x, y)
        cloud_main_core_artists[idx].set_data(x, y)
        x_local = x - observer_pos[0]
        y_local = y - observer_pos[1]
        cloud_inset_glow_artists[idx].set_linewidth(RENDER.cloud_linewidth * 2.0 * cloud_thickness)
        cloud_inset_core_artists[idx].set_linewidth(RENDER.cloud_linewidth * cloud_thickness)
        cloud_inset_glow_artists[idx].set_data(x_local, y_local)
        cloud_inset_core_artists[idx].set_data(x_local, y_local)
        cloud_inset_x_samples[idx] = x_local
        cloud_inset_y_samples[idx] = y_local
        cloud_arc_specs.append(
            {
                "radius": radius,
                "start": start,
                "end": end,
                "theta": theta,
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
    sat.set_data([], [])
    obs_to_sat_line.set_data([], [])
    trail.set_data([], [])
    cone.set_xy([[0, 0], [0, 0], [0, 0]])
    z_axis_arrow.set_positions((0, 0), (0, 0))
    z_axis_label.set_position((0, 0))
    inset_footprint_poly.set_xy(np.zeros((4, 2)))
    inset_footprint_poly.set_visible(False)
    inset_hit_marker.set_data([], [])
    inset_centerline.set_data([], [])
    base_img = np.zeros((1, _INSET_1D_BINS, 4), dtype=float)
    base_img[:, :, :] = np.array(_INSET_1D_EARTH_RGBA, dtype=float)
    base_img[0, _inset_1d_obs_bin, :] = np.array(_INSET_1D_OBSERVER_RGBA, dtype=float)
    inset_1d_img.set_data(base_img)
    main_1d_img.set_data(base_img)
    _agent_debug_log(
        "H1",
        "first_plot:init",
        "Artist visibility/zorders at init",
        {
            "main_1d_img_visible": bool(main_1d_img.get_visible()),
            "main_1d_img_zorder": float(main_1d_img.get_zorder()),
            "main_1d_img_alpha": None if main_1d_img.get_alpha() is None else float(main_1d_img.get_alpha()),
            "obs_to_sat_line_visible": bool(obs_to_sat_line.get_visible()),
            "obs_to_sat_line_zorder": float(obs_to_sat_line.get_zorder()),
            "obs_to_sat_line_alpha": None if obs_to_sat_line.get_alpha() is None else float(obs_to_sat_line.get_alpha()),
            "z_axis_arrow_visible": bool(z_axis_arrow.get_visible()),
            "z_axis_arrow_zorder": float(z_axis_arrow.get_zorder()),
            "z_axis_arrow_alpha": None if z_axis_arrow.get_alpha() is None else float(z_axis_arrow.get_alpha()),
            "inset_centerline_visible": bool(inset_centerline.get_visible()),
            "inset_footprint_poly_visible": bool(inset_footprint_poly.get_visible()),
            "inset_hit_marker_visible": bool(inset_hit_marker.get_visible()),
        },
    )
    closeup_cone.set_xy([[0, 0], [0, 0], [0, 0]])
    closeup_hit_marker.set_data([], [])
    # Hide close-up LOS trace to prevent the diagonal "ray" artifact.
    closeup_obs_to_hit_line.set_visible(False)
    closeup_obs_to_hit_line.set_data([], [])
    for glow, core in zip(cloud_main_glow_artists, cloud_main_core_artists):
        glow.set_data([], [])
        core.set_data([], [])
    for glow, core in zip(cloud_inset_glow_artists, cloud_inset_core_artists):
        glow.set_data([], [])
        core.set_data([], [])
    for glow, core in zip(closeup_cloud_glow_artists, closeup_cloud_core_artists):
        glow.set_data([], [])
        core.set_data([], [])
    info_telemetry_text.set_text("")
    return set_scene_at_index(0, speed_label=sim_speed_multiplier)


def set_scene_at_index(sim_idx, speed_label=None):
    sat_r = simulation.radius_km[sim_idx]
    sat_theta = simulation.theta_orbit_rad[sim_idx]
    sat_pos = np.array([sat_r * np.cos(sat_theta), sat_r * np.sin(sat_theta)])
    sim_time_local = float(simulation.t_s[sim_idx])
    cloud_arc_specs = _compute_cloud_arcs_at_time(sim_time_local)
    sat.set_data([sat_pos[0]], [sat_pos[1]])
    obs_to_sat_line.set_data([observer_x, sat_pos[0]], [observer_y, sat_pos[1]])
    trail_end = max(sim_idx + 1, 2)
    trail_theta = simulation.theta_orbit_rad[:trail_end]
    trail_radius = simulation.radius_km[:trail_end]
    trail.set_data(trail_radius * np.cos(trail_theta), trail_radius * np.sin(trail_theta))

    z_angle_rad = float(simulation.body_z_angle_rad[sim_idx])
    # Render the *simulated* body Z axis direction; do not derive it from LOS to the observer.
    z_axis_dir = np.array([np.cos(z_angle_rad), np.sin(z_angle_rad)], dtype=float)

    try:
        _cam = simulate_camera_strip_2d(
            sat_pos_xy_km=sat_pos,
            boresight_dir_unit_xy=z_axis_dir,
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=R_earth,
            sim_time_s=sim_time_local,
            sim_total_s=float(simulation.metadata.sim_total_s),
            pixel_ray_samples=_RENDER_PIXEL_RAY_SAMPLES,
        )
    except Exception:
        _cam = None

    if _cam is None:
        ground_left_xy_km = np.full(2, np.nan)
        ground_right_xy_km = np.full(2, np.nan)
        ground_center_xy_km = np.full(2, np.nan)
        center_first_hit_xy_km = np.full(2, np.nan)
        center_first_hit_is_cloud = False
        camera_gsd_m = float("nan")
        strip_cloud_blocked_fraction = float("nan")
    else:
        ground_left_xy_km = _cam.ground_left_xy_km
        ground_right_xy_km = _cam.ground_right_xy_km
        ground_center_xy_km = _cam.ground_center_xy_km
        center_first_hit_is_cloud = _cam.center_first_hit_is_cloud
        camera_gsd_m = float(_cam.gsd_m)
        strip_cloud_blocked_fraction = float(_cam.cloud_blocked_fraction)
        if _cam.center_first_hit_xy_km is not None:
            center_first_hit_xy_km = _cam.center_first_hit_xy_km
        else:
            center_first_hit_xy_km = np.full(2, np.nan)

    # Update cone footprint along +z direction
    cos_h, sin_h = np.cos(cone_half_angle_rad), np.sin(cone_half_angle_rad)
    rot_left = np.array([[cos_h, -sin_h], [sin_h, cos_h]])
    rot_right = np.array([[cos_h, sin_h], [-sin_h, cos_h]])
    edge_left = sat_pos + cone_length * (rot_left @ z_axis_dir)
    edge_right = sat_pos + cone_length * (rot_right @ z_axis_dir)
    cone.set_xy([sat_pos, edge_left, edge_right])
    sat_y_local, sat_z_local = _project_big_xy_to_closeup_yz(sat_pos[0], sat_pos[1])
    left_y_local, left_z_local = _project_big_xy_to_closeup_yz(edge_left[0], edge_left[1])
    right_y_local, right_z_local = _project_big_xy_to_closeup_yz(edge_right[0], edge_right[1])
    closeup_cone.set_xy([[sat_y_local, sat_z_local], [left_y_local, left_z_local], [right_y_local, right_z_local]])

    # Close-up LOS trace should match the 2D orbit plot observer->satellite orange line,
    # because this YZ panel is a zoom-in projection of that same geometry.
    if np.isfinite(sat_y_local) and np.isfinite(sat_z_local):
        closeup_obs_to_hit_line.set_data([0.0, float(sat_y_local)], [0.0, float(sat_z_local)])
    else:
        closeup_obs_to_hit_line.set_data([], [])
    # 1D inset image update:
    # - brown: earth background
    # - blue: view cone projection (footprint x-span)
    # - red: observer at x=0
    # - white: clouds inside the footprint rectangle
    inset_img = np.zeros((1, _INSET_1D_BINS, 4), dtype=float)
    inset_img[:, :, :] = np.array(_INSET_1D_EARTH_RGBA, dtype=float)
    inset_img[0, _inset_1d_obs_bin, :] = np.array(_INSET_1D_OBSERVER_RGBA, dtype=float)

    half_swath_km = 0.5 * (N_PIXELS_Y * camera_gsd_m) / 1000.0 if not np.isnan(camera_gsd_m) else float("nan")
    if not (np.isnan(ground_left_xy_km).any() or np.isnan(ground_right_xy_km).any() or np.isnan(half_swath_km)):
        left_local = ground_left_xy_km - observer_pos
        right_local = ground_right_xy_km - observer_pos
        verts = _inset_swiss_footprint_vertices_xy(left_local, right_local, half_swath_km)
        if verts is not None:
            # Compute y-span using the same clipped swiss-frame convention
            # as the original inset.
            verts_clipped = np.array([_project_to_swiss_frame(v) for v in verts], dtype=float)
            y_min = float(np.min(verts_clipped[:, 1]))
            y_max = float(np.max(verts_clipped[:, 1]))
            # 1D inset columns encode the *y* coordinate (in-plane), projected into [-h, +h].
            view_mask = (_inset_1d_x_bins >= y_min) & (_inset_1d_x_bins <= y_max)
            if sim_idx in (0, 160):
                _agent_debug_log(
                    "H2",
                    "first_plot:set_scene_at_index:view_mask_span",
                    "1D cone span computed (view_mask nonempty?)",
                    {
                        "sim_idx": int(sim_idx),
                        "y_min": y_min,
                        "y_max": y_max,
                        "view_mask_bins": int(np.count_nonzero(view_mask)),
                    },
                )
            inset_img[0, view_mask, :] = np.array(_INSET_1D_CONE_RGBA, dtype=float)

            # Clouds: mark x bins for points that are inside the full 2D footprint rectangle.
            chord = np.asarray(right_local, dtype=float) - np.asarray(left_local, dtype=float)
            L = float(np.linalg.norm(chord))
            if L >= 1e-9:
                e = chord / L
                e_perp = np.array([-e[1], e[0]], dtype=float)
                h = float(half_swath_km)
                cloud_points_marked = 0
                for ci in range(len(cloud_models)):
                    xs = cloud_inset_x_samples[ci]
                    ys = cloud_inset_y_samples[ci]
                    if xs is None or ys is None:
                        continue
                    xs_arr = np.asarray(xs, dtype=float)
                    ys_arr = np.asarray(ys, dtype=float)
                    # Map cloud points onto the same 1D bins as the blue view cone,
                    # but do not require full 2D rectangle containment (too strict for
                    # the thin 1D strip). This makes cloud markers visible and
                    # visually consistent with the cone span.
                    ys_clip = np.clip(ys_arr, -_INSET_1D_RANGE_KM, _INSET_1D_RANGE_KM)
                    bin_idx = (
                        (ys_clip + _INSET_1D_RANGE_KM)
                        / (2.0 * _INSET_1D_RANGE_KM)
                        * (_INSET_1D_BINS - 1)
                    ).astype(int)
                    bin_idx = np.clip(bin_idx, 0, _INSET_1D_BINS - 1)

                    # Show clouds wherever they land in the 1D mapping.
                    bin_idx = np.unique(bin_idx)
                    if bin_idx.size == 0:
                        continue

                    cloud_rgba = np.array(_INSET_1D_CLOUD_RGBA, dtype=float)
                    for bi in bin_idx:
                        j0 = max(0, int(bi) - 1)
                        j1 = min(_INSET_1D_BINS, int(bi) + 2)
                        inset_img[0, j0:j1, :] = cloud_rgba
                    cloud_points_marked += int(bin_idx.size)

                # 1D inset image update continues here.

    inset_1d_img.set_data(inset_img)
    main_1d_img.set_data(inset_img)
    if sim_idx in (0, 160):
        _agent_debug_log(
            "H3",
            "first_plot:set_scene_at_index:main_1d_array_sample",
            "main_1d_img receives inset_img (alpha+sample RGBA)",
            {
                "sim_idx": int(sim_idx),
                "main_1d_img_zorder": float(main_1d_img.get_zorder()),
                "main_1d_img_alpha": None if main_1d_img.get_alpha() is None else float(main_1d_img.get_alpha()),
                "main_arr_shape": None if main_1d_img.get_array() is None else list(main_1d_img.get_array().shape),
                "main_arr_center_bin_rgba": (
                    None
                    if main_1d_img.get_array() is None
                    else [float(x) for x in main_1d_img.get_array()[0, _inset_1d_obs_bin, :].tolist()]
                ),
            },
        )

    if not np.isnan(ground_center_xy_km).any():
        center_local = ground_center_xy_km - observer_pos
        center_local_frame = _project_to_swiss_frame(center_local)
        inset_hit_marker.set_data([center_local_frame[0]], [center_local_frame[1]])

        sat_local = sat_pos - observer_pos
        sat_local_frame = _project_to_swiss_frame(sat_local)
        inset_centerline.set_data(
            [sat_local_frame[0], center_local_frame[0]],
            [sat_local_frame[1], center_local_frame[1]],
        )
        hit_y_local, hit_z_local = _project_big_xy_to_closeup_yz(ground_center_xy_km[0], ground_center_xy_km[1])
        closeup_hit_marker.set_data([hit_y_local], [hit_z_local])

        hit_lat_deg, hit_lon_deg = _observer_local_km_to_geo(center_local_frame)
        hit_elevation_m = _sample_swiss_elevation_m(hit_lat_deg, hit_lon_deg)

        if not np.isnan(center_first_hit_xy_km).any():
            nearest_intersection_km = float(np.linalg.norm(center_first_hit_xy_km - sat_pos))
        else:
            nearest_intersection_km = None
    else:
        inset_hit_marker.set_data([], [])
        inset_centerline.set_data([], [])
        closeup_hit_marker.set_data([], [])
        # Do not clear close-up LOS: this panel is a zoom-in of the 2D observer->satellite geometry,
        # which should remain visible even when the camera ground target is missing/blocked.
        hit_lat_deg, hit_lon_deg, hit_elevation_m = None, None, None
        nearest_intersection_km = None
        center_first_hit_is_cloud = False

    for idx, cloud_spec in enumerate(cloud_arc_specs):
        theta = cloud_spec["theta"]
        radius = cloud_spec["radius"]
        x_mid = radius * np.cos(theta)
        y_mid = radius * np.sin(theta)
        closeup_cloud_glow_artists[idx].set_linewidth(RENDER.cloud_linewidth * 1.8 * cloud_spec["growth"])
        closeup_cloud_core_artists[idx].set_linewidth(RENDER.cloud_linewidth * cloud_spec["growth"])
        y_mid_local, z_mid_local = _project_big_xy_to_closeup_yz(x_mid, y_mid)
        closeup_cloud_glow_artists[idx].set_data(y_mid_local, z_mid_local)
        closeup_cloud_core_artists[idx].set_data(y_mid_local, z_mid_local)

    # Satellite Z orientation (relative to nadir).
    z_axis_tip = sat_pos + z_axis_length * z_axis_dir
    z_axis_arrow.set_positions((sat_pos[0], sat_pos[1]), (z_axis_tip[0], z_axis_tip[1]))
    label_pos = z_axis_tip + RENDER.z_label_offset.to(ureg.km).magnitude * z_axis_dir
    z_axis_label.set_position((label_pos[0], label_pos[1]))
    nadir_angle_rad = sat_theta + np.pi
    z_angle_rel_nadir_rad = np.arctan2(
        np.sin(np.arctan2(z_axis_dir[1], z_axis_dir[0]) - nadir_angle_rad),
        np.cos(np.arctan2(z_axis_dir[1], z_axis_dir[0]) - nadir_angle_rad),
    )
    z_angle_deg = np.rad2deg(z_angle_rel_nadir_rad)
    sat_to_observer = np.array([observer_x, observer_y]) - sat_pos
    los_angle_rad = np.arctan2(sat_to_observer[1], sat_to_observer[0])
    los_rel_nadir_rad = np.arctan2(
        np.sin(los_angle_rad - nadir_angle_rad),
        np.cos(los_angle_rad - nadir_angle_rad),
    )
    los_rel_nadir_deg = np.rad2deg(los_rel_nadir_rad)
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
    camera_swath_height_km = (N_PIXELS_Y * camera_gsd_m) / 1000.0 if not np.isnan(camera_gsd_m) else float("nan")
    strip_cloud_blocked_pct = 100.0 * strip_cloud_blocked_fraction if not np.isnan(strip_cloud_blocked_fraction) else float("nan")
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
                    f"  Swiss hit: {geo_hit_text}",
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
    info_telemetry_text.set_text(telemetry_body)

    return (
        sat,
        obs_to_sat_line,
        trail,
        cone,
        z_axis_arrow,
        z_axis_label,
        info_telemetry_text,
        inset_footprint_poly,
        inset_hit_marker,
        inset_centerline,
    )

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