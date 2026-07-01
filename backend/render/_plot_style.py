"""Shared styling for the dashboard time-series plots (mission-control dark theme)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from environment_definition.constants import RENDER

TAKE_PICTURE_CMD_COLOR = "deeppink"


def take_picture_cmd_marker_y_bounds(y_top: float) -> tuple[float, float]:
    """Short band above the x-axis — visible but not enormous."""
    span = max(float(y_top), 1.0)
    return 0.03 * span, 0.09 * span


def style_dashboard_axes(
    ax: plt.Axes,
    *,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
    grid: bool = True,
) -> None:
    """Apply the shared dark-panel look to a time-series axis."""
    ax.set_facecolor(RENDER.panel_bg)
    for spine in ax.spines.values():
        spine.set_edgecolor(RENDER.panel_edge)
        spine.set_linewidth(RENDER.panel_edge_linewidth)
    ax.tick_params(colors=RENDER.text_muted, labelsize=RENDER.plot_tick_fontsize, length=3, width=0.8)
    if grid:
        ax.grid(True, color=RENDER.grid_color, alpha=RENDER.grid_alpha, linewidth=0.6)
        ax.set_axisbelow(True)
    if title is not None:
        ax.set_title(
            title,
            color=RENDER.title_color,
            fontsize=RENDER.plot_title_fontsize,
            pad=RENDER.plot_title_pad,
            fontweight="bold",
        )
    if xlabel is not None:
        ax.set_xlabel(xlabel, color=RENDER.text_muted, fontsize=RENDER.plot_label_fontsize)
    if ylabel is not None:
        ax.set_ylabel(ylabel, color=RENDER.text_muted, fontsize=RENDER.plot_label_fontsize)


def style_dashboard_legend(ax: plt.Axes, **kwargs) -> None:
    """Legend with theme-consistent dark facecolor and muted labels."""
    legend = ax.legend(
        fontsize=RENDER.plot_legend_fontsize,
        facecolor=RENDER.panel_bg,
        edgecolor=RENDER.panel_edge,
        labelcolor=RENDER.text_muted,
        framealpha=0.85,
        **kwargs,
    )
    if legend is not None:
        legend.get_frame().set_linewidth(0.8)


def style_dashboard_figure(
    fig: plt.Figure,
    *,
    title: str | None = None,
    title_y: float = 0.995,
    title_fontsize: int = 12,
) -> None:
    """Black figure background and muted suptitle for dashboard-style exports."""
    fig.patch.set_facecolor(RENDER.space_background)
    if title is not None:
        fig.suptitle(
            title,
            color=RENDER.text_muted,
            fontsize=title_fontsize,
            y=title_y,
        )


def set_dashboard_xlabel(ax: plt.Axes, text: str) -> None:
    ax.set_xlabel(text, color=RENDER.text_muted, fontsize=RENDER.plot_label_fontsize)


def save_dashboard_figure(fig: plt.Figure, path: Path | str, *, dpi: int = 120, **kwargs: Any) -> None:
    """Save preserving dark facecolor (avoids white margins in PNG)."""
    fig.savefig(
        path,
        dpi=dpi,
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
        **kwargs,
    )
