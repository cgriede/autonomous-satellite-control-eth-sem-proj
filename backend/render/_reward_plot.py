import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from environment_definition.constants import RENDER

if __package__:
    from ._plot_style import style_dashboard_axes, style_dashboard_legend
else:
    from render._plot_style import style_dashboard_axes, style_dashboard_legend

_TAKE_PICTURE_CMD_COLOR = "deeppink"


def build_reward_panel(
    fig: plt.Figure,
    t_s: np.ndarray,
    *,
    latent_reward: np.ndarray,
    applied_reward: np.ndarray,
    title: str = "Reward",
    cmd_times_s: tuple[float, ...] | None = None,
) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.reward_axes_rect)
    style_dashboard_axes(ax, title=title, ylabel="reward")
    t_arr = np.asarray(t_s, dtype=float)
    return _build_capture_reward_panel(
        ax,
        t_arr,
        np.asarray(latent_reward, dtype=float),
        np.asarray(applied_reward, dtype=float),
        cmd_times_s=cmd_times_s,
    )


def _build_capture_reward_panel(
    ax: plt.Axes,
    t_arr: np.ndarray,
    latent: np.ndarray,
    applied: np.ndarray,
    *,
    cmd_times_s: tuple[float, ...] | None,
) -> tuple[dict, dict]:
    y_max = float(np.nanmax(latent)) if latent.size else 0.0
    y_max = max(y_max, float(np.nanmax(applied)) if applied.size else 0.0)
    pad = 1.0 if y_max <= 0.0 else 0.1 * y_max
    ax.set_xlim(float(t_arr[0]), float(t_arr[-1]))
    ax.set_ylim(0.0, y_max + pad)

    cmd_markers = None
    if cmd_times_s:
        y_cmd = y_max + 0.04 * pad
        (cmd_markers,) = ax.plot(
            list(cmd_times_s),
            [y_cmd] * len(cmd_times_s),
            linestyle="None",
            marker="v",
            markersize=5,
            color=_TAKE_PICTURE_CMD_COLOR,
            zorder=3,
        )

    (latent_line,) = ax.plot([], [], color="cyan", linewidth=1.2, label="latent", zorder=2)
    (applied_line,) = ax.plot(
        [],
        [],
        color="gold",
        linewidth=1.0,
        drawstyle="steps-post",
        label="applied",
        zorder=2,
    )
    (cursor,) = ax.plot([], [], color="yellow", marker="o", markersize=3, linestyle="None", zorder=4)

    legend_handles: list = [latent_line, applied_line]
    if cmd_times_s:
        legend_handles.append(
            Patch(
                facecolor=_TAKE_PICTURE_CMD_COLOR,
                edgecolor=_TAKE_PICTURE_CMD_COLOR,
                linewidth=0.8,
                label="take picture",
            )
        )
    style_dashboard_legend(ax, handles=legend_handles, loc="upper right")

    artists = {
        "latent_line": latent_line,
        "applied_line": applied_line,
        "cursor": cursor,
        "cmd_markers": cmd_markers,
        "t_s": t_arr,
        "latent_reward": latent,
        "applied_reward": applied,
    }
    return {"reward": ax}, artists


def update_reward_panel(artists: dict, sim_idx: int) -> None:
    t_s = artists["t_s"]
    k = int(np.clip(sim_idx, 0, t_s.shape[0] - 1))
    latent = artists["latent_reward"]
    applied = artists["applied_reward"]
    artists["latent_line"].set_data(t_s[: k + 1], latent[: k + 1])
    artists["applied_line"].set_data(t_s[: k + 1], applied[: k + 1])
    artists["cursor"].set_data([t_s[k]], [latent[k]])
