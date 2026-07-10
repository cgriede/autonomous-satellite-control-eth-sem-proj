import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyArrowPatch
from matplotlib.colors import to_rgba


from environment_definition.constants import RENDER, ureg
from environment_definition.constants.SATELLITE import FOCAL_LENGTH, SENSOR_HEIGHT
from environment_definition.constants.SIMULATION import SIMULATION
from simulation.camera_optics import pinhole_full_fov_rad

if __package__:
    from ._earth_frame import main_panel_axis_limits
    from ._earth_photo import draw_orbit_plane_earth, draw_orbit_plane_stars
else:
    from render._earth_frame import main_panel_axis_limits
    from render._earth_photo import draw_orbit_plane_earth, draw_orbit_plane_stars


def _target_arc_world_xy(R_earth: float, phi_lo_deg: float, phi_hi_deg: float) -> tuple[np.ndarray, np.ndarray]:
    th0 = np.deg2rad(phi_lo_deg)
    th1 = np.deg2rad(phi_hi_deg)
    n_arc = max(16, int(min(256, 4 * abs(float(phi_hi_deg - phi_lo_deg)) + 8)))
    theta_tgt = np.linspace(th0, th1, n_arc, dtype=float)
    tx = R_earth * np.cos(theta_tgt)
    ty = R_earth * np.sin(theta_tgt)
    return tx, ty


def build_main_panel(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.main_axes_rect)

    axes = {"main": ax}
    artists: dict = {}

    R_earth = scene["R_earth"]
    R_orbit = scene["R_orbit"]
    theta_center = scene["theta_center"]
    start_angle_deg = scene["start_angle_deg"]
    end_angle_deg = scene["end_angle_deg"]
    cloud_models = scene["cloud_models"]
    tgt_a_deg = float(scene["target_region_start_angle_deg"])
    tgt_b_deg = float(scene["target_region_end_angle_deg"])
    target_regions_deg = scene.get("target_region_bounds_deg")
    if not target_regions_deg:
        target_regions_deg = [(tgt_a_deg, tgt_b_deg)]

    # framing (orbit-plane cross-section; matches simulation ``camera_2d`` disk XY)
    x0, x1, y0, y1 = main_panel_axis_limits(scene)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
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

    draw_orbit_plane_stars(ax)
    draw_orbit_plane_earth(ax, float(R_earth))

    # Reward-aligned observation target segments on Earth rim (dynamic color per capture state).
    artists["target_bands"] = []
    for phi_lo_deg, phi_hi_deg in target_regions_deg:
        tx, ty = _target_arc_world_xy(R_earth, float(phi_lo_deg), float(phi_hi_deg))
        (band_line,) = ax.plot(
            tx,
            ty,
            color=RENDER.target_band_color,
            linewidth=max(1.8, float(RENDER.target_band_linewidth)),
            solid_capstyle="round",
            zorder=RENDER.zorder_target_band,
        )
        artists["target_bands"].append(band_line)

    # --- dynamic artists (returned) ---
    artists["sat"], = ax.plot([], [], RENDER.sat_marker_style,
                            markersize=RENDER.sat_marker_size, label="Satellite")

    artists["anchor_to_sat"], = ax.plot(
        [], [],
        linestyle="--",
        color=RENDER.los_color,
        linewidth=RENDER.los_linewidth,
        alpha=RENDER.los_alpha,
        zorder=RENDER.zorder_los,
        visible=RENDER.show_view_anchor_los,
    )

    artists["trail"], = ax.plot([], [], RENDER.trail_style,
                                linewidth=RENDER.trail_linewidth, alpha=RENDER.trail_alpha)

    # Cone params are static render config derived from optics constants.
    _vertical_fov_rad = pinhole_full_fov_rad(sensor_dim=SENSOR_HEIGHT, focal_length=FOCAL_LENGTH)
    artists["cone_half_angle_rad"] = float(_vertical_fov_rad.to(ureg.rad).magnitude / 2.0)
    artists["cone_length_km"] = SIMULATION.cone_length.to(ureg.km).magnitude * RENDER.cone_length_render_scale

    artists["cone"] = Polygon([[0, 0], [0, 0], [0, 0]],
                            closed=True, facecolor=RENDER.cone_color, edgecolor=RENDER.cone_color,
                            alpha=RENDER.cone_alpha)
    ax.add_patch(artists["cone"])

    artists["secondary_cone"] = Polygon([[0, 0], [0, 0], [0, 0]],
                                        closed=True, facecolor="gold", edgecolor="gold",
                                        alpha=RENDER.cone_alpha, linestyle="--", linewidth=1.2)
    ax.add_patch(artists["secondary_cone"])

    # z-axis indicator (also dynamic)
    artists["z_axis_length_km"] = SIMULATION.z_axis_length.to(ureg.km).magnitude
    artists["z_axis_arrow"] = FancyArrowPatch((0, 0), (0, 0),
                                            arrowstyle="-|>", mutation_scale=RENDER.z_arrow_mutation_scale,
                                            linewidth=RENDER.z_arrow_linewidth,
                                            color=RENDER.z_arrow_color, alpha=RENDER.z_arrow_alpha,
                                            zorder=RENDER.zorder_z_axis)
    artists["z_axis_arrow"].set_visible(False)
    ax.add_patch(artists["z_axis_arrow"])

    artists["z_axis_label"] = ax.text(0, 0, RENDER.z_label_text,
                                    color=RENDER.z_label_color, fontsize=RENDER.z_label_fontsize,
                                    weight=RENDER.z_label_weight, zorder=RENDER.zorder_z_label,
                                    visible=False)

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


def update_main_panel(artists: dict, scene: dict) -> None:
    sat_pos = np.asarray(scene["sat_pos"], dtype=float)
    z_axis_dir = np.asarray(scene["z_axis_dir"], dtype=float)
    edge_l = np.asarray(scene["edge_l"], dtype=float)
    edge_r = np.asarray(scene["edge_r"], dtype=float)

    artists["sat"].set_data([sat_pos[0]], [sat_pos[1]])
    if RENDER.show_view_anchor_los:
        artists["anchor_to_sat"].set_data(
            [scene["view_anchor_x"], sat_pos[0]],
            [scene["view_anchor_y"], sat_pos[1]],
        )
    else:
        artists["anchor_to_sat"].set_data([], [])

    x, y = scene["trail_xy"]
    artists["trail"].set_data(x, y)
    artists["cone"].set_xy([sat_pos, edge_l, edge_r])
    sec_edge_l = np.asarray(scene["sec_edge_l"], dtype=float)
    sec_edge_r = np.asarray(scene["sec_edge_r"], dtype=float)
    artists["secondary_cone"].set_xy([sat_pos, sec_edge_l, sec_edge_r])

    tip = sat_pos + float(artists["z_axis_length_km"]) * z_axis_dir
    artists["z_axis_arrow"].set_positions((sat_pos[0], sat_pos[1]), (tip[0], tip[1]))
    label_pos = tip + float(RENDER.z_label_offset.to(ureg.km).magnitude) * z_axis_dir
    artists["z_axis_label"].set_position((label_pos[0], label_pos[1]))
    ax = artists["sat"].axes
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    in_frame = (x_min <= float(label_pos[0]) <= x_max) and (y_min <= float(label_pos[1]) <= y_max)
    artists["z_axis_arrow"].set_visible(in_frame)
    artists["z_axis_label"].set_visible(in_frame)

    for i, spec in enumerate(scene["cloud_world"]):
        artists["cloud_glow"][i].set_data(spec["x"], spec["y"])
        artists["cloud_core"][i].set_data(spec["x"], spec["y"])

    captured = scene.get("captured_target_indices") or frozenset()
    for i, band_line in enumerate(artists.get("target_bands", [])):
        band_line.set_color(
            RENDER.target_captured_main_color if i in captured else RENDER.target_band_color
        )