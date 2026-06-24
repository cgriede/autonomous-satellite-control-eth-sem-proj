import json
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import RENDER
from environment_definition.constants import OBSERVATION_LINE_NOT_COMPUTED

_DEBUG_CAM_ORIENTATION_LOG = Path(__file__).resolve().parents[2] / "debug-b36892.log"
_DEBUG_CAM_ORIENTATION_LOGGED = False


def _rgba_for_observation_line_code(code: int) -> np.ndarray:
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

    # Vertical strip: one row per cross-track bin (90° CW from legacy horizontal layout).
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


def update_1d_sat_view(artists: dict, observation_line_codes: np.ndarray) -> None:
    codes = np.asarray(observation_line_codes, dtype=np.int8)
    w_strip = int(artists["W"])
    n_bins = int(artists["N_BINS"])
    if codes.shape[0] != n_bins:
        raise ValueError("observation_line_codes length does not match sat-view bin count.")

    col = np.empty((n_bins, 4), dtype=float)
    for j in range(n_bins):
        col[j, :] = _rgba_for_observation_line_code(int(codes[j]))
    img = np.tile(col[:, np.newaxis, :], (1, w_strip, 1))
    artists["img"].set_data(img)

    global _DEBUG_CAM_ORIENTATION_LOGGED
    if not _DEBUG_CAM_ORIENTATION_LOGGED:
        _DEBUG_CAM_ORIENTATION_LOGGED = True
        ax = artists["img"].axes
        ylo, yhi = ax.get_ylim()
        extent = artists["img"].get_extent()
        origin = "upper"
        row0_at_visual_top = bool(origin == "upper" and ylo < yhi)
  #region agent log
        payload = {
            "sessionId": "b36892",
            "runId": "cam-orientation",
            "hypothesisId": "A",
            "location": "_satellite_cam_view.py:update_1d_sat_view",
            "message": "camera strip bin orientation",
            "data": {
                "n_bins": int(n_bins),
                "ylim": [float(ylo), float(yhi)],
                "imshow_extent": [float(v) for v in extent],
                "imshow_origin": origin,
                "row0_at_visual_top": row0_at_visual_top,
                "code_bin0": int(codes[0]),
                "code_bin_last": int(codes[-1]),
            },
            "timestamp": int(time.time() * 1000),
        }
        try:
            with _DEBUG_CAM_ORIENTATION_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except OSError:
            pass
  #endregion
