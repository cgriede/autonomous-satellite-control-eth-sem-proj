import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import animation as mpl_animation
from matplotlib.patches import Circle, Polygon, FancyArrowPatch
from matplotlib.widgets import Button
import argparse
from pathlib import Path
import sys

#local imports
try:
    from backend.environment_definition.constants import (
        EARTH_GRAVITATIONAL_PARAMETER,
        EARTH_RADIUS,
        RENDER,
        SIMULATION,
        UREG as ureg,
    )
    from backend.environment_definition.mission_profiles.mission_1_random_fl import SATELLITE_ALTITUDE
    from backend.utils.flight_geometry.line_of_sight import minimum_contact_angle
except ModuleNotFoundError:
    # Allow running this file directly by adding repo root to module search path.
    repo_root = str(Path(__file__).resolve().parents[2])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from backend.environment_definition.constants import (
        EARTH_GRAVITATIONAL_PARAMETER,
        EARTH_RADIUS,
        RENDER,
        SIMULATION,
        UREG as ureg,
    )
    from backend.environment_definition.mission_profiles.mission_1_random_fl import SATELLITE_ALTITUDE
    from backend.utils.flight_geometry.line_of_sight import minimum_contact_angle


# --- Parameters ---
# Earth radius in kilometers is needed for all geometric calculations.
R_earth = EARTH_RADIUS.to(ureg.km).magnitude
# Satellite altitude in kilometers positions the orbit above Earth.
sat_altitude = SATELLITE_ALTITUDE.to(ureg.km).magnitude
# Orbit radius defines the circular path used by the animation.
R_orbit = R_earth + sat_altitude
# Standard gravitational parameter sets physically realistic orbital speed.
mu_earth = EARTH_GRAVITATIONAL_PARAMETER.to((ureg.km ** 3) / (ureg.s ** 2)).magnitude
# Angular rate drives time-to-angle conversion for satellite motion.
omega = np.sqrt(mu_earth / (R_orbit ** 3))  # Realistic circular-orbit angular speed [rad/s]
# Orbit period is displayed in the title for context.
orbit_period_s = 2 * np.pi / omega
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
#TODO Start angle in radians is needed for trigonometric orbit sampling.
theta_start = theta_center + np.deg2rad(start_angle_deg)
#TODO End angle in radians closes the selected orbit snippet.
theta_end = theta_center + np.deg2rad(end_angle_deg)
# Motion span scale controls how far satellite moves versus visible window.
sat_motion_span_scale = SIMULATION.sat_motion_span_scale
# Render span determines angular extent of the visible snippet.
render_theta_span = theta_end - theta_start
# Satellite span allows overtravel through the render window if desired.
sat_theta_span = render_theta_span * sat_motion_span_scale
#TODO Span start centers the motion range around the chosen view.
sat_theta_start = 0.5 * (theta_start + theta_end) - 0.5 * sat_theta_span
# Frame count controls temporal resolution of animation and exports.
num_frames = SIMULATION.num_frames
# Total simulated time maps chosen angular span to physical time.
sim_total_s = sat_theta_span / omega
# Per-frame simulated timestep supports consistent progression.
sim_dt_s = sim_total_s / (num_frames - 1)  # Simulated seconds per animation frame
# Initial z-offset defines body-axis orientation at simulation start.
sat_z_offset_deg = SIMULATION.sat_z_offset.to(ureg.deg).magnitude
# Initial z-axis angle seeds inertial-frame body-spin direction.
sat_z_initial_angle_rad = sat_theta_start + np.pi + np.deg2rad(sat_z_offset_deg)
# Human-readable spin label is shown in the bottom info bar.
sat_body_rotation_rate_label = "0.0 arcsec/s"
# Spin rate in radians per second drives continuous z-axis rotation.
sat_body_rotation_rate_rad_s = 0.0
# UI refresh interval sets rendering cadence in milliseconds.
animation_interval_ms = SIMULATION.animation_interval.to(ureg.ms).magnitude
# Speed multiplier scales simulated time versus wall-clock animation time.
sim_speed_multiplier = SIMULATION.default_speed_multiplier
# Running simulation clock accumulates elapsed simulated seconds.
sim_time_s = 0.0

# --- Set up the figure ---
fig, ax = plt.subplots(figsize=RENDER.figure_size, constrained_layout=RENDER.constrained_layout)
fig.patch.set_facecolor(RENDER.space_background)
plot_margin = RENDER.plot_margin.to(ureg.km).magnitude
plot_limit = R_orbit + plot_margin
# Show only the selected angular snippet and make it fill the window.
# Use the full angular arc for framing (not only endpoints), otherwise
# symmetric windows around nadir can collapse y-bounds.
theta_window = np.linspace(theta_start, theta_end, 721)
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
ax.plot(
    [observer_x],
    [observer_y],
    marker='x',
    color=RENDER.observer_color,
    markersize=RENDER.observer_marker_size,
    markeredgewidth=RENDER.observer_marker_edge_width,
    zorder=RENDER.zorder_observer,
)

# Cloud arc at 15 km altitude, split into 3 parts (middle removed)
cloud_altitude = SIMULATION.cloud_altitude.to(ureg.km).magnitude
# One edge anchored at 0 deg (observer radial), extending to one side.
cloud_start_deg = SIMULATION.cloud_start_angle.to(ureg.deg).magnitude
cloud_end_deg = SIMULATION.cloud_end_angle.to(ureg.deg).magnitude
cloud_radius = R_earth + cloud_altitude
cloud_total_span_deg = cloud_end_deg - cloud_start_deg
cloud_part_span_deg = cloud_total_span_deg / 3.0
for part_start_deg, part_end_deg in [
    (cloud_start_deg, cloud_start_deg + cloud_part_span_deg),  # first segment
    (cloud_start_deg + 2 * cloud_part_span_deg, cloud_end_deg),  # third segment
]:
    cloud_theta = np.linspace(
        theta_center + np.deg2rad(part_start_deg),
        theta_center + np.deg2rad(part_end_deg),
        RENDER.cloud_segment_points,
    )
    cloud_x = cloud_radius * np.cos(cloud_theta)
    cloud_y = cloud_radius * np.sin(cloud_theta)
    ax.plot(
        cloud_x,
        cloud_y,
        color=RENDER.cloud_color,
        linewidth=RENDER.cloud_linewidth,
        alpha=RENDER.cloud_alpha,
        solid_capstyle='round',
        zorder=RENDER.zorder_cloud,
    )


# Satellite (red dot)
sat, = ax.plot([], [], RENDER.sat_marker_style, markersize=RENDER.sat_marker_size, label='Satellite')

# Observer-to-satellite line of sight
obs_to_sat_line, = ax.plot([], [], linestyle='--', color=RENDER.los_color, linewidth=RENDER.los_linewidth, alpha=RENDER.los_alpha, zorder=RENDER.zorder_los)


# Optional: faint orbit trail line
trail, = ax.plot([], [], RENDER.trail_style, linewidth=RENDER.trail_linewidth, alpha=RENDER.trail_alpha)


# Cone beam parameters (nadir-pointing instrument footprint)
cone_opening_deg = SIMULATION.cone_opening.to(ureg.deg).magnitude
cone_half_angle_rad = np.deg2rad(cone_opening_deg / 2)
cone_length = (R_orbit - R_earth) * SIMULATION.cone_length_scale
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

# Start from configured body spin rate.
set_sat_body_rotation_rate(
    SIMULATION.default_body_spin_rate.to(ureg.arcminute / ureg.s).magnitude,
    unit="arcmin",
)

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

def get_satellite_z_axis_dir(theta_now, elapsed_s):
    """Return body +z direction with constant inertial-frame spin."""
    z_axis_angle = sat_z_initial_angle_rad + sat_body_rotation_rate_rad_s * elapsed_s
    return np.array([np.cos(z_axis_angle), np.sin(z_axis_angle)])

def init():
    global sim_time_s
    sim_time_s = 0.0
    sat.set_data([], [])
    obs_to_sat_line.set_data([], [])
    trail.set_data([], [])
    cone.set_xy([[0, 0], [0, 0], [0, 0]])
    z_axis_arrow.set_positions((0, 0), (0, 0))
    z_axis_label.set_position((0, 0))
    info_text.set_text(
        f"Orbit height: {sat_altitude:.1f} km   |   Body spin: {sat_body_rotation_rate_label}   |   Render window: {start_angle_deg:+.1f}° to {end_angle_deg:+.1f}°   |   Speed: {sim_speed_multiplier:.0f}x"
    )
    return sat, obs_to_sat_line, trail, cone, z_axis_arrow, z_axis_label, info_text

def set_scene_at_time(sim_time_local, wrap_orbit=True, speed_label=None):
    # Update satellite position
    if wrap_orbit:
        theta_now = sat_theta_start + np.mod(omega * sim_time_local, sat_theta_span)
    else:
        theta_now = sat_theta_start + np.clip(omega * sim_time_local, 0.0, sat_theta_span)
    sat_pos = np.array([R_orbit * np.cos(theta_now), R_orbit * np.sin(theta_now)])
    sat.set_data([sat_pos[0]], [sat_pos[1]])
    obs_to_sat_line.set_data([observer_x, sat_pos[0]], [observer_y, sat_pos[1]])
    
    # Update trail from start of the rendering window to current position
    trail_theta = np.linspace(sat_theta_start, theta_now, RENDER.trail_points)
    trail.set_data(R_orbit * np.cos(trail_theta), R_orbit * np.sin(trail_theta))

    # Body +z follows a constant inertial-frame spin (not nadir-pointing).
    z_axis_dir = get_satellite_z_axis_dir(theta_now, sim_time_local)

    # Update cone footprint along +z direction
    cos_h, sin_h = np.cos(cone_half_angle_rad), np.sin(cone_half_angle_rad)
    rot_left = np.array([[cos_h, -sin_h], [sin_h, cos_h]])
    rot_right = np.array([[cos_h, sin_h], [-sin_h, cos_h]])
    edge_left = sat_pos + cone_length * (rot_left @ z_axis_dir)
    edge_right = sat_pos + cone_length * (rot_right @ z_axis_dir)
    cone.set_xy([sat_pos, edge_left, edge_right])

    # Satellite Z orientation (relative to nadir).
    z_axis_tip = sat_pos + z_axis_length * z_axis_dir
    z_axis_arrow.set_positions((sat_pos[0], sat_pos[1]), (z_axis_tip[0], z_axis_tip[1]))
    label_pos = z_axis_tip + RENDER.z_label_offset.to(ureg.km).magnitude * z_axis_dir
    z_axis_label.set_position((label_pos[0], label_pos[1]))
    z_angle_deg = np.rad2deg(np.arctan2(z_axis_dir[1], z_axis_dir[0]))
    speed_for_text = sim_speed_multiplier if speed_label is None else speed_label
    info_text.set_text(
        f"Orbit height: {sat_altitude:.1f} km   |   Body spin: {sat_body_rotation_rate_label}   |   z angle: {z_angle_deg:+.1f}°   |   Render window: {start_angle_deg:+.1f}° to {end_angle_deg:+.1f}°   |   Speed: {speed_for_text:.0f}x"
    )
    
    return sat, obs_to_sat_line, trail, cone, z_axis_arrow, z_axis_label, info_text

def update(frame):
    global sim_time_s
    sim_time_s += (animation_interval_ms / 1000.0) * sim_speed_multiplier
    return set_scene_at_time(sim_time_s, wrap_orbit=True)

def save_one_pass_video_30x_to_project_root():
    export_speed_multiplier = SIMULATION.export_speed_multiplier
    export_fps = RENDER.export_fps
    export_num_frames = max(
        2,
        int(np.ceil(sim_total_s * export_fps / export_speed_multiplier)) + 1,
    )
    export_path = Path(__file__).resolve().parents[2] / RENDER.export_filename

    def export_update(frame):
        sim_t = (frame / (export_num_frames - 1)) * sim_total_s
        return set_scene_at_time(sim_t, wrap_orbit=False, speed_label=export_speed_multiplier)

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
        )  # ~33 fps
        plt.show()