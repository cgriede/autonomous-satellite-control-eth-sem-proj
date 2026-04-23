import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import RENDER
from simulation.observation_line_constants import (
    FIXED_GROUND_CONE_HIT_EARTH,
    OBSERVATION_LINE_NOT_COMPUTED,
)


def _rgba_for_fixed_ground_code(code: int) -> np.ndarray:
    c = int(code)
    if c == int(OBSERVATION_LINE_NOT_COMPUTED):
        return np.array([0.28, 0.28, 0.32, 1.0], dtype=float)
    if c == 0:
        return np.array([0.04, 0.06, 0.12, 1.0], dtype=float)
    if c == 1:
        return np.array([*RENDER.earth_green_rgb, 1.0], dtype=float)
    if c == 2:
        return np.array([0.78, 0.78, 0.80, 1.0], dtype=float)
    if c == 3:
        return np.array([0.95, 0.15, 0.12, 1.0], dtype=float)
    if c == int(FIXED_GROUND_CONE_HIT_EARTH):
        return np.array([0.05, 0.95, 0.95, 1.0], dtype=float)
    return np.array([0.5, 0.0, 0.5, 1.0], dtype=float)


def build_1d_fixed_bird_view(fig: plt.Figure, scene: dict) -> tuple[dict, dict]:
    l, b, w, h = RENDER.fixed_bird_view_axes_rect
    title_frac = 0.26
    h_title = h * title_frac
    h_strip = h * (1.0 - title_frac)

    ax_title = fig.add_axes([l, b + h_strip, w, h_title])
    ax_strip = fig.add_axes([l, b, w, h_strip])

    axes = {"fixed_bird": ax_strip, "fixed_bird_title": ax_title}
    artists: dict = {}

    n_bins = int(scene["n_bins"])
    half_extent_km = float(RENDER.fixed_bird_view_half_extent_km.to("km").magnitude)
    h_pix = 24
    artists["H"] = h_pix
    artists["N_BINS"] = n_bins
    artists["fixed_half_extent_km"] = half_extent_km
    artists["obs_x_km"] = 0.0

    img = np.zeros((h_pix, n_bins, 4), dtype=float)
    artists["img"] = ax_strip.imshow(
        img,
        extent=(-half_extent_km, half_extent_km, 0, 1),
        origin="lower",
        interpolation="none",
        aspect="auto",
        zorder=1,
    )

    # Observer marker is always visible; color is updated by policy in updater.
    obs_x_km = float(artists["obs_x_km"])
    (artists["observer_line"],) = ax_strip.plot(
        [obs_x_km, obs_x_km],
        [0.0, 1.0],
        color="red",
        linewidth=1.8,
        zorder=3,
    )

    ax_strip.set_facecolor(RENDER.space_background)
    ax_strip.set_xlim(-half_extent_km, half_extent_km)
    ax_strip.set_ylim(0, 1)
    ax_strip.set_xticks([])
    ax_strip.set_yticks([])
    ax_strip.set_frame_on(False)

    ax_title.set_facecolor("black")
    ax_title.set_xticks([])
    ax_title.set_yticks([])
    ax_title.set_frame_on(False)
    artists["title_text"] = ax_title.text(
        0.5,
        0.5,
        "1d_fixed_bird_view",
        transform=ax_title.transAxes,
        color="white",
        fontsize=9,
        fontweight="bold",
        ha="center",
        va="center",
    )

    return axes, artists


def update_1d_fixed_bird_view(
    artists: dict,
    fixed_ground_line_codes: np.ndarray,
    observer_cloud_covered: bool,
) -> None:
    codes = np.asarray(fixed_ground_line_codes, dtype=np.int8)
    h_strip = int(artists["H"])
    n_bins = int(artists["N_BINS"])
    if codes.shape[0] != n_bins:
        raise ValueError("fixed_ground_line_codes length does not match fixed-bird bin count.")

    row = np.empty((n_bins, 4), dtype=float)
    for j in range(n_bins):
        row[j, :] = _rgba_for_fixed_ground_code(int(codes[j]))
    img = np.tile(row[np.newaxis, :, :], (h_strip, 1, 1))
    artists["img"].set_data(img)

    artists["observer_line"].set_color("orange" if observer_cloud_covered else "red")
