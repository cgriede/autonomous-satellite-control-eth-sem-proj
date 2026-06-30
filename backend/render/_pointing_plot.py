import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import RENDER

if __package__:
    from ._plot_style import style_dashboard_axes, style_dashboard_legend
else:
    from render._plot_style import style_dashboard_axes, style_dashboard_legend


def build_pointing_panel(
    fig: plt.Figure,
    t_s: np.ndarray,
    offnadir_deg: np.ndarray,
    *,
    los_offnadir_deg: np.ndarray | None = None,
    agent_offnadir_deg: np.ndarray | None = None,
) -> tuple[dict, dict]:
    """Attitude pointing: body-z and (optional) target line-of-sight angle vs nadir."""
    ax = fig.add_axes(RENDER.pointing_axes_rect)
    style_dashboard_axes(ax, title="Pointing vs nadir", ylabel="angle [\u00b0]")
    ax.tick_params(labelbottom=False)

    z_arr = np.asarray(offnadir_deg, dtype=float)
    los_arr = np.asarray(los_offnadir_deg, dtype=float) if los_offnadir_deg is not None else None
    agent_arr = np.asarray(agent_offnadir_deg, dtype=float) if agent_offnadir_deg is not None else None
    stack = [z_arr]
    if los_arr is not None:
        stack.append(los_arr)
    if agent_arr is not None:
        stack.append(agent_arr)
    finite = np.concatenate([a[np.isfinite(a)] for a in stack if a.size > 0])
    if finite.size > 0:
        lo = float(np.min(finite))
        hi = float(np.max(finite))
    else:
        lo, hi = -1.0, 1.0
    span = hi - lo
    pad = 1.0 if np.isclose(lo, hi) else 0.15 * span
    ax.set_xlim(float(t_s[0]), float(t_s[-1]))
    ax.set_ylim(lo - pad, hi + pad)

    ax.axhline(0.0, color=RENDER.panel_edge, linewidth=0.9, alpha=0.9, zorder=0)

    line_los = None
    if los_arr is not None:
        (line_los,) = ax.plot([], [], color=RENDER.accent_cursor, linewidth=1.0, linestyle="--", label="target LOS")
    line_agent = None
    if agent_arr is not None:
        (line_agent,) = ax.plot(
            [],
            [],
            color=RENDER.accent_torque_agent,
            linewidth=1.0,
            linestyle="--",
            label="agent request",
            zorder=2,
        )
    (line_z,) = ax.plot([], [], color=RENDER.accent_pointing, linewidth=1.6, label="boresight (z)")
    (cursor,) = ax.plot(
        [], [], color=RENDER.accent_cursor, marker="o", markersize=4,
        markeredgecolor="black", markeredgewidth=0.5, linestyle="None", zorder=5,
    )
    style_dashboard_legend(ax, loc="upper right", ncol=2)

    axes = {"pointing": ax}
    artists: dict = {
        "line_z": line_z,
        "cursor": cursor,
        "t_s": np.asarray(t_s, dtype=float),
        "offnadir_deg": z_arr,
    }
    if line_los is not None and los_arr is not None:
        artists["line_los"] = line_los
        artists["los_offnadir_deg"] = los_arr
    if line_agent is not None and agent_arr is not None:
        artists["line_agent"] = line_agent
        artists["agent_offnadir_deg"] = agent_arr
    return axes, artists


def update_pointing_panel(artists: dict, sim_idx: int) -> None:
    t_s = artists["t_s"]
    z_arr = artists["offnadir_deg"]
    k = int(np.clip(sim_idx, 0, t_s.shape[0] - 1))
    artists["line_z"].set_data(t_s[: k + 1], z_arr[: k + 1])
    if "line_los" in artists:
        artists["line_los"].set_data(t_s[: k + 1], artists["los_offnadir_deg"][: k + 1])
    if "line_agent" in artists:
        artists["line_agent"].set_data(t_s[: k + 1], artists["agent_offnadir_deg"][: k + 1])
    artists["cursor"].set_data([t_s[k]], [z_arr[k]])
