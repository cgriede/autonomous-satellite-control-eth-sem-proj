"""Shared orbit-plane axis framing for main and closeup panels."""

from __future__ import annotations

import numpy as np

from environment_definition.constants import RENDER, ureg


def main_panel_axis_limits(scene: dict) -> tuple[float, float, float, float]:
    """World-km ``(x0, x1, y0, y1)`` limits used by the main orbit cross-section panel."""
    R_earth = float(scene["R_earth"])
    R_orbit = float(scene["R_orbit"])
    theta_center = float(scene["theta_center"])
    start_angle_deg = float(scene["start_angle_deg"])
    end_angle_deg = float(scene["end_angle_deg"])

    theta_window = np.linspace(
        theta_center + np.deg2rad(start_angle_deg),
        theta_center + np.deg2rad(end_angle_deg),
        721,
    )
    x_render = R_orbit * np.cos(theta_window)
    y_render = R_orbit * np.sin(theta_window)
    x_min_orbit = float(np.min(x_render))
    x_max_orbit = float(np.max(x_render))
    x_min_earth = float(np.clip(x_min_orbit, -R_earth, R_earth))
    x_max_earth = float(np.clip(x_max_orbit, -R_earth, R_earth))
    earth_cap_y_min = min(
        np.sqrt(max(R_earth**2 - x_min_earth**2, 0.0)),
        np.sqrt(max(R_earth**2 - x_max_earth**2, 0.0)),
    )
    zoom_pad_x = RENDER.zoom_pad_x.to(ureg.km).magnitude
    zoom_pad_y_bottom = RENDER.zoom_pad_y_bottom.to(ureg.km).magnitude
    zoom_pad_y_top = RENDER.zoom_pad_y_top.to(ureg.km).magnitude

    x0 = x_min_orbit - zoom_pad_x
    x1 = x_max_orbit + zoom_pad_x
    y0 = earth_cap_y_min - zoom_pad_y_bottom
    y1 = float(np.max(y_render)) + zoom_pad_y_top
    return x0, x1, y0, y1
