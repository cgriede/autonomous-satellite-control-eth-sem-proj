#!/usr/bin/env python3
"""Calibrate the Earth photo to the main orbit-plane panel frame."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "backend"))

from environment_definition.constants import EARTH_RADIUS, RENDER, ureg
from environment_definition.constants.MISSION import los_theta_offsets_deg
from environment_definition.constants import SIMULATION
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE_ALTITUDE
from render._earth_frame import main_panel_axis_limits
from render._earth_image_calibration import (
    DEFAULT_SOURCE,
    detect_earth_disk,
    load_source_rgba,
    sample_photo_world_window,
    write_calibration_json,
)

OUT_DIR = _REPO_ROOT / "data" / "earth_image"
CALIB_PATH = OUT_DIR / "earth_photo_calibration.json"
MAIN_CROP_PATH = OUT_DIR / "main_view_background.png"
ALIGNMENT_PATH = OUT_DIR / "preview_alignment_check.png"


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


def _save_alignment_check(
    *,
    rgba: np.ndarray,
    fit,
    R_earth: float,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cropped = sample_photo_world_window(
        rgba,
        R_earth_km=R_earth,
        x0=x0,
        x1=x1,
        y0=y0,
        y1=y1,
        center_x=fit.center_x,
        center_y=fit.center_y,
        radius_px=fit.radius,
        out_width_px=1600,
    )
    fig, ax = plt.subplots(figsize=(12, 4), facecolor="black")
    ax.imshow(cropped, extent=(x0, x1, y0, y1), origin="lower")
    xs_arc = np.linspace(-R_earth, R_earth, 400)
    ys_arc = np.sqrt(np.maximum(R_earth**2 - xs_arc**2, 0.0))
    valid = (ys_arc >= y0) & (ys_arc <= min(y1, R_earth))
    ax.plot(xs_arc[valid], ys_arc[valid], color="#00e5ff", linewidth=1.0, label="sim limb")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Alignment check: cyan = simulated limb on photo", color="white", fontsize=10)
    fig.tight_layout()
    fig.savefig(ALIGNMENT_PATH, dpi=150, facecolor="black")
    plt.close(fig)


def main() -> None:
    source_path = OUT_DIR / DEFAULT_SOURCE
    if not source_path.is_file():
        raise FileNotFoundError(f"Missing source image: {source_path}")

    rgba = load_source_rgba(source_path)
    coarse = detect_earth_disk(rgba)
    scene = _sample_main_scene()
    x0, x1, y0, y1 = main_panel_axis_limits(scene)
    R_earth = float(scene["R_earth"])
    fit = coarse

    cropped = sample_photo_world_window(
        rgba,
        R_earth_km=R_earth,
        x0=x0,
        x1=x1,
        y0=y0,
        y1=y1,
        center_x=fit.center_x,
        center_y=fit.center_y,
        radius_px=fit.radius,
        out_width_px=int(RENDER.earth_photo_render_width_px),
    )
    Image.fromarray(cropped).save(MAIN_CROP_PATH)
    write_calibration_json(
        CALIB_PATH,
        source_image=DEFAULT_SOURCE,
        rgba=rgba,
        fit=fit,
        main_view_world_km={
            "x0": round(x0, 3),
            "x1": round(x1, 3),
            "y0": round(y0, 3),
            "y1": round(y1, 3),
        },
    )
    _save_alignment_check(
        rgba=rgba,
        fit=fit,
        R_earth=R_earth,
        x0=x0,
        x1=x1,
        y0=y0,
        y1=y1,
    )

    print(f"Wrote calibration: {CALIB_PATH}")
    print(f"Wrote main-view crop: {MAIN_CROP_PATH}")
    print(f"Wrote alignment check: {ALIGNMENT_PATH}")
    print(f"Disk center px=({fit.center_x:.1f}, {fit.center_y:.1f}) radius={fit.radius:.1f}")
    print(f"Main frame km: x=[{x0:.1f}, {x1:.1f}] y=[{y0:.1f}, {y1:.1f}]")


if __name__ == "__main__":
    main()
