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
        0.96,
        "",
        transform=ax.transAxes,
        color=RENDER.info_text_color,
        fontsize=9,
        family=RENDER.info_panel_fontfamily,
        va="top",
        ha="left",
        linespacing=1.35,
        clip_on=True,
    )

    return axes, artists


def update_telemetry_panel(artists: dict, scene: dict) -> None:
    gsd_txt = f"{scene['camera_gsd_m']:.2f} m" if np.isfinite(scene["camera_gsd_m"]) else "n/a"
    swath_txt = (
        f"{scene['camera_swath_height_km']:.1f} km" if np.isfinite(scene["camera_swath_height_km"]) else "n/a"
    )
    blocked_txt = f"{scene['cloud_blocked_pct']:.0f}%" if np.isfinite(scene["cloud_blocked_pct"]) else "n/a"
    smear_px = float(scene.get("camera_image_smear_px", float("nan")))
    quality = float(scene.get("camera_image_quality", float("nan")))
    if np.isfinite(smear_px) and np.isfinite(quality):
        image_quality_txt = f"quality {quality:.6f}  ·  smear {smear_px:.3f} px"
    elif np.isfinite(smear_px):
        image_quality_txt = f"smear {smear_px:.3f} px  ·  quality n/a"
    else:
        image_quality_txt = "n/a"
    text = "\n".join(
        [
            "Orbit / attitude",
            f"  {scene['controller_mode']}  ·  h {scene['orbit_altitude_km']:.1f} km",
            f"  spin {scene['sat_body_rotation_rate_label']}",
            f"  z {scene['z_angle_rel_nadir_deg']:+.1f}°  ·  LOS {scene['los_rel_nadir_deg']:+.1f}°",
            f"  window {scene['render_window_text']}",
            "Camera / strip",
            f"  GSD {gsd_txt}  ·  FOV {scene['camera_vfov_deg']:.2f}°",
            f"  swath {swath_txt}  ·  blocked {blocked_txt}",
            f"  image {image_quality_txt}",
            "Hits",
            f"  center {scene['intersection_text']}",
            f"  ground {scene['ground_patch_hit_text']}",
            f"Playback  {scene['sim_speed_multiplier']:.0f}x  ·  frame {scene['sim_idx']}",
        ]
    )
    artists["text"].set_text(text)
