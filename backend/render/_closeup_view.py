import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon
from matplotlib.colors import to_rgba


from environment_definition.constants import RENDER, ureg

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

    # Target band on Earth rim, projected into observer-local close-up coords (same as cone base).
    R_earth = float(scene["R_earth"])
    theta_center = float(scene["theta_center"])
    tgt_a = float(scene["target_region_start_angle_deg"])
    tgt_b = float(scene["target_region_end_angle_deg"])
    th_arc = np.linspace(
        theta_center + np.deg2rad(tgt_a),
        theta_center + np.deg2rad(tgt_b),
        max(12, int(min(96, 4 * abs(tgt_b - tgt_a) + 8))),
        dtype=float,
    )
    xe = R_earth * np.cos(th_arc)
    ye = R_earth * np.sin(th_arc)
    hl = xe - observer_x
    vl = ye - observer_y
    ax.plot(
        hl,
        vl,
        color=RENDER.observer_color,
        linewidth=max(1.8, float(RENDER.observer_marker_edge_width)),
        solid_capstyle="round",
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


def update_closeup_panel(artists: dict, scene: dict) -> None:
    sat_pos = np.asarray(scene["sat_pos"], dtype=float)
    edge_l = np.asarray(scene["edge_l"], dtype=float)
    edge_r = np.asarray(scene["edge_r"], dtype=float)
    proj = artists["project"]

    y0, z0 = proj(float(sat_pos[0]), float(sat_pos[1]))
    yl, zl = proj(float(edge_l[0]), float(edge_l[1]))
    yr, zr = proj(float(edge_r[0]), float(edge_r[1]))
    artists["cone"].set_xy([[y0, z0], [yl, zl], [yr, zr]])
    artists["obs_to_hit"].set_data([0.0, y0], [0.0, z0])

    for i, spec in enumerate(scene["cloud_world"]):
        yl_cloud, zl_cloud = proj(spec["x"], spec["y"])
        artists["cloud_glow"][i].set_data(yl_cloud, zl_cloud)
        artists["cloud_core"][i].set_data(yl_cloud, zl_cloud)

