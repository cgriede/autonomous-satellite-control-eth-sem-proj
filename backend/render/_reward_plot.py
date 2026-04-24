import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import RENDER


def build_reward_panel(fig: plt.Figure, t_s: np.ndarray, reward: np.ndarray) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.reward_axes_rect)
    ax.set_facecolor(RENDER.space_background)
    ax.set_title("Reward over time", color=RENDER.info_text_color, fontsize=9, pad=4.0)
    ax.set_xlabel("time [s]", color=RENDER.info_text_color, fontsize=8)
    ax.set_ylabel("reward", color=RENDER.info_text_color, fontsize=8)
    ax.tick_params(colors=RENDER.info_text_color, labelsize=7)
    for sp in ax.spines.values():
        sp.set_edgecolor(RENDER.info_text_color)
        sp.set_linewidth(0.8)
    ax.grid(True, alpha=0.2, linewidth=0.6)

    reward_min = float(np.nanmin(reward))
    reward_max = float(np.nanmax(reward))
    if np.isclose(reward_min, reward_max):
        pad = 1.0
    else:
        pad = 0.1 * (reward_max - reward_min)
    ax.set_xlim(float(t_s[0]), float(t_s[-1]))
    ax.set_ylim(reward_min - pad, reward_max + pad)

    (line,) = ax.plot([], [], color="cyan", linewidth=1.2)
    (cursor,) = ax.plot([], [], color="yellow", marker="o", markersize=3, linestyle="None")

    axes = {"reward": ax}
    artists = {
        "line": line,
        "cursor": cursor,
        "t_s": np.asarray(t_s, dtype=float),
        "reward": np.asarray(reward, dtype=float),
    }
    return axes, artists


def update_reward_panel(artists: dict, sim_idx: int) -> None:
    t_s = artists["t_s"]
    reward = artists["reward"]
    k = int(np.clip(sim_idx, 0, t_s.shape[0] - 1))
    artists["line"].set_data(t_s[: k + 1], reward[: k + 1])
    artists["cursor"].set_data([t_s[k]], [reward[k]])
