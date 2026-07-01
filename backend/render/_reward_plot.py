import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from environment_definition.constants import RENDER

if __package__:
    from ._plot_style import (
        TAKE_PICTURE_CMD_COLOR,
        style_dashboard_axes,
        style_dashboard_legend,
        take_picture_cmd_marker_y_bounds,
    )
else:
    from render._plot_style import (
        TAKE_PICTURE_CMD_COLOR,
        style_dashboard_axes,
        style_dashboard_legend,
        take_picture_cmd_marker_y_bounds,
    )


def build_reward_panel(
    fig: plt.Figure,
    t_s: np.ndarray,
    *,
    latent_reward: np.ndarray,
    applied_reward: np.ndarray,
    title: str = "Reward",
    cmd_steps: tuple[int, ...] | None = None,
) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.reward_axes_rect)
    style_dashboard_axes(ax, title=title, ylabel="reward")
    t_arr = np.asarray(t_s, dtype=float)
    return _build_capture_reward_panel(
        ax,
        t_arr,
        np.asarray(latent_reward, dtype=float),
        np.asarray(applied_reward, dtype=float),
        cmd_steps=cmd_steps,
    )


def _build_capture_reward_panel(
    ax: plt.Axes,
    t_arr: np.ndarray,
    latent: np.ndarray,
    applied: np.ndarray,
    *,
    cmd_steps: tuple[int, ...] | None,
) -> tuple[dict, dict]:
    y_max = float(np.nanmax(latent)) if latent.size else 0.0
    y_max = max(y_max, float(np.nanmax(applied)) if applied.size else 0.0)
    pad = 1.0 if y_max <= 0.0 else 0.1 * y_max
    y_top = y_max + pad
    ax.set_xlim(float(t_arr[0]), float(t_arr[-1]))
    ax.set_ylim(0.0, y_top)

    cmd_vlines = None

    (latent_line,) = ax.plot([], [], color="cyan", linewidth=1.2, label="latent", zorder=2)
    (applied_line,) = ax.plot(
        [],
        [],
        color="gold",
        linewidth=0.0,
        marker="o",
        markersize=4,
        linestyle="None",
        label="applied",
        zorder=4,
    )
    (cursor,) = ax.plot([], [], color="yellow", marker="o", markersize=3, linestyle="None", zorder=5)

    legend_handles: list = [latent_line, applied_line]
    if cmd_steps:
        legend_handles.append(
            Patch(
                facecolor=TAKE_PICTURE_CMD_COLOR,
                edgecolor=TAKE_PICTURE_CMD_COLOR,
                linewidth=0.8,
                label="take picture",
            )
        )
    style_dashboard_legend(ax, handles=legend_handles, loc="upper right")

    artists = {
        "latent_line": latent_line,
        "applied_line": applied_line,
        "cursor": cursor,
        "cmd_vlines": cmd_vlines,
        "cmd_steps": tuple(int(s) for s in (cmd_steps or ())),
        "y_top": y_top,
        "t_s": t_arr,
        "latent_reward": latent,
        "applied_reward": applied,
    }
    return {"reward": ax}, artists


def _update_take_picture_cmd_markers(artists: dict, sim_idx: int) -> None:
    cmd_steps = artists.get("cmd_steps") or ()
    if not cmd_steps:
        return
    t_s = artists["t_s"]
    k = int(sim_idx)
    visible_times = [
        float(t_s[int(step)])
        for step in cmd_steps
        if 0 <= int(step) <= k and 0 <= int(step) < t_s.shape[0]
    ]
    ymin, ymax = take_picture_cmd_marker_y_bounds(artists["y_top"])
    ax = artists["latent_line"].axes
    cmd_vlines = artists.get("cmd_vlines")
    if visible_times:
        if cmd_vlines is None:
            artists["cmd_vlines"] = ax.vlines(
                visible_times,
                ymin=ymin,
                ymax=ymax,
                colors=TAKE_PICTURE_CMD_COLOR,
                linewidth=1.2,
                alpha=0.85,
                zorder=3,
            )
        else:
            segments = np.array([[[t, ymin], [t, ymax]] for t in visible_times], dtype=float)
            cmd_vlines.set_segments(segments)
            cmd_vlines.set_visible(True)
    elif cmd_vlines is not None:
        cmd_vlines.set_visible(False)


def update_reward_panel(artists: dict, sim_idx: int) -> None:
    t_s = artists["t_s"]
    k = int(np.clip(sim_idx, 0, t_s.shape[0] - 1))
    latent = artists["latent_reward"]
    applied = artists["applied_reward"]
    artists["latent_line"].set_data(t_s[: k + 1], latent[: k + 1])
    prefix_t = t_s[: k + 1]
    prefix_applied = applied[: k + 1]
    applied_mask = prefix_applied > 0.0
    if np.any(applied_mask):
        artists["applied_line"].set_data(prefix_t[applied_mask], prefix_applied[applied_mask])
    else:
        artists["applied_line"].set_data([], [])
    artists["cursor"].set_data([t_s[k]], [latent[k]])
    _update_take_picture_cmd_markers(artists, k)
