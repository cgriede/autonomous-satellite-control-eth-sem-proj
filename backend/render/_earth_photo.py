"""Earth photo background aligned to the simulation orbit-plane disk frame."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import Circle

from environment_definition.constants import RENDER

from ._earth_image_calibration import sample_photo_world_window

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class EarthPhotoCalibration:
    source_image: str
    disk_center_px: tuple[float, float]
    disk_radius_px: float
    rotation_deg: float = 0.0

    @property
    def source_path(self) -> Path:
        return _REPO_ROOT / "data" / "earth_image" / self.source_image

    @classmethod
    def load(cls, path: Path | None = None) -> EarthPhotoCalibration:
        calib_path = path or (_REPO_ROOT / RENDER.earth_photo_calibration_path)
        payload = json.loads(calib_path.read_text(encoding="utf-8"))
        center = payload.get("disk_center_px")
        radius = payload.get("disk_radius_px")
        if center is None or radius is None:
            source = _REPO_ROOT / "data" / "earth_image" / str(payload["source_image"])
            from PIL import Image

            with Image.open(source) as img:
                img_w, img_h = img.size
            center_norm = payload.get("disk_center_norm", [0.5, 0.5])
            radius_norm = float(payload.get("disk_radius_norm", 0.46))
            center = [center_norm[0] * img_w, center_norm[1] * img_h]
            radius = radius_norm * min(img_w, img_h)
        return cls(
            source_image=str(payload["source_image"]),
            disk_center_px=(float(center[0]), float(center[1])),
            disk_radius_px=float(radius),
            rotation_deg=float(payload.get("rotation_deg", 0.0)),
        )


@lru_cache(maxsize=4)
def _load_source_rgba(path_str: str) -> np.ndarray:
    from PIL import Image

    with Image.open(path_str) as img:
        return np.asarray(img.convert("RGBA"), dtype=np.uint8)


def crop_world_window_rgba(
    calib: EarthPhotoCalibration,
    *,
    R_earth_km: float,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    out_width_px: int = 1600,
) -> np.ndarray:
    """Crop and resample the source photo to the axis-aligned world-km window."""
    source = _load_source_rgba(str(calib.source_path))
    cx, cy = calib.disk_center_px
    return sample_photo_world_window(
        source,
        R_earth_km=R_earth_km,
        x0=x0,
        x1=x1,
        y0=y0,
        y1=y1,
        center_x=cx,
        center_y=cy,
        radius_px=calib.disk_radius_px,
        rotation_deg=calib.rotation_deg,
        out_width_px=out_width_px,
        mask_outside_disk=True,
        suppress_stars=True,
    )


def draw_earth_photo_background(
    ax: Axes,
    R_earth_km: float,
    *,
    calib: EarthPhotoCalibration | None = None,
) -> None:
    """Draw the calibrated Earth photo mapped to current axis limits."""
    if calib is None:
        calib = EarthPhotoCalibration.load()
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    rgba = crop_world_window_rgba(
        calib,
        R_earth_km=R_earth_km,
        x0=float(x0),
        x1=float(x1),
        y0=float(y0),
        y1=float(y1),
        out_width_px=int(RENDER.earth_photo_render_width_px),
    )
    ax.imshow(
        rgba,
        extent=(x0, x1, y0, y1),
        origin="lower",
        interpolation="bilinear",
        zorder=RENDER.zorder_earth,
    )


def draw_earth_crust_outline(ax: Axes, R_earth_km: float) -> None:
    """Thin limb circle used to verify photo-to-disk alignment."""
    ax.add_patch(
        Circle(
            (0.0, 0.0),
            R_earth_km,
            fill=False,
            edgecolor=RENDER.earth_crust_color,
            linewidth=RENDER.earth_crust_linewidth,
            alpha=RENDER.earth_crust_alpha,
            zorder=RENDER.zorder_earth_outline,
        )
    )


def draw_orbit_plane_earth(
    ax: Axes,
    R_earth_km: float,
    *,
    use_photo: bool | None = None,
) -> None:
    """Earth background layer: photo + thin crust when enabled, else legacy shaded disk."""
    if use_photo is None:
        use_photo = bool(RENDER.earth_photo_enabled)
    if use_photo:
        draw_earth_photo_background(ax, R_earth_km)
        draw_earth_crust_outline(ax, R_earth_km)
        return
    from ._orbit_plane_static import draw_shaded_earth_disk

    draw_shaded_earth_disk(ax, R_earth_km)


def draw_orbit_plane_stars(ax: Axes) -> None:
    if RENDER.earth_photo_enabled and not RENDER.earth_photo_show_stars:
        return
    from ._orbit_plane_static import draw_star_field

    draw_star_field(ax)
