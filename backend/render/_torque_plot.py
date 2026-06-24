import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import RENDER

if __package__:
    from ._plot_style import style_dashboard_axes, style_dashboard_legend
else:
    from render._plot_style import style_dashboard_axes, style_dashboard_legend


def build_torque_panel(
    fig: plt.Figure,
    t_s: np.ndarray,
    torque_applied_nm: np.ndarray,
    *,
    torque_agent_nm: np.ndarray | None = None,
    applied_label: str = "applied (RW)",
) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.torque_axes_rect)
    style_dashboard_axes(ax, title="Reaction-wheel torque", xlabel="time [s]", ylabel="\u03c4 [N\u00b7m]")

    t_nm = np.asarray(torque_applied_nm, dtype=float)
    agent_nm = np.asarray(torque_agent_nm, dtype=float) if torque_agent_nm is not None else None
    stack = [t_nm] if agent_nm is None else [t_nm, agent_nm]
    finite = np.concatenate([a[np.isfinite(a)] for a in stack if a.size > 0])
    if finite.size > 0:
        tmin = float(np.min(finite))
        tmax = float(np.max(finite))
    else:
        tmin, tmax = 0.0, 1.0
    span = tmax - tmin
    pad = 1.0 if np.isclose(tmin, tmax) else 0.15 * span
    ax.set_xlim(float(t_s[0]), float(t_s[-1]))
    ax.set_ylim(tmin - pad, tmax + pad)

    ax.axhline(0.0, color=RENDER.panel_edge, linewidth=0.8, alpha=0.9, zorder=0)

    line_agent = None
    if agent_nm is not None:
        (line_agent,) = ax.plot(
            [], [], color=RENDER.accent_torque_agent, linewidth=1.0, linestyle="--", label="agent request"
        )
    (line_applied,) = ax.plot([], [], color=RENDER.accent_torque, linewidth=1.6, label=applied_label)
    (cursor,) = ax.plot(
        [], [], color=RENDER.accent_cursor, marker="o", markersize=4,
        markeredgecolor="black", markeredgewidth=0.5, linestyle="None", zorder=5,
    )
    style_dashboard_legend(ax, loc="upper right")

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
