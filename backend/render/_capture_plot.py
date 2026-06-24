import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import RENDER

if __package__:
    from ._plot_style import style_dashboard_axes, style_dashboard_legend
else:
    from render._plot_style import style_dashboard_axes, style_dashboard_legend


def build_capture_panel(
    fig: plt.Figure,
    t_s: np.ndarray,
    image_quality: np.ndarray,
    cloud_blocked_pct: np.ndarray,
) -> tuple[dict, dict]:
    """Capture conditions: image quality [0..1] (left) and cloud-blocked % (right twin)."""
    ax = fig.add_axes(RENDER.capture_axes_rect)
    style_dashboard_axes(ax, title="Capture conditions", xlabel="time [s]", ylabel="image quality")
    ax.set_xlim(float(t_s[0]), float(t_s[-1]))
    ax.set_ylim(-0.03, 1.05)

    ax2 = ax.twinx()
    ax2.set_facecolor("none")
    ax2.set_ylim(0.0, 100.0)
    ax2.tick_params(colors=RENDER.accent_cloud, labelsize=RENDER.plot_tick_fontsize, length=3, width=0.8)
    ax2.set_ylabel("cloud blocked [%]", color=RENDER.accent_cloud, fontsize=RENDER.plot_label_fontsize)
    for spine in ax2.spines.values():
        spine.set_edgecolor(RENDER.panel_edge)
        spine.set_linewidth(RENDER.panel_edge_linewidth)

    quality_arr = np.asarray(image_quality, dtype=float)
    cloud_arr = np.asarray(cloud_blocked_pct, dtype=float)

    (line_cloud,) = ax2.plot([], [], color=RENDER.accent_cloud, linewidth=1.1, linestyle="--", label="cloud blocked")
    (line_quality,) = ax.plot([], [], color=RENDER.accent_quality, linewidth=1.6, label="image quality")
    (cursor,) = ax.plot(
        [], [], color=RENDER.accent_cursor, marker="o", markersize=4,
        markeredgecolor="black", markeredgewidth=0.5, linestyle="None", zorder=5,
    )

    handles = [line_quality, line_cloud]
    labels = [h.get_label() for h in handles]
    legend = ax.legend(
        handles,
        labels,
        loc="upper left",
        fontsize=RENDER.plot_legend_fontsize,
        facecolor=RENDER.panel_bg,
        edgecolor=RENDER.panel_edge,
        labelcolor=RENDER.text_muted,
        framealpha=0.85,
    )
    if legend is not None:
        legend.get_frame().set_linewidth(0.8)

    axes = {"capture": ax, "capture_cloud": ax2}
    artists: dict = {
        "line_quality": line_quality,
        "line_cloud": line_cloud,
        "cursor": cursor,
        "t_s": np.asarray(t_s, dtype=float),
        "image_quality": quality_arr,
        "cloud_blocked_pct": cloud_arr,
    }
    return axes, artists


def update_capture_panel(artists: dict, sim_idx: int) -> None:
    t_s = artists["t_s"]
    quality = artists["image_quality"]
    cloud = artists["cloud_blocked_pct"]
    k = int(np.clip(sim_idx, 0, t_s.shape[0] - 1))
    artists["line_quality"].set_data(t_s[: k + 1], quality[: k + 1])
    artists["line_cloud"].set_data(t_s[: k + 1], cloud[: k + 1])
    q_k = float(quality[k]) if np.isfinite(quality[k]) else np.nan
    if np.isfinite(q_k):
        artists["cursor"].set_data([t_s[k]], [q_k])
    else:
        artists["cursor"].set_data([], [])
