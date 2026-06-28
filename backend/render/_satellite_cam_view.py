import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import OBSERVATION_LINE_NOT_COMPUTED, RENDER
from environment_definition.constants.observation_codes import (
    is_observation_target_code,
    target_index_from_observation_code,
)


def _rgba_for_observation_line_code(
    code: int,
    *,
    captured_target_indices: frozenset[int] | set[int] | None = None,
) -> np.ndarray:
    c = int(code)
    if c == int(OBSERVATION_LINE_NOT_COMPUTED):
        return np.array([0.28, 0.28, 0.32, 1.0], dtype=float)
    if c == 0:
        return np.array([0.04, 0.06, 0.12, 1.0], dtype=float)
    if c == 1:
        return np.array([*RENDER.earth_green_rgb, 1.0], dtype=float)
    if c == 2:
        return np.array([0.78, 0.78, 0.80, 1.0], dtype=float)
    if is_observation_target_code(c):
        idx = target_index_from_observation_code(c)
        captured = captured_target_indices or frozenset()
        if idx is not None and idx in captured:
            return np.array([*RENDER.target_captured_cam_rgb, 1.0], dtype=float)
        return np.array([*RENDER.target_pending_cam_rgb, 1.0], dtype=float)
    return np.array([0.5, 0.0, 0.5, 1.0], dtype=float)


def build_1d_sat_view(
    fig: plt.Figure,
    scene: dict,
    *,
    axes_rect: tuple | None = None,
    n_bins_override: int | None = None,
    title: str = "Primary Camera",
) -> tuple[dict, dict]:
    l, b, w, h = axes_rect if axes_rect is not None else RENDER.sat_view_1d_axes_rect
    title_frac = 0.26
    h_title = h * title_frac
    h_strip = h * (1.0 - title_frac)

    ax_title = fig.add_axes([l, b + h_strip, w, h_title])
    ax_strip = fig.add_axes([l, b, w, h_strip])

    axes = {"1d_sat_view": ax_strip, "1d_sat_view_title": ax_title}
    artists: dict = {}

    n_bins = n_bins_override if n_bins_override is not None else int(scene["n_bins"])
    w_pix = 24
    artists["W"] = w_pix
    artists["N_BINS"] = n_bins

    img = np.zeros((n_bins, w_pix, 4), dtype=float)
    artists["img"] = ax_strip.imshow(
        img,
        extent=(0, 1, 0, n_bins),
        origin="upper",
        interpolation="none",
        aspect="auto",
        zorder=1,
    )

    ax_strip.set_facecolor(RENDER.space_background)
    ax_strip.set_xlim(0, 1)
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
        title,
        transform=ax_title.transAxes,
        color="white",
        fontsize=9,
        fontweight="bold",
        ha="center",
        va="center",
    )

    return axes, artists


def update_1d_sat_view(
    artists: dict,
    observation_line_codes: np.ndarray,
    *,
    captured_target_indices: frozenset[int] | set[int] | None = None,
) -> None:
    codes = np.asarray(observation_line_codes, dtype=np.int8)
    w_strip = int(artists["W"])
    n_bins = int(artists["N_BINS"])
    if codes.shape[0] != n_bins:
        raise ValueError("observation_line_codes length does not match sat-view bin count.")

    captured = frozenset(captured_target_indices) if captured_target_indices is not None else frozenset()
    col = np.empty((n_bins, 4), dtype=float)
    for j in range(n_bins):
        col[j, :] = _rgba_for_observation_line_code(int(codes[j]), captured_target_indices=captured)
    img = np.tile(col[:, np.newaxis, :], (1, w_strip, 1))
    artists["img"].set_data(img)
