"""Static orbit-plane cross-section layers shared by main and closeup panels."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import Circle

from environment_definition.constants import RENDER


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


def draw_shaded_earth_disk(ax: Axes, R_earth: float) -> None:
    earth_res = RENDER.earth_res
    earth_x = np.linspace(-R_earth, R_earth, earth_res)
    earth_y = np.linspace(-R_earth, R_earth, earth_res)
    earth_X, earth_Y = np.meshgrid(earth_x, earth_y)
    earth_r2 = (earth_X / R_earth) ** 2 + (earth_Y / R_earth) ** 2
    earth_mask = earth_r2 <= 1.0
    earth_Z = np.sqrt(np.clip(1.0 - earth_r2, 0.0, 1.0))
    light_dir = np.array(RENDER.light_dir)
    light_dir = light_dir / np.linalg.norm(light_dir)
    earth_intensity = np.clip(
        earth_X / R_earth * light_dir[0]
        + earth_Y / R_earth * light_dir[1]
        + earth_Z * light_dir[2],
        0.0,
        1.0,
    )
    earth_dark = np.array(RENDER.earth_dark_rgb)
    earth_bright = np.array(RENDER.earth_bright_rgb)
    earth_rgb = earth_dark + earth_intensity[..., None] * (earth_bright - earth_dark)
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
