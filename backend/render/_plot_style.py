"""Shared styling for the dashboard time-series plots (mission-control dark theme)."""

import matplotlib.pyplot as plt

from environment_definition.constants import RENDER


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
