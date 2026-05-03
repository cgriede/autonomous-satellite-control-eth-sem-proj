import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import RENDER


def build_torque_panel(fig: plt.Figure, t_s: np.ndarray, torque_nm: np.ndarray) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.torque_axes_rect)
    ax.set_facecolor(RENDER.space_background)
    ax.set_title("Wheel torque command", color=RENDER.info_text_color, fontsize=9, pad=4.0)
    ax.set_xlabel("time [s]", color=RENDER.info_text_color, fontsize=8)
    ax.set_ylabel("τ_cmd [N·m]", color=RENDER.info_text_color, fontsize=8)
    ax.tick_params(colors=RENDER.info_text_color, labelsize=7)
    for sp in ax.spines.values():
        sp.set_edgecolor(RENDER.info_text_color)
        sp.set_linewidth(0.8)
    ax.grid(True, alpha=0.2, linewidth=0.6)

    t_nm = np.asarray(torque_nm, dtype=float)
    finite = np.isfinite(t_nm)
    if np.any(finite):
        tmin = float(np.nanmin(t_nm))
        tmax = float(np.nanmax(t_nm))
    else:
        tmin, tmax = 0.0, 1.0
    if np.isclose(tmin, tmax):
        pad = 1.0
    else:
        pad = 0.1 * (tmax - tmin)
    ax.set_xlim(float(t_s[0]), float(t_s[-1]))
    ax.set_ylim(tmin - pad, tmax + pad)

    (line,) = ax.plot([], [], color="cyan", linewidth=1.2)
    (cursor,) = ax.plot([], [], color="yellow", marker="o", markersize=3, linestyle="None")

    axes = {"torque": ax}
    artists = {
        "line": line,
        "cursor": cursor,
        "t_s": np.asarray(t_s, dtype=float),
        "torque_nm": t_nm,
    }
    return axes, artists


def update_torque_panel(artists: dict, sim_idx: int) -> None:
    t_s = artists["t_s"]
    torque_nm = artists["torque_nm"]
    k = int(np.clip(sim_idx, 0, t_s.shape[0] - 1))
    artists["line"].set_data(t_s[: k + 1], torque_nm[: k + 1])
    artists["cursor"].set_data([t_s[k]], [torque_nm[k]])
