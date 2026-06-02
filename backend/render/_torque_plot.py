import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import RENDER


def build_torque_panel(
    fig: plt.Figure,
    t_s: np.ndarray,
    torque_applied_nm: np.ndarray,
    *,
    torque_agent_nm: np.ndarray | None = None,
) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.torque_axes_rect)
    ax.set_facecolor(RENDER.space_background)
    ax.set_title("Wheel torque", color=RENDER.info_text_color, fontsize=9, pad=4.0)
    ax.set_xlabel("time [s]", color=RENDER.info_text_color, fontsize=8)
    ax.set_ylabel("τ [N·m]", color=RENDER.info_text_color, fontsize=8)
    ax.tick_params(colors=RENDER.info_text_color, labelsize=7)
    for sp in ax.spines.values():
        sp.set_edgecolor(RENDER.info_text_color)
        sp.set_linewidth(0.8)
    ax.grid(True, alpha=0.2, linewidth=0.6)

    t_nm = np.asarray(torque_applied_nm, dtype=float)
    agent_nm = np.asarray(torque_agent_nm, dtype=float) if torque_agent_nm is not None else None
    stack = [t_nm] if agent_nm is None else [t_nm, agent_nm]
    finite = np.concatenate([a[np.isfinite(a)] for a in stack if a.size > 0])
    if finite.size > 0:
        tmin = float(np.min(finite))
        tmax = float(np.max(finite))
    else:
        tmin, tmax = 0.0, 1.0
    if np.isclose(tmin, tmax):
        pad = 1.0
    else:
        pad = 0.1 * (tmax - tmin)
    ax.set_xlim(float(t_s[0]), float(t_s[-1]))
    ax.set_ylim(tmin - pad, tmax + pad)

    (line_applied,) = ax.plot([], [], color="orange", linewidth=1.2, label="applied (RW)")
    line_agent = None
    if agent_nm is not None:
        (line_agent,) = ax.plot(
            [], [], color="cyan", linewidth=1.0, linestyle="--", label="agent request"
        )
    (cursor,) = ax.plot([], [], color="yellow", marker="o", markersize=3, linestyle="None")
    if agent_nm is not None:
        ax.legend(loc="upper right", fontsize=6, facecolor=RENDER.space_background, labelcolor=RENDER.info_text_color)

    axes = {"torque": ax}
    artists: dict = {
        "line_applied": line_applied,
        "cursor": cursor,
        "t_s": np.asarray(t_s, dtype=float),
        "torque_applied_nm": t_nm,
    }
    if line_agent is not None and agent_nm is not None:
        artists["line_agent"] = line_agent
        artists["torque_agent_nm"] = agent_nm
    return axes, artists


def update_torque_panel(artists: dict, sim_idx: int) -> None:
    t_s = artists["t_s"]
    torque_applied = artists["torque_applied_nm"]
    k = int(np.clip(sim_idx, 0, t_s.shape[0] - 1))
    artists["line_applied"].set_data(t_s[: k + 1], torque_applied[: k + 1])
    if "line_agent" in artists:
        torque_agent = artists["torque_agent_nm"]
        artists["line_agent"].set_data(t_s[: k + 1], torque_agent[: k + 1])
    artists["cursor"].set_data([t_s[k]], [torque_applied[k]])
