import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from matplotlib.colors import to_rgba


from environment_definition.constants import RENDER, ureg

if __package__:
    from ._orbit_plane_static import draw_shaded_earth_disk, draw_star_field
else:
    from render._orbit_plane_static import draw_shaded_earth_disk, draw_star_field


def _target_arc_world_xy(R_earth: float, phi_lo_deg: float, phi_hi_deg: float) -> tuple[np.ndarray, np.ndarray]:
    th0 = np.deg2rad(phi_lo_deg)
    th1 = np.deg2rad(phi_hi_deg)
    n_arc = max(12, int(min(128, 4 * abs(float(phi_hi_deg - phi_lo_deg)) + 8)))
    theta_arc = np.linspace(th0, th1, n_arc, dtype=float)
    xe = R_earth * np.cos(theta_arc)
    ye = R_earth * np.sin(theta_arc)
    return xe, ye


def _closeup_world_window_km(scene: dict, *, focus_xy_km: np.ndarray | None = None) -> tuple[float, float, float, float]:
    """World-km axis limits for the closeup panel.

    When ``focus_xy_km`` is finite (primary ``camera_ground_center_xy_km``), the window
    is centered on that point so the panel tracks the live ground footprint (dynamic
    follow). Otherwise limits frame the static mission target arc midpoint.
    """
    R_earth = float(scene["R_earth"])
    tgt_a = float(scene["target_region_start_angle_deg"])
    tgt_b = float(scene["target_region_end_angle_deg"])
    target_regions_deg = scene.get("target_region_bounds_deg")
    if not target_regions_deg:
        target_regions_deg = [(tgt_a, tgt_b)]
    target_regions_deg = [(float(phi_lo_deg), float(phi_hi_deg)) for phi_lo_deg, phi_hi_deg in target_regions_deg]

    if focus_xy_km is not None and np.all(np.isfinite(focus_xy_km)):
        target_center = np.asarray(focus_xy_km, dtype=float).reshape(2)
        target_span_km = 0.0
    else:
        endpoint_x0, endpoint_y0 = _target_arc_world_xy(R_earth, target_regions_deg[0][0], target_regions_deg[0][0])
        endpoint_x1, endpoint_y1 = _target_arc_world_xy(R_earth, target_regions_deg[-1][1], target_regions_deg[-1][1])
        endpoint_0 = np.asarray([endpoint_x0[0], endpoint_y0[0]], dtype=float)
        endpoint_1 = np.asarray([endpoint_x1[0], endpoint_y1[0]], dtype=float)
        target_span_km = float(np.linalg.norm(endpoint_1 - endpoint_0))
        target_center = 0.5 * (endpoint_0 + endpoint_1)

    min_distance_km = 500.0
    margin_km = 50.0
    default_half_window_km = float(RENDER.closeup_half_window_km.to(ureg.km).magnitude)
    if target_span_km > min_distance_km:
        closeup_half_window = 0.5 * target_span_km + margin_km
    else:
        closeup_half_window = default_half_window_km

    x0 = float(target_center[0] - closeup_half_window)
    x1 = float(target_center[0] + closeup_half_window)
    y0 = float(target_center[1] - closeup_half_window)
    y1 = float(target_center[1] + closeup_half_window)
    return x0, x1, y0, y1


def build_closeup_panel(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.closeup_axes_rect)

    axes = {"closeup": ax}
    artists: dict = {}

    cloud_models = scene["cloud_models"]

    ax.set_facecolor(RENDER.space_background)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor(RENDER.panel_edge)
        spine.set_linewidth(RENDER.panel_edge_linewidth)

    R_earth = float(scene["R_earth"])
    tgt_a = float(scene["target_region_start_angle_deg"])
    tgt_b = float(scene["target_region_end_angle_deg"])
    target_regions_deg = scene.get("target_region_bounds_deg")
    if not target_regions_deg:
        target_regions_deg = [(tgt_a, tgt_b)]
    target_regions_deg = [(float(phi_lo_deg), float(phi_hi_deg)) for phi_lo_deg, phi_hi_deg in target_regions_deg]

    x0, x1, y0, y1 = _closeup_world_window_km(scene)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)

    ax.text(
        0.025, 0.965, "TARGET ZOOM",
        transform=ax.transAxes, color=RENDER.section_header_color,
        fontsize=RENDER.plot_title_fontsize, fontweight="bold", va="top", ha="left",
    )

    draw_star_field(ax)
    draw_shaded_earth_disk(ax, R_earth)

    for phi_lo_deg, phi_hi_deg in target_regions_deg:
        target_xe, target_ye = _target_arc_world_xy(R_earth, phi_lo_deg, phi_hi_deg)
        ax.plot(
            target_xe,
            target_ye,
            color=RENDER.target_band_color,
            linewidth=max(1.8, float(RENDER.target_band_linewidth)),
            solid_capstyle="round",
            zorder=RENDER.zorder_target_band,
        )

    # dynamic: cone + ground footprint + LOS
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

    artists["secondary_cone"] = Polygon(
        [[0, 0], [0, 0], [0, 0]],
        closed=True,
        facecolor="gold",
        edgecolor="gold",
        linewidth=1.2,
        linestyle="--",
        alpha=RENDER.cone_alpha,
        zorder=RENDER.zorder_closeup_cone,
    )
    ax.add_patch(artists["secondary_cone"])

    artists["ground_footprint"], = ax.plot(
        [], [],
        color=RENDER.closeup_ground_line_color,
        linewidth=RENDER.closeup_ground_line_linewidth,
        solid_capstyle="round",
        zorder=RENDER.zorder_closeup_ground,
    )

    artists["anchor_to_sat"], = ax.plot(
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


def update_closeup_panel(artists: dict, scene: dict) -> None:
    sat_pos = np.asarray(scene["sat_pos"], dtype=float)
    edge_l = np.asarray(scene["edge_l"], dtype=float)
    edge_r = np.asarray(scene["edge_r"], dtype=float)
    ground_center = np.asarray(scene["ground_center"], dtype=float)
    ground_left = np.asarray(scene["ground_left"], dtype=float)
    ground_right = np.asarray(scene["ground_right"], dtype=float)

    if np.all(np.isfinite(ground_center)):
        x0, x1, y0, y1 = _closeup_world_window_km(scene, focus_xy_km=ground_center)
        ax = artists["cone"].axes
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)

    artists["cone"].set_xy([sat_pos, edge_l, edge_r])
    artists["anchor_to_sat"].set_data(
        [scene["view_anchor_x"], sat_pos[0]],
        [scene["view_anchor_y"], sat_pos[1]],
    )

    sec_edge_l = np.asarray(scene["sec_edge_l"], dtype=float)
    sec_edge_r = np.asarray(scene["sec_edge_r"], dtype=float)
    artists["secondary_cone"].set_xy([sat_pos, sec_edge_l, sec_edge_r])

    if np.all(np.isfinite(ground_left)) and np.all(np.isfinite(ground_right)):
        artists["ground_footprint"].set_data(
            [ground_left[0], ground_center[0], ground_right[0]],
            [ground_left[1], ground_center[1], ground_right[1]],
        )
    else:
        artists["ground_footprint"].set_data([], [])

    for i, spec in enumerate(scene["cloud_world"]):
        artists["cloud_glow"][i].set_data(spec["x"], spec["y"])
        artists["cloud_core"][i].set_data(spec["x"], spec["y"])
