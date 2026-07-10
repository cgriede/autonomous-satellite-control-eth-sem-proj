#!/usr/bin/env python3
"""Render calibration previews from the current earth_photo_calibration.json."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BACKEND = _REPO_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from environment_definition.constants import EARTH_RADIUS, RENDER, ureg
from environment_definition.constants.MISSION import los_theta_offsets_deg
from environment_definition.constants import SIMULATION
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE_ALTITUDE
from render._earth_frame import main_panel_axis_limits
from render._earth_photo import draw_orbit_plane_earth

OUT_PATH = _REPO_ROOT / "data" / "earth_image" / "preview_main_view.png"
LOG_PATH = _REPO_ROOT / "data" / "earth_image" / "preview_main_view.log"


def _sample_main_scene() -> dict:
    R_earth = float(EARTH_RADIUS.to(ureg.km).magnitude)
    sat_alt = float(SATELLITE_ALTITUDE.to(ureg.km).magnitude)
    margin_deg = float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude)
    start_angle_deg, end_angle_deg = los_theta_offsets_deg(
        orbit_height=SATELLITE_ALTITUDE,
        margin_deg=margin_deg,
    )
    return {
        "R_earth": R_earth,
        "R_orbit": R_earth + sat_alt,
        "theta_center": float(SIMULATION.theta_center.to(ureg.rad).magnitude),
        "start_angle_deg": float(start_angle_deg),
        "end_angle_deg": float(end_angle_deg),
        "cloud_models": [],
        "target_region_start_angle_deg": 89.65,
        "target_region_end_angle_deg": 90.0,
    }


def main() -> None:
    scene = _sample_main_scene()
    R_earth = float(scene["R_earth"])
    x0, x1, y0, y1 = main_panel_axis_limits(scene)

    fig, ax = plt.subplots(figsize=(12, 7), facecolor="black")
    ax.set_facecolor(RENDER.space_background)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    draw_orbit_plane_earth(ax, R_earth)
    ax.set_title(
        "Earth photo calibration preview (thin blue crust = alignment check)",
        color="white",
        fontsize=11,
        pad=8,
    )
    fig.tight_layout()
    fig.savefig(OUT_PATH, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)

    lines = [
        "preview: ok",
        f"output: {OUT_PATH}",
        f"frame km: x=[{x0:.1f},{x1:.1f}] y=[{y0:.1f},{y1:.1f}]",
    ]
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
