"""Static orbit-plane cross-section layers shared by main and closeup panels."""

from __future__ import annotations

import importlib

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import Circle

from environment_definition.constants import RENDER

_ISLAND_BLOB_ATTRS = (
    "island_blob_along_scale",
    "island_blob_along_pad_km",
    "island_blob_inward_sigma_km",
    "island_blob_inward_peak_km",
)


def _resolve_render_constants():
    """Return live ``RENDER``; reload constants module if a long-lived kernel cached a stale instance."""
    rc = RENDER
    missing = [name for name in _ISLAND_BLOB_ATTRS if not hasattr(rc, name)]
    if not missing:
        return rc
    render_constants_mod = importlib.import_module("environment_definition.constants.RENDER")
    importlib.reload(render_constants_mod)
    return render_constants_mod.RENDER


def _shaded_sphere_rgb(
    earth_x: np.ndarray,
    earth_y: np.ndarray,
    *,
    R_earth: float,
    dark_rgb: tuple[float, float, float],
    bright_rgb: tuple[float, float, float],
) -> np.ndarray:
    earth_r2 = (earth_x / R_earth) ** 2 + (earth_y / R_earth) ** 2
    earth_z = np.sqrt(np.clip(1.0 - earth_r2, 0.0, 1.0))
    light_dir = np.array(RENDER.light_dir, dtype=float)
    light_dir = light_dir / np.linalg.norm(light_dir)
    intensity = np.clip(
        earth_x / R_earth * light_dir[0]
        + earth_y / R_earth * light_dir[1]
        + earth_z * light_dir[2],
        0.0,
        1.0,
    )
    dark = np.array(dark_rgb, dtype=float)
    bright = np.array(bright_rgb, dtype=float)
    return dark + intensity[..., None] * (bright - dark)


def _island_blob_weight(
    earth_x: np.ndarray,
    earth_y: np.ndarray,
    *,
    R_earth: float,
    earth_mask: np.ndarray,
    island_phi_bounds_deg: list[tuple[float, float]],
    island_blob_center_xy_km: tuple[float, float],
) -> np.ndarray:
    """Soft elliptical land blob aligned with the mission anchor on the Earth rim."""
    rc = _resolve_render_constants()
    cx, cy = (float(island_blob_center_xy_km[0]), float(island_blob_center_xy_km[1]))
    rim_radius_km = float(np.hypot(cx, cy))
    if rim_radius_km <= 0.0:
        return np.zeros_like(earth_x, dtype=float)

    cos_t = cx / rim_radius_km
    sin_t = cy / rim_radius_km
    dx = earth_x - cx
    dy = earth_y - cy
    # Tangent (along-track) and inward (cross-track) km from the anchor on the rim.
    along_km = -dx * sin_t + dy * cos_t
    inward_km = -dx * cos_t - dy * sin_t

    phi_lo = min(lo for lo, _ in island_phi_bounds_deg)
    phi_hi = max(hi for _, hi in island_phi_bounds_deg)
    span_deg = max(float(phi_hi - phi_lo), 1.0)
    sigma_along_km = (
        R_earth * np.deg2rad(span_deg) * float(rc.island_blob_along_scale)
        + float(rc.island_blob_along_pad_km)
    )
    sigma_inward_km = float(rc.island_blob_inward_sigma_km)
    peak_inward_km = float(rc.island_blob_inward_peak_km)

    along_weight = np.exp(-0.5 * (along_km / max(sigma_along_km, 1.0)) ** 2)
    inward_weight = np.exp(-0.5 * ((inward_km - peak_inward_km) / max(sigma_inward_km, 1.0)) ** 2)

    earth_r2 = (earth_x / R_earth) ** 2 + (earth_y / R_earth) ** 2
    r_norm = np.sqrt(np.clip(earth_r2, 0.0, 1.0))
    rim_weight = np.clip(
        (r_norm - float(rc.island_r_min_frac)) / float(rc.island_r_feather_frac),
        0.0,
        1.0,
    )
    y_norm = earth_y / R_earth
    cap_weight = np.clip(
        (y_norm - float(rc.island_y_min_frac)) / float(rc.island_y_feather_frac),
        0.0,
        1.0,
    )

    return along_weight * inward_weight * rim_weight * cap_weight * earth_mask.astype(float)


def draw_star_field(ax: Axes) -> None:
    star_rng = np.random.default_rng(RENDER.star_rng_seed)
    num_stars = RENDER.num_stars
    star_x = star_rng.uniform(ax.get_xlim()[0], ax.get_xlim()[1], num_stars)
    star_y = star_rng.uniform(ax.get_ylim()[0], ax.get_ylim()[1], num_stars)
    star_sizes = star_rng.uniform(RENDER.star_size_min, RENDER.star_size_max, num_stars)
    star_alpha = star_rng.uniform(RENDER.star_alpha_min, RENDER.star_alpha_max, num_stars)
    star_colors = np.ones((num_stars, 4))
    star_colors[:, :3] = RENDER.star_color_rgb
    star_colors[:, 3] = star_alpha
    ax.scatter(
        star_x,
        star_y,
        s=star_sizes,
        c=star_colors,
        linewidths=0,
        zorder=RENDER.zorder_stars,
    )


def draw_shaded_earth_disk(
    ax: Axes,
    R_earth: float,
    *,
    island_phi_bounds_deg: list[tuple[float, float]] | None = None,
    island_blob_center_xy_km: tuple[float, float] | None = None,
) -> None:
    earth_res = RENDER.earth_res
    earth_x = np.linspace(-R_earth, R_earth, earth_res)
    earth_y = np.linspace(-R_earth, R_earth, earth_res)
    earth_X, earth_Y = np.meshgrid(earth_x, earth_y)
    earth_r2 = (earth_X / R_earth) ** 2 + (earth_Y / R_earth) ** 2
    earth_mask = earth_r2 <= 1.0

    ocean_rgb = _shaded_sphere_rgb(
        earth_X,
        earth_Y,
        R_earth=R_earth,
        dark_rgb=RENDER.earth_dark_rgb,
        bright_rgb=RENDER.earth_bright_rgb,
    )
    earth_rgb = ocean_rgb.copy()

    if island_phi_bounds_deg and island_blob_center_xy_km is not None:
        island_weight = _island_blob_weight(
            earth_X,
            earth_Y,
            R_earth=R_earth,
            earth_mask=earth_mask,
            island_phi_bounds_deg=island_phi_bounds_deg,
            island_blob_center_xy_km=island_blob_center_xy_km,
        )
        if np.any(island_weight > 0.0):
            island_rgb = _shaded_sphere_rgb(
                earth_X,
                earth_Y,
                R_earth=R_earth,
                dark_rgb=RENDER.island_dark_rgb,
                bright_rgb=RENDER.island_bright_rgb,
            )
            w = island_weight[..., None]
            earth_rgb = ocean_rgb * (1.0 - w) + island_rgb * w

    earth_alpha = earth_mask.astype(float)
    earth_rgba = np.dstack((earth_rgb, earth_alpha))
    ax.imshow(
        earth_rgba,
        extent=(-R_earth, R_earth, -R_earth, R_earth),
        origin="lower",
        interpolation="bilinear",
        zorder=RENDER.zorder_earth,
    )
    ax.add_patch(
        Circle(
            (0, 0),
            R_earth,
            fill=False,
            edgecolor=RENDER.earth_outline_color,
            linewidth=RENDER.earth_outline_linewidth,
            alpha=RENDER.earth_outline_alpha,
            zorder=RENDER.zorder_earth_outline,
        )
    )
