import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import RENDER, ureg



def build_telemetry_panel(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.telemetry_axes_rect)

    axes = {"telemetry": ax}
    artists: dict = {}

    ax.set_facecolor(RENDER.space_background)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor(RENDER.info_text_color)
        sp.set_linewidth(0.8)

    artists["text"] = ax.text(
        0.04,
        0.98,
        "",
        transform=ax.transAxes,
        color=RENDER.info_text_color,
        fontsize=RENDER.info_panel_fontsize,
        family=RENDER.info_panel_fontfamily,
        va="top",
        ha="left",
        linespacing=1.14,
    )

    return axes, artists


def update_telemetry_panel(artists: dict, scene: dict) -> None:
    gsd_txt = f"{scene['camera_gsd_m']:.2f} m" if np.isfinite(scene["camera_gsd_m"]) else "n/a"
    swath_txt = (
        f"{scene['camera_swath_height_km']:.1f} km" if np.isfinite(scene["camera_swath_height_km"]) else "n/a"
    )
    blocked_txt = f"{scene['cloud_blocked_pct']:.0f}%" if np.isfinite(scene["cloud_blocked_pct"]) else "n/a"

    text = "\n".join(
        [
            "Render telemetry",
            f"  frame: {scene['sim_idx']}",
            f"  orbit altitude: {scene['orbit_altitude_km']:.1f} km",
            f"  GSD: {gsd_txt}",
            f"  V-FOV: {scene['camera_vfov_deg']:.2f} deg",
            f"  swath: {swath_txt}",
            f"  strip cloud blocked: {blocked_txt}",
            f"  speed: {scene['sim_speed_multiplier']:.0f}x",
        ]
    )
    artists["text"].set_text(text)