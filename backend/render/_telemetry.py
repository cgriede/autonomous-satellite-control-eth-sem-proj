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
    text = "\n\n".join(
        [
            "\n".join(
                [
                    "Orbit / attitude",
                    f"  Orbit height: {scene['orbit_altitude_km']:.1f} km",
                    f"  Body spin: {scene['sat_body_rotation_rate_label']}",
                    f"  z angle rel nadir: {scene['z_angle_rel_nadir_deg']:+.1f} deg",
                    f"  LOS rel nadir: {scene['los_rel_nadir_deg']:+.1f} deg",
                    f"  Render window: {scene['render_window_text']}",
                ]
            ),
            "\n".join(
                [
                    "Camera / strip",
                    f"  GSD: {gsd_txt}, V-FOV: {scene['camera_vfov_deg']:.2f} deg",
                    f"  Swath height: {swath_txt}",
                    f"  Strip cloud blocked: {blocked_txt}",
                ]
            ),
            "\n".join(
                [
                    "Hits",
                    f"  Centerline hit: {scene['intersection_text']}",
                    f"  Ground patch hit: {scene['ground_patch_hit_text']}",
                ]
            ),
            "\n".join(
                [
                    "Playback",
                    f"  Controller mode: {scene['controller_mode']}",
                    f"  Speed: {scene['sim_speed_multiplier']:.0f}x",
                    f"  Frame: {scene['sim_idx']}",
                ]
            ),
        ]
    )
    artists["text"].set_text(text)