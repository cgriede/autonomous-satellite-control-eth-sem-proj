"""
Pinhole camera optics helpers (GSD, FOV). Used by camera_2d, SIMULATION config, and render.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from environment_definition.constants.UNIT_REGISTRY import UREG as ureg


def pinhole_full_fov_rad(*, sensor_dim: Any, focal_length: Any) -> Any:
    """
    Full field-of-view opening angle for one sensor dimension:

        FOV = 2 * arctan((sensor_dim/2) / focal_length)

    Returns a Pint angle quantity in radians.
    """
    ratio_dimless = (sensor_dim / (2.0 * focal_length)).to_base_units().magnitude
    return (2.0 * np.arctan(ratio_dimless)) * ureg.rad


def nadir_ground_sample_distance(*, pixel_size: Any, altitude: Any, focal_length: Any) -> Any:
    """
    Ground sample distance at nadir:

        GSD = (pixel_size * altitude) / focal_length

    Returns a Pint length quantity in meters.
    """
    return (pixel_size * altitude / focal_length).to(ureg.m)
