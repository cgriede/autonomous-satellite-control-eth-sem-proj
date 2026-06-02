"""One-off repro for notebook main-frame layout (debug session 78ee2f)."""
import json
import sys
import time
from pathlib import Path

backend_root = Path(__file__).resolve().parents[1]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

import matplotlib.pyplot as plt
import numpy as np

from environment_definition.constants import EARTH_RADIUS, RENDER, SIMULATION
from environment_definition.constants.MISSION import los_theta_offsets_deg
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE_ALTITUDE
from render._main_view import build_main_panel
from utils.geometry.mission_stripe_disk import geodetic_on_lon_meridian_to_disk_polar_deg

_LOG = Path(__file__).resolve().parents[2] / "debug-78ee2f.log"


def _log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    payload = {
        "sessionId": "78ee2f",
        "runId": "repro-script",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    with _LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def main() -> None:
    r_earth_km = float(EARTH_RADIUS.to("km").magnitude)
    r_orbit_km = r_earth_km + float(SATELLITE_ALTITUDE.to("km").magnitude)
    theta_center_rad = float(SIMULATION.theta_center.to("rad").magnitude)
    theta_center_deg = float(SIMULATION.theta_center.to("deg").magnitude)
    margin_deg = float(SIMULATION.contact_margin_angle.to("deg").magnitude)
    los_lo_deg, los_hi_deg = los_theta_offsets_deg(
        orbit_height=SATELLITE_ALTITUDE,
        margin_deg=margin_deg,
    )
    frame_lo_deg = min(los_lo_deg, los_hi_deg)
    frame_hi_deg = max(los_lo_deg, los_hi_deg)
    overall_phi_lo_deg = 60.0
    overall_phi_hi_deg = 120.0
    mid_lat_deg = 45.0
    view_anchor_phi_deg = geodetic_on_lon_meridian_to_disk_polar_deg(lat_deg=mid_lat_deg, lon_deg=0.0)
    view_anchor_x = r_earth_km * np.cos(np.deg2rad(view_anchor_phi_deg))
    view_anchor_y = r_earth_km * np.sin(np.deg2rad(view_anchor_phi_deg))
    scene = {
        "R_earth": r_earth_km,
        "R_orbit": r_orbit_km,
        "theta_center": theta_center_rad,
        "start_angle_deg": frame_lo_deg,
        "end_angle_deg": frame_hi_deg,
        "target_region_start_angle_deg": overall_phi_lo_deg,
        "target_region_end_angle_deg": overall_phi_hi_deg,
        "target_region_bounds_deg": [(overall_phi_lo_deg, overall_phi_hi_deg)],
        "view_anchor_x": float(view_anchor_x),
        "view_anchor_y": float(view_anchor_y),
        "view_anchor_pos": np.asarray([view_anchor_x, view_anchor_y], dtype=float),
        "cloud_models": [],
        "n_clouds": 0,
        "n_bins": 0,
        "n_bins_secondary": 0,
        "controller_mode": "static-target-grid",
    }

    margin_l, margin_b, margin_w, title_frac = 0.06, 0.10, 0.9, 0.08
    usable_h_frac = 1.0 - margin_b - title_frac
    fig_w = 9.5

    fig = plt.figure(figsize=(fig_w, 6.5), facecolor=RENDER.space_background)
    axes, artists = build_main_panel(fig, scene)
    ax = axes["main"]
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    data_aspect = (xlim[1] - xlim[0]) / (ylim[1] - ylim[0])
    fig_h = (margin_w * fig_w) / data_aspect / usable_h_frac
    fig.set_size_inches(fig_w, fig_h)
  #region agent log
    _log(
        "A",
        "debug_main_frame_layout.py:after_build",
        "axes after build_main_panel",
        {
            "main_axes_rect": list(RENDER.main_axes_rect),
            "position": list(ax.get_position().bounds),
            "xlim": list(ax.get_xlim()),
            "ylim": list(ax.get_ylim()),
            "aspect": str(ax.get_aspect()),
            "adjustable": ax.get_adjustable(),
        },
    )
  #endregion

    fig_w, fig_h = fig.get_size_inches()
    h_frac = (margin_w * fig_w) / data_aspect / fig_h
    ax.set_position([margin_l, margin_b, margin_w, h_frac])
    ax.set_aspect("equal", adjustable="box")
  #region agent log
    _log(
        "B",
        "debug_main_frame_layout.py:after_set_position",
        "axes after aspect-fitted set_position",
        {
            "requested_h_frac": h_frac,
            "data_aspect": data_aspect,
            "position": list(ax.get_position().bounds),
        },
    )
  #endregion

    fig.suptitle("Static render-style target overview", color="white", fontsize=14)
  #region agent log
    _log(
        "F",
        "debug_main_frame_layout.py:after_suptitle",
        "axes after suptitle",
        {"position": list(ax.get_position().bounds), "figsize_in": list(fig.get_size_inches())},
    )
  #endregion

    z_lbl = artists["z_axis_label"]
    fig.canvas.draw()
  #region agent log
    _log(
        "D",
        "debug_main_frame_layout.py:z_label",
        "z_axis_label state",
        {
            "visible": z_lbl.get_visible(),
            "position_data": list(z_lbl.get_position()),
            "text": z_lbl.get_text(),
            "color": z_lbl.get_color(),
            "window_extent": list(z_lbl.get_window_extent(fig.canvas.get_renderer()).bounds),
        },
    )
  #endregion

    tight = fig.get_tightbbox(fig.canvas.get_renderer())
  #region agent log
    _log(
        "E",
        "debug_main_frame_layout.py:tightbbox",
        "figure tight bbox (display coords)",
        {"tightbbox": list(tight.bounds), "fig_bbox": list(fig.bbox.bounds)},
    )
  #endregion

    out = Path(__file__).resolve().parents[2] / "debug-main-frame.png"
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)
    _log("E", "debug_main_frame_layout.py:done", "saved figure", {"path": str(out)})


if __name__ == "__main__":
    main()
