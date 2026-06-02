"""Experiment-only FOV pre-cull (not promoted — neutral on frozen 108-cloud benchmark)."""

from __future__ import annotations

import numpy as np

CLOUD_FOV_CULL_ENABLED = True
CLOUD_FOV_CULL_MIN_CLOUDS = 8


def _arc_sample_phis(start_rad: float, end_rad: float) -> list[float] | None:
    """Sample arc φ angles; return None when cull would be non-conservative."""
    two_pi = 2.0 * np.pi
    span = (end_rad - start_rad) % two_pi
    if span > np.pi:
        return None
    center = 0.5 * (start_rad + end_rad)
    phis = [float(start_rad), float(end_rad), float(center)]
    if start_rad > end_rad:
        phis.extend([0.0, two_pi])
    return phis


def _direction_intervals_overlap(a_lo: float, a_hi: float, b_lo: float, b_hi: float) -> bool:
    """Overlap test for contiguous direction-angle intervals (span ≤ π)."""
    return a_lo <= b_hi and b_lo <= a_hi


def _cloud_arc_direction_envelope(
    sat_pos_xy_km: np.ndarray,
    *,
    radius_km: float,
    start_rad: float,
    end_rad: float,
) -> tuple[float, float] | None:
    phis = _arc_sample_phis(start_rad, end_rad)
    if phis is None:
        return None
    p = np.asarray(sat_pos_xy_km, dtype=float).reshape(2,)
    dir_angles: list[float] = []
    for phi in phis:
        pt = radius_km * np.array([np.cos(phi), np.sin(phi)], dtype=float)
        d = pt - p
        dir_angles.append(float(np.arctan2(d[1], d[0])))
    return float(min(dir_angles)), float(max(dir_angles))


def filter_cloud_specs_for_camera_fov(
    sat_pos_xy_km: np.ndarray,
    ray_dirs_unit_xy: np.ndarray,
    cloud_arc_specs: list[dict[str, float]],
    *,
    enabled: bool = CLOUD_FOV_CULL_ENABLED,
    min_clouds_for_cull: int = CLOUD_FOV_CULL_MIN_CLOUDS,
) -> tuple[list[dict[str, float]], dict[str, int]]:
    """
    Drop cloud arcs that cannot intersect any ray direction in the camera FOV.

    Conservative: when uncertain (large/wrap arcs), the cloud is kept.
    """
    stats = {"clouds_total": len(cloud_arc_specs), "clouds_culled": 0}
    if not enabled or len(cloud_arc_specs) < min_clouds_for_cull:
        return cloud_arc_specs, stats

    dirs = np.asarray(ray_dirs_unit_xy, dtype=float)
    ray_angles = np.arctan2(dirs[:, 1], dirs[:, 0])
    fov_lo = float(np.min(ray_angles))
    fov_hi = float(np.max(ray_angles))
    if (fov_hi - fov_lo) > np.pi:
        return cloud_arc_specs, stats

    kept: list[dict[str, float]] = []
    for spec in cloud_arc_specs:
        envelope = _cloud_arc_direction_envelope(
            sat_pos_xy_km,
            radius_km=float(spec["radius_km"]),
            start_rad=float(spec["start_rad"]),
            end_rad=float(spec["end_rad"]),
        )
        if envelope is None:
            kept.append(spec)
            continue
        arc_lo, arc_hi = envelope
        if _direction_intervals_overlap(fov_lo, fov_hi, arc_lo, arc_hi):
            kept.append(spec)
        else:
            stats["clouds_culled"] += 1
    return kept, stats
