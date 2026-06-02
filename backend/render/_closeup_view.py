import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from matplotlib.colors import to_rgba


from environment_definition.constants import RENDER, ureg


def _target_arc_world_xy(R_earth: float, phi_lo_deg: float, phi_hi_deg: float) -> tuple[np.ndarray, np.ndarray]:
    th0 = np.deg2rad(phi_lo_deg)
    th1 = np.deg2rad(phi_hi_deg)
    n_arc = max(12, int(min(128, 4 * abs(float(phi_hi_deg - phi_lo_deg)) + 8)))
    theta_arc = np.linspace(th0, th1, n_arc, dtype=float)
    xe = R_earth * np.cos(theta_arc)
    ye = R_earth * np.sin(theta_arc)
    return xe, ye


def build_closeup_panel(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.closeup_axes_rect)

    axes = {"closeup": ax}
    artists: dict = {}

    view_anchor_x = float(scene["view_anchor_x"])
    view_anchor_y = float(scene["view_anchor_y"])
    cloud_models = scene["cloud_models"]

    ax.set_facecolor(RENDER.space_background)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor(RENDER.info_text_color)
        spine.set_linewidth(1.0)

    R_earth = float(scene["R_earth"])
    tgt_a = float(scene["target_region_start_angle_deg"])
    tgt_b = float(scene["target_region_end_angle_deg"])
    target_regions_deg = scene.get("target_region_bounds_deg")
    if not target_regions_deg:
        target_regions_deg = [(tgt_a, tgt_b)]
    target_regions_deg = [(float(phi_lo_deg), float(phi_hi_deg)) for phi_lo_deg, phi_hi_deg in target_regions_deg]

    context_lo_deg = min(phi_lo_deg for phi_lo_deg, _ in target_regions_deg)
    context_hi_deg = max(phi_hi_deg for _, phi_hi_deg in target_regions_deg)
    context_xe, context_ye = _target_arc_world_xy(R_earth, context_lo_deg, context_hi_deg)

    def project_xy_to_closeup(x_world_km: float, y_world_km: float):
        x_arr = np.asarray(x_world_km, dtype=float)
        y_arr = np.asarray(y_world_km, dtype=float)
        projected_x = x_arr - view_anchor_x
        projected_y = y_arr - view_anchor_y
        if projected_x.ndim == 0:
            return float(projected_x), float(projected_y)
        return projected_x, projected_y

    artists["project"] = project_xy_to_closeup

    ax.text(
        0.02, 0.98, "Target Zoom",
        transform=ax.transAxes, color=RENDER.info_text_color,
        fontsize=8, va="top", ha="left",
    )

    endpoint_x0, endpoint_y0 = _target_arc_world_xy(R_earth, target_regions_deg[0][0], target_regions_deg[0][0])
    endpoint_x1, endpoint_y1 = _target_arc_world_xy(R_earth, target_regions_deg[-1][1], target_regions_deg[-1][1])
    endpoint_0 = np.asarray(project_xy_to_closeup(endpoint_x0[0], endpoint_y0[0]), dtype=float)
    endpoint_1 = np.asarray(project_xy_to_closeup(endpoint_x1[0], endpoint_y1[0]), dtype=float)
    target_span_km = float(np.linalg.norm(endpoint_1 - endpoint_0))
    target_center = 0.5 * (endpoint_0 + endpoint_1)
    min_distance_km = 500.0
    margin_km = 50.0
    default_half_window_km = float(RENDER.closeup_half_window_km.to(ureg.km).magnitude)
    if target_span_km > min_distance_km:
        closeup_half_window = 0.5 * target_span_km + margin_km
    else:
        closeup_half_window = default_half_window_km
    ax.set_xlim(target_center[0] - closeup_half_window, target_center[0] + closeup_half_window)
    ax.set_ylim(target_center[1] - closeup_half_window, target_center[1] + closeup_half_window)

    crust_h, crust_v = project_xy_to_closeup(context_xe, context_ye)
    ax.plot(
        crust_h,
        crust_v,
        color=RENDER.closeup_ground_line_color,
        linewidth=max(1.2, float(RENDER.closeup_ground_line_linewidth)),
        alpha=RENDER.earth_outline_alpha,
        solid_capstyle="round",
        zorder=RENDER.zorder_closeup_ground,
    )
    for phi_lo_deg, phi_hi_deg in target_regions_deg:
        target_xe, target_ye = _target_arc_world_xy(R_earth, phi_lo_deg, phi_hi_deg)
        target_h, target_v = project_xy_to_closeup(target_xe, target_ye)
        ax.plot(
            target_h,
            target_v,
            color=RENDER.target_band_color,
            linewidth=max(1.8, float(RENDER.target_band_linewidth)),
            solid_capstyle="round",
            zorder=RENDER.zorder_closeup_target_band,
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

    artists["hit"], = ax.plot(
        [], [], marker="o", color="yellow", markersize=4,
        linestyle="None", zorder=RENDER.zorder_closeup_hit,
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
    proj = artists["project"]

    y0, z0 = proj(float(sat_pos[0]), float(sat_pos[1]))
    yl, zl = proj(float(edge_l[0]), float(edge_l[1]))
    yr, zr = proj(float(edge_r[0]), float(edge_r[1]))
    artists["cone"].set_xy([[y0, z0], [yl, zl], [yr, zr]])
    artists["anchor_to_sat"].set_data([0.0, y0], [0.0, z0])

    sec_edge_l = np.asarray(scene["sec_edge_l"], dtype=float)
    sec_edge_r = np.asarray(scene["sec_edge_r"], dtype=float)
    ysl, zsl = proj(float(sec_edge_l[0]), float(sec_edge_l[1]))
    ysr, zsr = proj(float(sec_edge_r[0]), float(sec_edge_r[1]))
    artists["secondary_cone"].set_xy([[y0, z0], [ysl, zsl], [ysr, zsr]])

    for i, spec in enumerate(scene["cloud_world"]):
        yl_cloud, zl_cloud = proj(spec["x"], spec["y"])
        artists["cloud_glow"][i].set_data(yl_cloud, zl_cloud)
        artists["cloud_core"][i].set_data(yl_cloud, zl_cloud)
