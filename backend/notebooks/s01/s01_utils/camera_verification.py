"""Notebook verification helpers for dual-camera mount + observation-line checks."""

from __future__ import annotations

from typing import Any

from s01_utils.cloud_verification import show_static_panels_from_series


def show_dual_camera_mount_panels(series: Any, *, frame_idx: int = 0) -> None:
    """Main + closeup render panels from canonical ``SimulationStateSeries``.

    Primary nadir cone: filled (``RENDER.cone_color``). Secondary forward cone: gold dashed.
    """
    show_static_panels_from_series(series, frame_idx=frame_idx)


def print_dual_camera_numeric_gate(series: Any) -> None:
    """Stdout checks that complement the visual MP4 / static panels."""
    sec_bins = int(series.secondary_camera_observation_line_codes.shape[1])
    pri_bins = int(series.camera_observation_line_codes.shape[1])
    sec_tilt_deg = float(series.secondary_camera_tilt_off_nadir_rad) * 180.0 / 3.141592653589793
    sec_vfov_deg = float(series.secondary_camera_vertical_fov_rad) * 180.0 / 3.141592653589793
    print("Dual-camera numeric gate")
    print(f"  primary observation-line bins:   {pri_bins}")
    print(f"  secondary observation-line bins: {sec_bins}")
    print(f"  secondary tilt off nadir:        {sec_tilt_deg:.2f} deg (expect 25)")
    print(f"  secondary sim vertical FOV:      {sec_vfov_deg:.2f} deg (expect 70)")
    if sec_bins <= 0:
        raise RuntimeError("secondary camera observation line has zero bins")
