import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from environment_definition.constants import RENDER

_TAKE_PICTURE_CMD_COLOR = "deeppink"


def build_reward_panel(
    fig: plt.Figure,
    t_s: np.ndarray,
    latent_reward: np.ndarray,
    applied_reward: np.ndarray,
    *,
    capture_windows_s: list[tuple[float, float]] | None = None,
) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.reward_axes_rect)
    ax.set_facecolor(RENDER.space_background)
    ax.set_title("Reward", color=RENDER.info_text_color, fontsize=9, pad=4.0)
    ax.set_xlabel("time [s]", color=RENDER.info_text_color, fontsize=8)
    ax.set_ylabel("reward", color=RENDER.info_text_color, fontsize=8)
    ax.tick_params(colors=RENDER.info_text_color, labelsize=7)
    for sp in ax.spines.values():
        sp.set_edgecolor(RENDER.info_text_color)
        sp.set_linewidth(0.8)
    ax.grid(True, alpha=0.2, linewidth=0.6)

    latent = np.asarray(latent_reward, dtype=float)
    applied = np.asarray(applied_reward, dtype=float)
    t_arr = np.asarray(t_s, dtype=float)

    y_max = float(np.nanmax(latent)) if latent.size else 0.0
    y_max = max(y_max, float(np.nanmax(applied)) if applied.size else 0.0)
    pad = 1.0 if y_max <= 0.0 else 0.1 * y_max
    ax.set_xlim(float(t_arr[0]), float(t_arr[-1]))
    ax.set_ylim(0.0, y_max + pad)

    for t0, t1 in capture_windows_s or ():
        ax.axvspan(
            t0,
            t1,
            ymin=0.0,
            ymax=1.0,
            color=_TAKE_PICTURE_CMD_COLOR,
            alpha=0.22,
            linewidth=0,
            zorder=0,
        )
        ax.axvline(
            t0,
            color=_TAKE_PICTURE_CMD_COLOR,
            alpha=0.85,
            linewidth=1.2,
            linestyle="-",
            zorder=1,
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
    (cursor,) = ax.plot([], [], color="yellow", marker="o", markersize=3, linestyle="None", zorder=3)

    legend_handles: list = [latent_line, applied_line]
    if capture_windows_s:
        legend_handles.append(
            Patch(
                facecolor=_TAKE_PICTURE_CMD_COLOR,
                alpha=0.35,
                edgecolor=_TAKE_PICTURE_CMD_COLOR,
                linewidth=0.8,
                label="take picture",
            )
        )
    ax.legend(
        handles=legend_handles,
        loc="upper right",
        fontsize=6,
        facecolor=RENDER.space_background,
        labelcolor=RENDER.info_text_color,
    )

    axes = {"reward": ax}
    artists = {
        "latent_line": latent_line,
        "applied_line": applied_line,
        "cursor": cursor,
        "t_s": t_arr,
        "latent_reward": latent,
        "applied_reward": applied,
    }
    return axes, artists


def update_reward_panel(artists: dict, sim_idx: int) -> None:
    t_s = artists["t_s"]
    latent = artists["latent_reward"]
    applied = artists["applied_reward"]
    k = int(np.clip(sim_idx, 0, t_s.shape[0] - 1))
    artists["latent_line"].set_data(t_s[: k + 1], latent[: k + 1])
    artists["applied_line"].set_data(t_s[: k + 1], applied[: k + 1])
    artists["cursor"].set_data([t_s[k]], [latent[k]])
