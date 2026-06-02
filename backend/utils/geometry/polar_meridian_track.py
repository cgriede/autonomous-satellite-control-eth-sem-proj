"""
Along-track target placement on the polar meridian (LON_GLOBAL), including pole crossing.

Geodesic ``vreckon`` northward saturates at the pole and can flip longitude, which shrinks
gaps and mirrors segments in the renderer. This module steps a monotonic **track offset**
``offset_deg = λ_deg − 90°`` before the pole and continues with positive offset past the pole
(orbit-disk angle ``φ_deg = θ_center + offset_deg`` keeps increasing).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from environment_definition.constants.EARTH import EARTH_RADIUS
from environment_definition.constants.MISSION import LON_GLOBAL, ObservationTargetArea
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.units.require_compatible_unit import require_compatible_units


def _lon_deg_for_track_offset_deg(offset_deg: float) -> float:
    lon_asc = float(LON_GLOBAL.to(ureg.deg).magnitude)
    if float(offset_deg) > 0.0:
        return lon_asc + 180.0 if lon_asc >= 0.0 else lon_asc - 180.0
    return lon_asc


def lat_deg_from_track_offset_deg(offset_deg: float) -> float:
    """Map along-track offset to geodetic latitude on the forward meridian sweep."""
    if offset_deg <= 0.0:
        return 90.0 + float(offset_deg)
    return 90.0 - float(offset_deg)


def track_offset_deg_from_anchor_lat_deg(anchor_lat_deg: float) -> float:
    return float(anchor_lat_deg) - 90.0


def _offset_step_deg(distance_m: float) -> float:
    r_m = float(EARTH_RADIUS.to(ureg.m).magnitude)
    return float(np.rad2deg(float(distance_m) / r_m))


def phi_deg_from_track_offset_deg(offset_deg: float, *, theta_center_deg: float = 90.0) -> float:
    return float(theta_center_deg) + float(offset_deg)


@dataclass(frozen=True)
class MeridianTargetSegment:
    lat_min: Any
    lat_max: Any
    label: str
    track_offset_lo_deg: float
    track_offset_hi_deg: float
    lon_min_deg: float | None = None
    lon_max_deg: float | None = None

    def endpoint_lon_deg(self, *, which: str) -> float:
        if which == "min":
            if self.lon_min_deg is not None:
                return float(self.lon_min_deg)
            return _lon_deg_for_track_offset_deg(self.track_offset_lo_deg)
        if which == "max":
            if self.lon_max_deg is not None:
                return float(self.lon_max_deg)
            return _lon_deg_for_track_offset_deg(self.track_offset_hi_deg)
        raise ValueError("which must be 'min' or 'max'.")

    def to_observation_target_area(self) -> ObservationTargetArea:
        lon_lo = self.endpoint_lon_deg(which="min")
        lon_hi = self.endpoint_lon_deg(which="max")
        return ObservationTargetArea(
            lat_min=self.lat_min,
            lat_max=self.lat_max,
            label=self.label,
            lat_min_lon=lon_lo * ureg.deg,
            lat_max_lon=lon_hi * ureg.deg,
        )

    def phi_bounds_deg(self, *, theta_center_deg: float = 90.0) -> tuple[float, float]:
        phi_lo = phi_deg_from_track_offset_deg(self.track_offset_lo_deg, theta_center_deg=theta_center_deg)
        phi_hi = phi_deg_from_track_offset_deg(self.track_offset_hi_deg, theta_center_deg=theta_center_deg)
        return phi_lo, phi_hi


def build_target_grid_polar_meridian(
    *,
    anchor_lat: Any,
    n_targets: int,
    target_size: Any,
    spacing: Any,
    anchor_lon: Any | None = None,
    theta_center_deg: float = 90.0,
) -> list[MeridianTargetSegment]:
    """
  Build evenly spaced target bands along the northward meridian, continuing past the pole.

  ``anchor_lon`` is accepted for API symmetry with geodesic builders; placement uses the
  polar meridian / orbit-disk model (``LON_GLOBAL`` episode slice).
    """
    _ = anchor_lon if anchor_lon is not None else LON_GLOBAL
    require_compatible_units(anchor_lat, ureg.deg, "anchor_lat")
    require_compatible_units(target_size, ureg.km, "target_size")
    require_compatible_units(spacing, ureg.km, "spacing")
    if n_targets < 1:
        raise ValueError("n_targets must be >= 1")

    target_step_deg = _offset_step_deg(float(target_size.to(ureg.m).magnitude))
    spacing_step_deg = _offset_step_deg(float(spacing.to(ureg.m).magnitude))

    offset_cursor = track_offset_deg_from_anchor_lat_deg(float(anchor_lat.to(ureg.deg).magnitude))
    segments: list[MeridianTargetSegment] = []

    for i in range(n_targets):
        offset_lo = offset_cursor
        offset_hi = offset_cursor + target_step_deg
        lat_lo = lat_deg_from_track_offset_deg(offset_lo)
        lat_hi = lat_deg_from_track_offset_deg(offset_hi)
        lon_lo = _lon_deg_for_track_offset_deg(offset_lo)
        lon_hi = _lon_deg_for_track_offset_deg(offset_hi)
        segments.append(
            MeridianTargetSegment(
                lat_min=min(lat_lo, lat_hi) * ureg.deg,
                lat_max=max(lat_lo, lat_hi) * ureg.deg,
                label=f"target_{i}",
                track_offset_lo_deg=float(offset_lo),
                track_offset_hi_deg=float(offset_hi),
                lon_min_deg=float(lon_lo),
                lon_max_deg=float(lon_hi),
            )
        )
        offset_cursor = offset_hi + spacing_step_deg

    return segments
