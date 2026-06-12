"""Primary-camera image smear and quality from ground-track motion during exposure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from pint import Quantity
from pymap3d.ellipsoid import Ellipsoid

from environment_definition.constants.EARTH import WGS84_ELLIPSOID
from environment_definition.constants.SATELLITE import (
    CAMERA_EXPOSURE_TIME,
    IMAGE_QUALITY_SMEAR_REFERENCE_M,
    IMAGE_QUALITY_SMEAR_REFERENCE_PX,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.geometry.orbit_disk_wgs84 import (
    KM_TO_M,
    disk_direction_xy_to_ecef_unit,
    disk_xy_km_to_ecef_m,
    ray_oblate_spheroid_positive_hit_distance_m,
)
from utils.units.require_compatible_unit import require_compatible_units

# Backward-compatible alias (px reference; quality uses ground-meters reference below).
IMAGE_QUALITY_EPSILON = float(IMAGE_QUALITY_SMEAR_REFERENCE_PX)


@dataclass(frozen=True)
class PrimaryImageQualityDiagnostics:
    """Intermediate quantities for one primary-camera frame (plain floats for storage/print)."""

    slant_range_km: float
    elevation_deg: float
    omega_body_rad_s: float
    v_bore_ground_m_s: float
    v_bore_ground_x_m_s: float
    v_bore_ground_y_m_s: float
    smear_px: float
    quality: float
    gsd_m: float
    exposure_time_s: float


def slant_range_sat_to_bore(
    sat_pos_xy_km: np.ndarray,
    bore_ground_xy_km: np.ndarray,
) -> Quantity:
    """Slant range from satellite to primary bore ground hit [km]."""
    sat = np.asarray(sat_pos_xy_km, dtype=float).reshape(2)
    bore = np.asarray(bore_ground_xy_km, dtype=float).reshape(2)
    slant_km = float(np.linalg.norm(sat - bore))
    return slant_km * ureg.km


def elevation_angle_at_bore_rad(
    sat_pos_xy_km: np.ndarray,
    bore_ground_xy_km: np.ndarray,
) -> Quantity:
    """
    Elevation of the satellite as seen from the bore ground point [rad].

    2D disk: local outward radial at bore; elevation above tangent = arctan2(radial, tangent).
    """
    sat = np.asarray(sat_pos_xy_km, dtype=float).reshape(2)
    bore = np.asarray(bore_ground_xy_km, dtype=float).reshape(2)
    vec = sat - bore
    slant_km = float(np.linalg.norm(vec))
    if slant_km <= 0.0:
        return 0.0 * ureg.rad
    bore_norm = float(np.linalg.norm(bore))
    if bore_norm <= 0.0:
        return 0.0 * ureg.rad
    radial_out = bore / bore_norm
    radial_comp = float(np.dot(vec, radial_out))
    tangent_comp = abs(float(vec[0] * radial_out[1] - vec[1] * radial_out[0]))
    elev_rad = float(np.arctan2(radial_comp, tangent_comp))
    return elev_rad * ureg.rad


def _ellipsoid_ray_quadratic(
    origin_m: np.ndarray,
    dir_unit_m: np.ndarray,
    *,
    ell: Ellipsoid,
) -> tuple[float, float, float]:
    """Coefficients ``aa, bb, cc`` for ``aa t² + bb t + cc = 0`` (WGS84 oblate spheroid)."""
    a = float(ell.semimajor_axis)
    b = float(ell.semiminor_axis)
    ox, oy, oz = [float(v) for v in np.asarray(origin_m, dtype=float).reshape(3)]
    dx, dy, dz = [float(v) for v in np.asarray(dir_unit_m, dtype=float).reshape(3)]
    ia2 = 1.0 / (a * a)
    ib2 = 1.0 / (b * b)
    aa = (dx * dx + dy * dy) * ia2 + dz * dz * ib2
    bb = 2.0 * ((ox * dx + oy * dy) * ia2 + oz * dz * ib2)
    cc = (ox * ox + oy * oy) * ia2 + oz * oz * ib2 - 1.0
    return aa, bb, cc


def analytic_bore_ground_velocity_disk_m_s(
    *,
    sat_pos_xy_km: np.ndarray,
    boresight_dir_unit_xy: np.ndarray,
    theta_orbit_rad: float,
    omega_orbit_rad_s: float,
    orbit_radius_km: float,
    omega_body_rad_s: float,
    ell: Ellipsoid | None = None,
) -> np.ndarray:
    """
    Time derivative of the WGS84 bore ground hit in the orbit disk [m/s].

    Uses the same ray–ellipsoid intersection as ``camera_2d`` / ``orbit_disk_wgs84``:
    ``hit = sat + t * boresight`` with ``t`` from the oblate-spheroid quadratic, then
    implicit differentiation for ``ṫ`` from satellite motion and body rate.
    """
    e = WGS84_ELLIPSOID if ell is None else ell
    sat = np.asarray(sat_pos_xy_km, dtype=float).reshape(2)
    bore = np.asarray(boresight_dir_unit_xy, dtype=float).reshape(2)
    bore_norm = float(np.linalg.norm(bore))
    if bore_norm <= 0.0:
        return np.array([np.nan, np.nan], dtype=float)
    bore = bore / bore_norm

    sat_vel_km_s = float(orbit_radius_km) * float(omega_orbit_rad_s) * np.array(
        [-np.sin(float(theta_orbit_rad)), np.cos(float(theta_orbit_rad))],
        dtype=float,
    )
    origin_m = disk_xy_km_to_ecef_m(sat)
    origin_dot_m = np.array(
        [float(sat_vel_km_s[0]) * KM_TO_M, 0.0, float(sat_vel_km_s[1]) * KM_TO_M],
        dtype=float,
    )
    dir_m = disk_direction_xy_to_ecef_unit(bore)
    phi = float(np.arctan2(bore[1], bore[0]))
    dir_dot_m = float(omega_body_rad_s) * np.array(
        [-np.sin(phi), 0.0, np.cos(phi)],
        dtype=float,
    )

    t_m = ray_oblate_spheroid_positive_hit_distance_m(origin_m, dir_m, ell=e)
    if t_m is None:
        return np.array([np.nan, np.nan], dtype=float)

    aa, bb, cc = _ellipsoid_ray_quadratic(origin_m, dir_m, ell=e)
    aa_dot = 2.0 * (
        dir_m[0] * dir_dot_m[0] / (e.semimajor_axis**2)
        + dir_m[1] * dir_dot_m[1] / (e.semimajor_axis**2)
        + dir_m[2] * dir_dot_m[2] / (e.semiminor_axis**2)
    )
    bb_dot = 2.0 * (
        origin_dot_m[0] * dir_m[0] / (e.semimajor_axis**2)
        + origin_m[0] * dir_dot_m[0] / (e.semimajor_axis**2)
        + origin_dot_m[1] * dir_m[1] / (e.semimajor_axis**2)
        + origin_m[1] * dir_dot_m[1] / (e.semimajor_axis**2)
        + origin_dot_m[2] * dir_m[2] / (e.semiminor_axis**2)
        + origin_m[2] * dir_dot_m[2] / (e.semiminor_axis**2)
    )
    cc_dot = 2.0 * (
        origin_m[0] * origin_dot_m[0] / (e.semimajor_axis**2)
        + origin_m[1] * origin_dot_m[1] / (e.semimajor_axis**2)
        + origin_m[2] * origin_dot_m[2] / (e.semiminor_axis**2)
    )

    denom = 2.0 * aa * float(t_m) + bb
    if abs(denom) <= 1e-12:
        return np.array([np.nan, np.nan], dtype=float)
    t_dot = -(aa_dot * float(t_m) * float(t_m) + bb_dot * float(t_m) + cc_dot) / denom

    hit_dot_m = origin_dot_m + t_dot * dir_m + float(t_m) * dir_dot_m
    return np.array([float(hit_dot_m[0]), float(hit_dot_m[2])], dtype=float)


def bore_ground_speed_m_s(
    bore_ground_xy_km: np.ndarray,
    *,
    dt_s: float,
    prev_bore_ground_xy_km: np.ndarray,
) -> float:
    """Empirical ground speed of the bore footprint from consecutive disk positions [m/s]."""
    if dt_s <= 0.0:
        return float("nan")
    bore = np.asarray(bore_ground_xy_km, dtype=float).reshape(2)
    prev = np.asarray(prev_bore_ground_xy_km, dtype=float).reshape(2)
    if not np.all(np.isfinite(bore)) or not np.all(np.isfinite(prev)):
        return float("nan")
    return float(np.linalg.norm(bore - prev) / dt_s * 1000.0)


def ground_blur_m(*, v_ground: Any, exposure_time: Any) -> Quantity:
    """Ground displacement during exposure [m] (before GSD conversion to px)."""
    require_compatible_units(v_ground, "meter/second", "v_ground")
    require_compatible_units(exposure_time, "second", "exposure_time")
    return (abs(v_ground) * exposure_time).to(ureg.m)


def image_smear_px(*, v_ground: Any, exposure_time: Any, gsd: Any) -> float:
    """Pixel smear during exposure (dimensionless GSD units)."""
    require_compatible_units(gsd, "meter", "gsd")
    blur_m = ground_blur_m(v_ground=v_ground, exposure_time=exposure_time)
    smear = blur_m / gsd
    return float(smear.to(ureg.dimensionless).magnitude)


def image_quality_normalized(
    blur_m: float,
    *,
    smear_reference_m: float | None = None,
) -> float:
    """
    Map ground blur [m] to [0, 1].

    ``quality = ref / (blur + ref)``; zero blur → 1; blur = ref → 0.5.
    GSD affects ``smear_px`` only; quality uses physical ground motion vs ``ref``.
    """
    if smear_reference_m is None:
        smear_reference_m = float(IMAGE_QUALITY_SMEAR_REFERENCE_M.to(ureg.m).magnitude)
    ref = float(smear_reference_m)
    quality_normalized = ref / (float(blur_m) + ref)
    return float(np.clip(quality_normalized, 0.0, 1.0))


def decompose_primary_image_quality(
    *,
    sat_pos_xy_km: np.ndarray,
    bore_ground_xy_km: np.ndarray,
    boresight_dir_unit_xy: np.ndarray,
    gsd_m: float,
    theta_orbit_rad: float,
    omega_orbit_rad_s: float,
    orbit_radius_km: float,
    omega_body_rad_s: float,
    exposure_time: Any | None = None,
) -> PrimaryImageQualityDiagnostics:
    """
    Full smear breakdown for one timestep using analytic bore ground-track speed.

    Returns NaN fields when geometry or GSD is invalid.
    """
    if exposure_time is None:
        exposure_time = CAMERA_EXPOSURE_TIME
    require_compatible_units(exposure_time, "second", "exposure_time")
    t_exp_s = float(exposure_time.to(ureg.s).magnitude)

    bore = np.asarray(bore_ground_xy_km, dtype=float).reshape(2)
    if not np.all(np.isfinite(bore)) or not np.isfinite(gsd_m) or gsd_m <= 0.0:
        nan = float("nan")
        return PrimaryImageQualityDiagnostics(
            slant_range_km=nan,
            elevation_deg=nan,
            omega_body_rad_s=float(omega_body_rad_s),
            v_bore_ground_m_s=nan,
            v_bore_ground_x_m_s=nan,
            v_bore_ground_y_m_s=nan,
            smear_px=nan,
            quality=nan,
            gsd_m=float(gsd_m) if np.isfinite(gsd_m) else nan,
            exposure_time_s=t_exp_s,
        )

    slant = slant_range_sat_to_bore(sat_pos_xy_km, bore)
    elevation = elevation_angle_at_bore_rad(sat_pos_xy_km, bore)
    v_xy = analytic_bore_ground_velocity_disk_m_s(
        sat_pos_xy_km=sat_pos_xy_km,
        boresight_dir_unit_xy=boresight_dir_unit_xy,
        theta_orbit_rad=float(theta_orbit_rad),
        omega_orbit_rad_s=float(omega_orbit_rad_s),
        orbit_radius_km=float(orbit_radius_km),
        omega_body_rad_s=float(omega_body_rad_s),
    )
    v_bore = float(np.linalg.norm(v_xy))
    gsd = float(gsd_m) * ureg.m
    v_q = v_bore * ureg.m / ureg.s
    blur_m = float(ground_blur_m(v_ground=v_q, exposure_time=exposure_time).to(ureg.m).magnitude)
    smear = image_smear_px(v_ground=v_q, exposure_time=exposure_time, gsd=gsd)
    quality = image_quality_normalized(blur_m)
    return PrimaryImageQualityDiagnostics(
        slant_range_km=float(slant.to(ureg.km).magnitude),
        elevation_deg=float(elevation.to(ureg.deg).magnitude),
        omega_body_rad_s=float(omega_body_rad_s),
        v_bore_ground_m_s=v_bore,
        v_bore_ground_x_m_s=float(v_xy[0]),
        v_bore_ground_y_m_s=float(v_xy[1]),
        smear_px=smear,
        quality=quality,
        gsd_m=float(gsd_m),
        exposure_time_s=t_exp_s,
    )


def evaluate_primary_image_quality(
    *,
    sat_pos_xy_km: np.ndarray,
    bore_ground_xy_km: np.ndarray,
    boresight_dir_unit_xy: np.ndarray,
    gsd_m: float,
    theta_orbit_rad: float,
    omega_orbit_rad_s: float,
    orbit_radius_km: float,
    omega_body_rad_s: float,
    exposure_time: Any | None = None,
) -> tuple[float, float]:
    """
    Primary-camera image smear and normalized quality for one timestep.

    Smear uses analytic ``|d(bore_ground)/dt|`` on the orbit disk (WGS84 ray hit).

    Returns:
        (smear_px, quality) as plain floats for numpy storage; NaN if geometry invalid.
    """
    if exposure_time is None:
        exposure_time = CAMERA_EXPOSURE_TIME
    diag = decompose_primary_image_quality(
        sat_pos_xy_km=sat_pos_xy_km,
        bore_ground_xy_km=bore_ground_xy_km,
        boresight_dir_unit_xy=boresight_dir_unit_xy,
        gsd_m=gsd_m,
        theta_orbit_rad=theta_orbit_rad,
        omega_orbit_rad_s=omega_orbit_rad_s,
        orbit_radius_km=orbit_radius_km,
        omega_body_rad_s=omega_body_rad_s,
        exposure_time=exposure_time,
    )
    return diag.smear_px, diag.quality
