import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import animation as mpl_animation
from matplotlib.patches import Circle, Polygon, FancyArrowPatch
from matplotlib.widgets import Button
import argparse
import json
import time
from pathlib import Path

#local imports
from environment_definition.constants import (
    EARTH_GRAVITATIONAL_PARAMETER,
    EARTH_RADIUS,
    RENDER,
    SIMULATION,
    UREG as ureg,
)
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE_ALTITUDE
from utils.flight_geometry.line_of_sight import minimum_contact_angle
from simulation.trajectory_simulator import KinematicSimulationConfig, simulate_kinematic_trajectory


def _debug_log(run_id, hypothesis_id, location, message, data):
    payload = {
        "sessionId": "89b7c9",
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    log_path = Path(__file__).resolve().parents[2] / "debug-89b7c9.log"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


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
# Human-readable spin label is shown in the bottom info bar.
sat_body_rotation_rate_label = "0.000 deg/s"
# Spin rate in radians per second drives continuous z-axis rotation.
sat_body_rotation_rate_rad_s = 0.0
# UI refresh interval sets rendering cadence in milliseconds.
animation_interval_ms = SIMULATION.animation_interval.to(ureg.ms).magnitude
# Speed multiplier scales simulated time versus wall-clock animation time.
sim_speed_multiplier = SIMULATION.default_speed_multiplier
# Running simulation clock accumulates elapsed simulated seconds.
sim_time_s = 0.0
simulation = None
# region agent log
_debug_log(
    run_id="pre-fix",
    hypothesis_id="H2",
    location="backend/render/first_plot.py:simulation_constants_probe",
    message="Simulation constants attributes",
    data={
        "has_cone_opening": bool(hasattr(SIMULATION, "cone_opening")),
        "has_field_of_view_cone": bool(hasattr(SIMULATION, "field_of_view_cone")),
        "simulation_type": type(SIMULATION).__name__,
    },
)
# endregion

# --- Set up the figure ---
fig, ax = plt.subplots(figsize=RENDER.figure_size, constrained_layout=False)
fig.patch.set_facecolor(RENDER.space_background)
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
observer_marker_rng = np.random.default_rng()
observer_cross_local = np.array(
    [
        float(observer_marker_rng.uniform(-500.0, 500.0)),
        float(observer_marker_rng.uniform(-500.0, 500.0)),
    ]
)
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

# Observer-local weather/capture inset (1000 km x 1000 km frame)
inset_ax = fig.add_axes([0.67, 0.61, 0.30, 0.34])
inset_ax.set_facecolor(RENDER.space_background)
inset_ax.set_aspect('equal', adjustable='box')
inset_ax.set_xlim(-500.0, 500.0)
inset_ax.set_ylim(-500.0, 500.0)
inset_ax.set_xticks([])
inset_ax.set_yticks([])
for spine in inset_ax.spines.values():
    spine.set_edgecolor(RENDER.info_text_color)
    spine.set_linewidth(1.0)
inset_ax.set_title(
    f"Swiss Patch 1000x1000 km ({swiss_center_lat_deg:.2f}N, {swiss_center_lon_deg:.2f}E)",
    color=RENDER.info_text_color,
    fontsize=8,
)
inset_ax.plot(
    [observer_cross_local[0]],
    [observer_cross_local[1]],
    marker='x',
    color=RENDER.observer_color,
    markersize=6 * RENDER.observer_marker_render_scale,
    markeredgewidth=1.2,
)
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
    )
    inset_core, = inset_ax.plot(
        [],
        [],
        color=RENDER.cloud_color,
        linewidth=RENDER.cloud_linewidth,
        alpha=RENDER.cloud_alpha,
        solid_capstyle='round',
    )
    cloud_inset_glow_artists.append(inset_glow)
    cloud_inset_core_artists.append(inset_core)
inset_footprint, = inset_ax.plot([], [], color=RENDER.cone_color, linewidth=1.8, alpha=0.9)
inset_hit_marker, = inset_ax.plot([], [], marker='o', color='yellow', markersize=4, linestyle='None')
inset_centerline, = inset_ax.plot([], [], color=RENDER.z_arrow_color, linewidth=1.2, alpha=0.8)

# Observer/cloud close-up in the same 2D orbital plane.
closeup_ax = fig.add_axes(RENDER.closeup_axes_rect)
closeup_ax.set_facecolor(RENDER.space_background)
closeup_ax.set_aspect('equal', adjustable='box')
closeup_half_window = RENDER.closeup_half_window_km.to(ureg.km).magnitude
closeup_ax.set_xlim(observer_x - closeup_half_window, observer_x + closeup_half_window)
closeup_ax.set_ylim(observer_y - closeup_half_window, observer_y + closeup_half_window)
closeup_ax.set_xticks([])
closeup_ax.set_yticks([])
for spine in closeup_ax.spines.values():
    spine.set_edgecolor(RENDER.info_text_color)
    spine.set_linewidth(1.0)
closeup_ax.set_title(
    "Observer + Cloud Plane Close-up",
    color=RENDER.info_text_color,
    fontsize=8,
)
closeup_ax.plot(
    [observer_x],
    [observer_y],
    marker='x',
    color=RENDER.observer_color,
    markersize=RENDER.observer_marker_size * RENDER.observer_marker_render_scale,
    markeredgewidth=RENDER.observer_marker_edge_width,
)
closeup_cone = Polygon([[0, 0], [0, 0], [0, 0]], closed=True, color=RENDER.cone_color, alpha=0.30)
closeup_ax.add_patch(closeup_cone)
closeup_centerline, = closeup_ax.plot([], [], color=RENDER.z_arrow_color, linewidth=1.2, alpha=0.9)
closeup_hit_marker, = closeup_ax.plot([], [], marker='o', color='yellow', markersize=4, linestyle='None')
closeup_cloud_glow_artists = []
closeup_cloud_core_artists = []
closeup_cloud_upper_artists = []
closeup_cloud_lower_artists = []
for _ in cloud_models:
    closeup_glow, = closeup_ax.plot([], [], color="#cfefff", linewidth=RENDER.cloud_linewidth * 1.8, alpha=0.35)
    closeup_core, = closeup_ax.plot([], [], color=RENDER.cloud_color, linewidth=RENDER.cloud_linewidth, alpha=RENDER.cloud_alpha)
    closeup_upper, = closeup_ax.plot([], [], color=RENDER.cloud_color, linewidth=1.2, alpha=0.7)
    closeup_lower, = closeup_ax.plot([], [], color=RENDER.cloud_color, linewidth=1.2, alpha=0.7)
    closeup_cloud_glow_artists.append(closeup_glow)
    closeup_cloud_core_artists.append(closeup_core)
    closeup_cloud_upper_artists.append(closeup_upper)
    closeup_cloud_lower_artists.append(closeup_lower)

# Satellite (red dot)
sat, = ax.plot([], [], RENDER.sat_marker_style, markersize=RENDER.sat_marker_size, label='Satellite')

# Observer-to-satellite line of sight
obs_to_sat_line, = ax.plot([], [], linestyle='--', color=RENDER.los_color, linewidth=RENDER.los_linewidth, alpha=RENDER.los_alpha, zorder=RENDER.zorder_los)


# Optional: faint orbit trail line
trail, = ax.plot([], [], RENDER.trail_style, linewidth=RENDER.trail_linewidth, alpha=RENDER.trail_alpha)


# Cone beam parameters (nadir-pointing instrument footprint)
# region agent log
_debug_log(
    run_id="pre-fix",
    hypothesis_id="H1",
    location="backend/render/first_plot.py:cone_opening_access",
    message="About to access cone opening setting",
    data={
        "access_path": "SIMULATION.field_of_view_cone.opening_angle",
        "has_cone_opening": bool(hasattr(SIMULATION, "cone_opening")),
        "has_field_of_view_cone": bool(hasattr(SIMULATION, "field_of_view_cone")),
    },
)
# endregion
cone_opening_deg = SIMULATION.field_of_view_cone.opening_angle.to(ureg.deg).magnitude
cone_half_angle_rad = np.deg2rad(cone_opening_deg / 2) * RENDER.cone_half_angle_render_scale
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
info_text = ax.text(
    0.5,
    0.02,
    "",
    transform=ax.transAxes,
    color=RENDER.info_text_color,
    fontsize=RENDER.info_fontsize,
    va='bottom',
    ha='center',
    bbox=dict(
        boxstyle=RENDER.info_bbox_boxstyle,
        facecolor=RENDER.info_bbox_facecolor,
        edgecolor=RENDER.info_bbox_edgecolor,
        alpha=RENDER.info_bbox_alpha,
        linewidth=RENDER.info_bbox_linewidth,
    ),
    zorder=RENDER.zorder_info,
)

def set_sim_speed(multiplier):
    global sim_speed_multiplier
    sim_speed_multiplier = float(multiplier)

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


def build_simulation_series():
    config = KinematicSimulationConfig(
        earth_radius_km=R_earth,
        sat_altitude_km=sat_altitude,
        mu_earth_km3_s2=mu_earth,
        theta_center_rad=theta_center,
        start_angle_deg=start_angle_deg,
        end_angle_deg=end_angle_deg,
        sat_motion_span_scale=sat_motion_span_scale,
        num_frames=num_frames,
        sat_z_offset_deg=sat_z_offset_deg,
        body_spin_rate_rad_s=sat_body_rotation_rate_rad_s,
    )
    return simulate_kinematic_trajectory(config)


# Start from configured body spin rate.
set_sat_body_rotation_rate(
    SIMULATION.default_body_spin_rate.to(ureg.deg / ureg.s).magnitude,
    unit="deg",
)
simulation = build_simulation_series()
orbit_period_s = simulation.metadata.orbit_period_s

button_specs = list(RENDER.speed_button_specs)
speed_buttons = []
for label, multiplier, left in button_specs:
    button_ax = fig.add_axes([left, RENDER.speed_button_top, RENDER.speed_button_width, RENDER.speed_button_height])
    button_ax.set_facecolor(RENDER.space_background)
    button = Button(
        button_ax,
        label,
        color=RENDER.speed_button_color,
        hovercolor=RENDER.speed_button_hover_color,
    )
    button.label.set_color(RENDER.speed_button_label_color)
    button.on_clicked(lambda _event, m=multiplier: set_sim_speed(m))
    speed_buttons.append(button)


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
    return np.array(
        [
            float(np.clip(local_xy_km[0], -500.0, 500.0)),
            float(np.clip(local_xy_km[1], -500.0, 500.0)),
        ]
    )


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
        shift = omega * mod * sim_time_local
        base_start = model["start_rad_0"] + shift
        base_end = model["end_rad_0"] + shift
        center = 0.5 * (base_start + base_end)
        half_span = 0.5 * (base_end - base_start) * cloud_growth
        start = center - half_span
        end = center + half_span
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
    inset_footprint.set_data([], [])
    inset_hit_marker.set_data([], [])
    inset_centerline.set_data([], [])
    closeup_cone.set_xy([[0, 0], [0, 0], [0, 0]])
    closeup_centerline.set_data([], [])
    closeup_hit_marker.set_data([], [])
    for glow, core in zip(cloud_main_glow_artists, cloud_main_core_artists):
        glow.set_data([], [])
        core.set_data([], [])
    for glow, core in zip(cloud_inset_glow_artists, cloud_inset_core_artists):
        glow.set_data([], [])
        core.set_data([], [])
    for glow, core, upper, lower in zip(
        closeup_cloud_glow_artists,
        closeup_cloud_core_artists,
        closeup_cloud_upper_artists,
        closeup_cloud_lower_artists,
    ):
        glow.set_data([], [])
        core.set_data([], [])
        upper.set_data([], [])
        lower.set_data([], [])
    info_text.set_text("")
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

    z_angle_rad = simulation.body_z_angle_rad[sim_idx]
    sat_to_observer_unit = observer_pos - sat_pos
    sat_to_observer_norm = np.linalg.norm(sat_to_observer_unit)
    if sat_to_observer_norm < 1e-9:
        z_axis_dir = np.array([0.0, -1.0])
    else:
        z_axis_dir = sat_to_observer_unit / sat_to_observer_norm

    # Update cone footprint along +z direction
    cos_h, sin_h = np.cos(cone_half_angle_rad), np.sin(cone_half_angle_rad)
    rot_left = np.array([[cos_h, -sin_h], [sin_h, cos_h]])
    rot_right = np.array([[cos_h, sin_h], [-sin_h, cos_h]])
    edge_left = sat_pos + cone_length * (rot_left @ z_axis_dir)
    edge_right = sat_pos + cone_length * (rot_right @ z_axis_dir)
    cone.set_xy([sat_pos, edge_left, edge_right])
    closeup_cone.set_xy([sat_pos, edge_left, edge_right])

    left_dir = rot_left @ z_axis_dir
    center_dir = z_axis_dir
    right_dir = rot_right @ z_axis_dir
    t_left, p_left = _nearest_surface_hit(sat_pos, left_dir, cloud_arc_specs)
    t_center, p_center = _nearest_surface_hit(sat_pos, center_dir, cloud_arc_specs)
    t_right, p_right = _nearest_surface_hit(sat_pos, right_dir, cloud_arc_specs)

    nearest_intersection_km = t_center

    if p_left is not None and p_right is not None:
        left_local = p_left - observer_pos
        right_local = p_right - observer_pos
        inset_footprint.set_data([left_local[0], right_local[0]], [left_local[1], right_local[1]])
    else:
        inset_footprint.set_data([], [])

    if p_center is not None:
        center_local = p_center - observer_pos
        center_local_frame = _project_to_swiss_frame(center_local)
        inset_hit_marker.set_data([center_local_frame[0]], [center_local_frame[1]])
        sat_local = sat_pos - observer_pos
        sat_local_frame = _project_to_swiss_frame(sat_local)
        inset_centerline.set_data(
            [sat_local_frame[0], center_local_frame[0]],
            [sat_local_frame[1], center_local_frame[1]],
        )
        closeup_centerline.set_data([sat_pos[0], p_center[0]], [sat_pos[1], p_center[1]])
        closeup_hit_marker.set_data([p_center[0]], [p_center[1]])
        hit_lat_deg, hit_lon_deg = _observer_local_km_to_geo(center_local_frame)
        hit_elevation_m = _sample_swiss_elevation_m(hit_lat_deg, hit_lon_deg)
    else:
        inset_hit_marker.set_data([], [])
        inset_centerline.set_data([], [])
        closeup_centerline.set_data([], [])
        closeup_hit_marker.set_data([], [])
        hit_lat_deg, hit_lon_deg, hit_elevation_m = None, None, None

    for idx, cloud_spec in enumerate(cloud_arc_specs):
        theta = cloud_spec["theta"]
        radius = cloud_spec["radius"]
        profile_height = 0.5 * RENDER.cloud_linewidth * cloud_spec["growth"] * RENDER.closeup_cloud_height_scale
        x_mid = radius * np.cos(theta)
        y_mid = radius * np.sin(theta)
        x_hi = (radius + profile_height) * np.cos(theta)
        y_hi = (radius + profile_height) * np.sin(theta)
        x_lo = (radius - profile_height) * np.cos(theta)
        y_lo = (radius - profile_height) * np.sin(theta)
        closeup_cloud_glow_artists[idx].set_linewidth(RENDER.cloud_linewidth * 1.8 * cloud_spec["growth"])
        closeup_cloud_core_artists[idx].set_linewidth(RENDER.cloud_linewidth * cloud_spec["growth"])
        closeup_cloud_glow_artists[idx].set_data(x_mid, y_mid)
        closeup_cloud_core_artists[idx].set_data(x_mid, y_mid)
        closeup_cloud_upper_artists[idx].set_data(x_hi, y_hi)
        closeup_cloud_lower_artists[idx].set_data(x_lo, y_lo)

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
        intersection_text = f"{nearest_intersection_km:.1f} km"
    if hit_lat_deg is None:
        geo_hit_text = "none"
    else:
        geo_hit_text = f"{hit_lat_deg:.3f}N {hit_lon_deg:.3f}E @ {hit_elevation_m:.0f}m"
    speed_for_text = sim_speed_multiplier if speed_label is None else speed_label
    info_text.set_text(
        f"Orbit height: {sat_altitude:.1f} km   |   Body spin: {sat_body_rotation_rate_label}   |   z angle rel nadir: {z_angle_deg:+.1f}°   |   LOS rel nadir: {los_rel_nadir_deg:+.1f}°   |   Centerline hit: {intersection_text}   |   Swiss hit: {geo_hit_text}   |   Render window: {start_angle_deg:+.1f}° to {end_angle_deg:+.1f}°   |   Speed: {speed_for_text:.0f}x"
    )
    
    return sat, obs_to_sat_line, trail, cone, z_axis_arrow, z_axis_label, info_text, inset_footprint, inset_hit_marker, inset_centerline

def update(frame):
    global sim_time_s
    sim_time_s += (animation_interval_ms / 1000.0) * sim_speed_multiplier
    sim_idx = simulation_index_from_time(sim_time_s, wrap_orbit=True)
    return set_scene_at_index(sim_idx)

def save_one_pass_video_30x_to_project_root():
    export_speed_multiplier = SIMULATION.export_speed_multiplier
    export_fps = RENDER.export_fps
    sim_total_s = simulation.metadata.sim_total_s
    export_num_frames = max(
        2,
        int(np.ceil(sim_total_s * export_fps / export_speed_multiplier)) + 1,
    )
    export_path = Path(__file__).resolve().parents[2] / RENDER.export_filename

    def export_update(frame):
        sim_t = (frame / (export_num_frames - 1)) * sim_total_s
        sim_idx = simulation_index_from_time(sim_t, wrap_orbit=False)
        return set_scene_at_index(sim_idx, speed_label=export_speed_multiplier)

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
        export_ani.save(str(export_path), writer="ffmpeg", fps=export_fps, dpi=RENDER.export_dpi)
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
    return export_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Satellite render and video export")
    parser.add_argument(
        "--save-one-pass-30x",
        action="store_true",
        help="Save one-pass MP4 at 30x speed to project root",
    )
    args = parser.parse_args()

    plt.title(
        f"2D Satellite Orbit around Earth (h={sat_altitude:.0f} km, T={orbit_period_s/60:.1f} min)",
        color='white',
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
        plt.show()