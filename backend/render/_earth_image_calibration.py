"""Earth disk detection and photo-to-world calibration helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = "javier-miranda-AlJ9TQqeCV0-unsplash.jpg"


@dataclass(frozen=True)
class DiskFit:
    center_x: float
    center_y: float
    radius: float
    score: float


def load_source_rgba(path: Path) -> np.ndarray:
    with Image.open(path) as img:
        return np.asarray(img.convert("RGBA"), dtype=np.uint8)


def detect_earth_disk(rgba: np.ndarray) -> DiskFit:
    """Fit the visible Earth sphere from the lit-body bounding box."""
    rgb = rgba[..., :3].astype(np.float32)
    luminance = rgb.max(axis=2)
    earth_body = luminance > 14.0

    ys, xs = np.where(earth_body)
    if xs.size == 0:
        h, w = rgba.shape[:2]
        return DiskFit(w * 0.5, h * 0.52, min(w, h) * 0.46, 0.0)

    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    cx = 0.5 * (x0 + x1)
    cy = 0.5 * (y0 + y1)
    radius = 0.5 * min(x1 - x0, y1 - y0) * 1.015
    return DiskFit(float(cx), float(cy), float(radius), 0.0)


def world_to_source_xy(
    earth_x_km: np.ndarray,
    earth_y_km: np.ndarray,
    *,
    R_earth_km: float,
    center_x: float,
    center_y: float,
    radius_px: float,
    rotation_deg: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    scale = radius_px / R_earth_km
    theta = np.deg2rad(rotation_deg)
    cos_t = float(np.cos(theta))
    sin_t = float(np.sin(theta))
    wx = np.asarray(earth_x_km, dtype=float)
    wy = np.asarray(earth_y_km, dtype=float)
    rx = wx * cos_t - wy * sin_t
    ry = wx * sin_t + wy * cos_t
    src_x = center_x + rx * scale
    src_y = center_y - ry * scale
    return src_x, src_y


def sample_photo_world_window(
    rgba: np.ndarray,
    *,
    R_earth_km: float,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    center_x: float,
    center_y: float,
    radius_px: float,
    rotation_deg: float = 0.0,
    out_width_px: int = 1600,
    mask_outside_disk: bool = True,
    suppress_stars: bool = True,
) -> np.ndarray:
    """Resample the source photo into a world-km window."""
    out_h = max(32, int(round(out_width_px * (y1 - y0) / max(x1 - x0, 1.0))))
    grid_x = np.linspace(x0, x1, out_width_px, dtype=float)
    grid_y = np.linspace(y0, y1, out_h, dtype=float)
    earth_X, earth_Y = np.meshgrid(grid_x, grid_y)

    src_x, src_y = world_to_source_xy(
        earth_X,
        earth_Y,
        R_earth_km=R_earth_km,
        center_x=center_x,
        center_y=center_y,
        radius_px=radius_px,
        rotation_deg=rotation_deg,
    )

    h, w = rgba.shape[:2]
    x_f = np.clip(src_x, 0.0, w - 1.001)
    y_f = np.clip(src_y, 0.0, h - 1.001)
    x0i = np.floor(x_f).astype(int)
    y0i = np.floor(y_f).astype(int)
    x1i = np.clip(x0i + 1, 0, w - 1)
    y1i = np.clip(y0i + 1, 0, h - 1)
    tx = (x_f - x0i)[..., None]
    ty = (y_f - y0i)[..., None]

    c00 = rgba[y0i, x0i].astype(np.float32)
    c10 = rgba[y0i, x1i].astype(np.float32)
    c01 = rgba[y1i, x0i].astype(np.float32)
    c11 = rgba[y1i, x1i].astype(np.float32)
    out = (1 - tx) * (1 - ty) * c00 + tx * (1 - ty) * c10 + (1 - tx) * ty * c01 + tx * ty * c11

    earth_r2 = (earth_X / R_earth_km) ** 2 + (earth_Y / R_earth_km) ** 2
    inside = earth_r2 <= 1.0
    if mask_outside_disk or suppress_stars:
        out[~inside] = 0.0

    return np.clip(out, 0, 255).astype(np.uint8)


def fine_tune_radius_for_limb(
    rgba: np.ndarray,
    *,
    R_earth_km: float,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    initial: DiskFit,
) -> DiskFit:
    """Nudge radius so the simulated limb sits on the photo's outer silhouette."""
    rgb = rgba[..., :3].astype(np.float32)
    edge_score = rgb[..., :3].std(axis=2)

    xs = np.linspace(x0, x1, 320)
    ys = np.sqrt(np.maximum(R_earth_km**2 - xs**2, 0.0))
    valid = (ys >= y0) & (ys <= y1)
    xs = xs[valid]
    ys = ys[valid]
    if xs.size < 8:
        return initial

    best = initial
    best_metric = -np.inf
    for scale in np.linspace(1.000, 1.012, 13):
        radius = initial.radius * float(scale)
        src_x, src_y = world_to_source_xy(
            xs,
            ys,
            R_earth_km=R_earth_km,
            center_x=initial.center_x,
            center_y=initial.center_y,
            radius_px=radius,
        )
        xi = np.clip(np.round(src_x).astype(int), 0, rgba.shape[1] - 1)
        yi = np.clip(np.round(src_y).astype(int), 0, rgba.shape[0] - 1)
        metric = float(np.mean(edge_score[yi, xi]))
        if metric > best_metric:
            best_metric = metric
            best = DiskFit(initial.center_x, initial.center_y, radius, metric)
    return best


def write_calibration_json(
    path: Path,
    *,
    source_image: str,
    rgba: np.ndarray,
    fit: DiskFit,
    main_view_world_km: dict[str, float],
    rotation_deg: float = 0.0,
) -> None:
    img_w, img_h = rgba.shape[1], rgba.shape[0]
    payload = {
        "source_image": source_image,
        "image_width_px": img_w,
        "image_height_px": img_h,
        "disk_center_px": [round(fit.center_x, 2), round(fit.center_y, 2)],
        "disk_radius_px": round(fit.radius, 2),
        "disk_center_norm": [round(fit.center_x / img_w, 5), round(fit.center_y / img_h, 5)],
        "disk_radius_norm": round(fit.radius / min(img_w, img_h), 5),
        "rotation_deg": rotation_deg,
        "main_view_world_km": main_view_world_km,
        "main_view_crop_png": "main_view_background.png",
        "fit_score": round(float(fit.score), 4),
        "notes": (
            "rotation_deg=0 is the current perfect-day orientation. "
            "Re-run calibrate_earth_background.py after changing source photo."
        ),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
