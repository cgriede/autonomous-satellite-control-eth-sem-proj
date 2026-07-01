"""Static reward/torque episode plots from canonical simulation series (view-only)."""

from __future__ import annotations

import numpy as np
from matplotlib.patches import Patch

from environment_definition.constants import RENDER
from simulation.capture_reward import applied_capture_reward_series, latent_capture_reward_series
from simulation.state_types import SimulationStateSeries

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


def series_attitude_request_mode(series: SimulationStateSeries) -> str:
    return str(getattr(series.metadata, "attitude_request_mode", "torque") or "torque").lower()


def series_uses_obc_pointing(series: SimulationStateSeries) -> bool:
    return "obc" in str(series.metadata.controller_mode).lower()


def torque_agent_series_for_plot(series: SimulationStateSeries) -> np.ndarray | None:
    """Agent-requested wheel torque for dashboard plots (torque mode only)."""
    if series_uses_obc_pointing(series) or series_attitude_request_mode(series) == "vector":
        return None
    return np.asarray(series.wheel_torque_agent_cmd_nm, dtype=float)


def agent_pointing_offnadir_deg_for_plot(series: SimulationStateSeries) -> np.ndarray | None:
    """Agent-requested boresight off-nadir for vector-mode pointing plots."""
    if series_attitude_request_mode(series) != "vector":
        return None
    arr = series.agent_pointing_offnadir_deg
    if arr is None:
        return None
    return np.asarray(arr, dtype=float)


def take_picture_cmd_steps(series: SimulationStateSeries) -> tuple[int, ...]:
    meta = series.metadata
    if meta.take_picture_cmd_steps:
        return tuple(int(s) for s in meta.take_picture_cmd_steps)
    baseline = meta.baseline_shutter_cmd_steps
    if baseline:
        return tuple(int(s) for s in baseline)
    cmd = series.baseline_take_picture_cmd
    if cmd is not None:
        return tuple(int(i) for i in np.flatnonzero(np.asarray(cmd, dtype=bool)))
    return ()


def take_picture_cmd_times_s(series: SimulationStateSeries) -> tuple[float, ...]:
    steps = take_picture_cmd_steps(series)
    if not steps:
        return ()
    t_s = np.asarray(series.t_s, dtype=float)
    return tuple(float(t_s[int(k)]) for k in steps if 0 <= int(k) < t_s.shape[0])


def draw_episode_reward_axes(
    ax,
    series: SimulationStateSeries,
    *,
    title: str | None = None,
    show_legend: bool = True,
) -> None:
    t_arr = np.asarray(series.t_s, dtype=float)
    cmd_steps = take_picture_cmd_steps(series)
    latent = latent_capture_reward_series(series)
    applied = applied_capture_reward_series(series, cmd_steps=cmd_steps)
    cmd_times_s = take_picture_cmd_times_s(series)

    style_dashboard_axes(ax, title=title, ylabel="reward")
    y_max = float(np.nanmax(latent)) if latent.size else 0.0
    y_max = max(y_max, float(np.nanmax(applied)) if applied.size else 0.0)
    pad = 1.0 if y_max <= 0.0 else 0.1 * y_max
    y_top = y_max + pad
    ax.set_xlim(float(t_arr[0]), float(t_arr[-1]))
    ax.set_ylim(0.0, y_top)

    if cmd_times_s:
        ymin, ymax = take_picture_cmd_marker_y_bounds(y_top)
        ax.vlines(
            list(cmd_times_s),
            ymin=ymin,
            ymax=ymax,
            colors=TAKE_PICTURE_CMD_COLOR,
            linewidth=1.2,
            alpha=0.85,
            zorder=3,
        )

    (latent_line,) = ax.plot(t_arr, latent, color="cyan", linewidth=1.2, label="latent", zorder=2)
    applied_mask = applied > 0.0
    if np.any(applied_mask):
        (applied_line,) = ax.plot(
            t_arr[applied_mask],
            applied[applied_mask],
            color="gold",
            linewidth=0.0,
            marker="o",
            markersize=4,
            linestyle="None",
            label="applied",
            zorder=4,
        )
    else:
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

    legend_handles: list = [latent_line, applied_line]
    if cmd_times_s:
        legend_handles.append(
            Patch(
                facecolor=TAKE_PICTURE_CMD_COLOR,
                edgecolor=TAKE_PICTURE_CMD_COLOR,
                linewidth=0.8,
                label="take picture",
            )
        )
    if show_legend:
        style_dashboard_legend(ax, handles=legend_handles, loc="upper right")


def draw_episode_torque_axes(
    ax,
    series: SimulationStateSeries,
    *,
    title: str | None = None,
    show_legend: bool = True,
) -> None:
    t_arr = np.asarray(series.t_s, dtype=float)
    torque_applied = np.asarray(series.wheel_torque_cmd_nm, dtype=float)
    torque_agent = torque_agent_series_for_plot(series)
    use_obc = series_uses_obc_pointing(series)

    style_dashboard_axes(ax, title=title, ylabel="\u03c4 [N\u00b7m]")
    stack = [torque_applied] if torque_agent is None else [torque_applied, torque_agent]
    finite = np.concatenate([a[np.isfinite(a)] for a in stack if a.size > 0])
    if finite.size > 0:
        tmin = float(np.min(finite))
        tmax = float(np.max(finite))
    else:
        tmin, tmax = 0.0, 1.0
    span = tmax - tmin
    pad = 1.0 if np.isclose(tmin, tmax) else 0.15 * span
    ax.set_xlim(float(t_arr[0]), float(t_arr[-1]))
    ax.set_ylim(tmin - pad, tmax + pad)
    ax.axhline(0.0, color=RENDER.panel_edge, linewidth=0.8, alpha=0.9, zorder=0)

    applied_label = "OBC pointing (RW)" if use_obc else "applied (RW)"
    ax.plot(t_arr, torque_applied, color=RENDER.accent_torque, linewidth=1.6, label=applied_label, zorder=1)
    if torque_agent is not None:
        ax.plot(
            t_arr,
            torque_agent,
            color=RENDER.accent_torque_agent,
            linewidth=1.0,
            linestyle="--",
            label="agent request",
            zorder=2,
        )
    if show_legend:
        style_dashboard_legend(ax, loc="upper right")


def draw_episode_pointing_axes(
    ax,
    series: SimulationStateSeries,
    *,
    title: str | None = None,
    show_legend: bool = True,
) -> None:
    t_arr = np.asarray(series.t_s, dtype=float)
    nadir_angle = series.theta_orbit_rad + np.pi
    z_offnadir_rad = np.arctan2(
        np.sin(series.body_z_angle_rad - nadir_angle),
        np.cos(series.body_z_angle_rad - nadir_angle),
    )
    offnadir_deg = np.rad2deg(z_offnadir_rad)
    agent_offnadir_deg = agent_pointing_offnadir_deg_for_plot(series)

    stack = [offnadir_deg]
    if agent_offnadir_deg is not None:
        stack.append(agent_offnadir_deg)
    finite = np.concatenate([a[np.isfinite(a)] for a in stack if a.size > 0])
    if finite.size > 0:
        lo = float(np.min(finite))
        hi = float(np.max(finite))
    else:
        lo, hi = -1.0, 1.0
    span = hi - lo
    pad = 1.0 if np.isclose(lo, hi) else 0.15 * span

    style_dashboard_axes(ax, title=title or "Pointing vs nadir", ylabel="angle [\u00b0]")
    ax.set_xlim(float(t_arr[0]), float(t_arr[-1]))
    ax.set_ylim(lo - pad, hi + pad)
    ax.axhline(0.0, color=RENDER.panel_edge, linewidth=0.9, alpha=0.9, zorder=0)
    ax.plot(t_arr, offnadir_deg, color=RENDER.accent_pointing, linewidth=1.6, label="boresight (z)", zorder=1)
    if agent_offnadir_deg is not None:
        ax.plot(
            t_arr,
            agent_offnadir_deg,
            color=RENDER.accent_torque_agent,
            linewidth=1.0,
            linestyle="--",
            label="agent request",
            zorder=2,
        )
    if show_legend:
        style_dashboard_legend(ax, loc="upper right", ncol=2)
