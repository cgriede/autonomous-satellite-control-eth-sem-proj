import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, FancyArrowPatch
from matplotlib.colors import to_rgba


from environment_definition.constants import RENDER, ureg
from environment_definition.constants.SATELLITE import FOCAL_LENGTH, SENSOR_HEIGHT
from environment_definition.constants.SIMULATION import SIMULATION
from simulation.camera_optics import pinhole_full_fov_rad


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

    # Reward-aligned observation target segments on Earth rim.
    for phi_lo_deg, phi_hi_deg in target_regions_deg:
        tx, ty = _target_arc_world_xy(R_earth, float(phi_lo_deg), float(phi_hi_deg))
        ax.plot(
            tx,
            ty,
            color=RENDER.target_band_color,
            linewidth=max(1.8, float(RENDER.target_band_linewidth)),
            solid_capstyle="round",
            zorder=RENDER.zorder_target_band,
        )

    # --- dynamic artists (returned) ---
    artists["sat"], = ax.plot([], [], RENDER.sat_marker_style,
                            markersize=RENDER.sat_marker_size, label="Satellite")

    artists["anchor_to_sat"], = ax.plot([], [], linestyle="--", color=RENDER.los_color,
                                        linewidth=RENDER.los_linewidth, alpha=RENDER.los_alpha,
                                        zorder=RENDER.zorder_los)

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
    artists["anchor_to_sat"].set_data(
        [scene["view_anchor_x"], sat_pos[0]],
        [scene["view_anchor_y"], sat_pos[1]],
    )

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