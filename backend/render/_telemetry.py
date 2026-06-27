import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import RENDER


def build_telemetry_panel(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    ax = fig.add_axes(RENDER.telemetry_axes_rect)

    axes = {"telemetry": ax}
    artists: dict = {}

    ax.set_facecolor(RENDER.panel_bg)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_edgecolor(RENDER.panel_edge)
        sp.set_linewidth(RENDER.panel_edge_linewidth)

    ax.text(
        0.045,
        0.972,
        "TELEMETRY",
        transform=ax.transAxes,
        color=RENDER.section_header_color,
        fontsize=RENDER.plot_title_fontsize,
        family=RENDER.info_panel_fontfamily,
        fontweight="bold",
        va="top",
        ha="left",
    )

    artists["text"] = ax.text(
        0.045,
        0.925,
        "",
        transform=ax.transAxes,
        color="#d8e3f5",
        fontsize=RENDER.telemetry_fontsize,
        family=RENDER.info_panel_fontfamily,
        va="top",
        ha="left",
        linespacing=1.3,
        clip_on=True,
    )

    return axes, artists


def _fmt(value: float, suffix: str, fmt: str = "{:.2f}") -> str:
    return (fmt.format(value) + suffix) if np.isfinite(value) else "n/a"


def update_telemetry_panel(artists: dict, scene: dict) -> None:
    gsd_txt = _fmt(scene["camera_gsd_m"], " m")
    swath_txt = _fmt(scene["camera_swath_height_km"], " km", "{:.1f}")
    blocked_txt = _fmt(scene["cloud_blocked_pct"], "%", "{:.0f}")
    smear_px = float(scene.get("camera_image_smear_px", float("nan")))
    quality = float(scene.get("camera_image_quality", float("nan")))
    quality_txt = _fmt(quality, "", "{:.3f}")
    smear_txt = _fmt(smear_px, " px", "{:.2f}")

    lat = float(scene.get("sat_subpoint_lat_deg", float("nan")))
    lon = float(scene.get("sat_subpoint_lon_deg", float("nan")))
    sub_txt = f"{lat:+.1f}/{lon:+.1f}\u00b0" if (np.isfinite(lat) and np.isfinite(lon)) else "n/a"
    alt_txt = _fmt(scene.get("sat_altitude_km", scene.get("orbit_altitude_km", float("nan"))), " km", "{:.1f}")
    theta_txt = _fmt(scene.get("theta_orbit_deg", float("nan")), "\u00b0", "{:+.1f}")

    intersection_pct = float(scene.get("target_intersection_pct", float("nan")))
    inview_txt = _fmt(intersection_pct, "%", "{:.0f}")

    lines = [
        "ORBIT",
        f"  alt {alt_txt}   sub {sub_txt}",
        f"  theta {theta_txt}   spin {scene['sat_body_rotation_rate_label']}",
        "ATTITUDE",
        f"  z off-nadir    {scene['z_angle_rel_nadir_deg']:+.1f}\u00b0",
        f"  LOS off-nadir  {scene['los_rel_nadir_deg']:+.1f}\u00b0",
        "CAMERA",
        f"  GSD {gsd_txt}   FOV {scene['camera_vfov_deg']:.2f}\u00b0",
        f"  swath {swath_txt}   smear {smear_txt}",
        f"  quality {quality_txt}   blocked {blocked_txt}",
        "TARGET",
        f"  in-view {inview_txt}",
        f"  center {scene['intersection_text']}",
    ]

    shutter_txt = str(scene.get("baseline_shutter_text", "")).strip()
    target_txt = str(scene.get("baseline_target_text", "")).strip()
    latent_txt = str(scene.get("baseline_latent_reward_text", "")).strip()
    if shutter_txt or target_txt or latent_txt:
        lines.append("MISSION")
        if target_txt:
            lines.append(f"  {target_txt}")
        if shutter_txt:
            lines.append(f"  {shutter_txt}")
        if latent_txt:
            lines.append(f"  {latent_txt}")

    lines.append("PLAYBACK")
    lines.append(f"  {scene['sim_speed_multiplier']:.0f}x   frame {scene['sim_idx']}")

    artists["text"].set_text("\n".join(lines))
