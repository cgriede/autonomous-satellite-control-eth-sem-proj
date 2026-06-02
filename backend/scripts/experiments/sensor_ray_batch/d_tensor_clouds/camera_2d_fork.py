"""Hypothesis D — tensorized _batch_cloud_hits_t_best (patches production camera_2d)."""

from __future__ import annotations

import numpy as np

import simulation.camera_2d as _camera_2d_mod
from simulation.camera_2d import *  # noqa: F403


def _batch_cloud_hits_t_best_tensor(
    ray_origin_xy_km: np.ndarray,
    ray_dirs_unit_xy: np.ndarray,
    cloud_arc_specs: list[dict[str, float]],
) -> np.ndarray:
    """Nearest positive cloud-shell hit per ray; all clouds in one (C, N) tensor pass."""
    origin = np.asarray(ray_origin_xy_km, dtype=float).reshape(2,)
    dirs = np.asarray(ray_dirs_unit_xy, dtype=float)
    if dirs.ndim != 2 or dirs.shape[1] != 2:
        raise ValueError("ray_dirs_unit_xy must have shape (N,2).")
    n_rays = dirs.shape[0]
    if not cloud_arc_specs:
        return np.full(n_rays, np.nan, dtype=float)

    radii = np.array([float(s["radius_km"]) for s in cloud_arc_specs], dtype=float)
    starts = np.array([float(s["start_rad"]) for s in cloud_arc_specs], dtype=float)
    ends = np.array([float(s["end_rad"]) for s in cloud_arc_specs], dtype=float)
    c_count = radii.shape[0]

    b = 2.0 * (origin[0] * dirs[:, 0] + origin[1] * dirs[:, 1])
    c_origin = float(np.dot(origin, origin))
    c = c_origin - radii.reshape(c_count, 1) ** 2
    disc = b.reshape(1, n_rays) ** 2 - 4.0 * c

    t_cloud = np.full((c_count, n_rays), np.nan, dtype=float)
    mask = disc >= 0.0
    if np.any(mask):
        sqrt_disc = np.sqrt(np.maximum(disc[mask], 0.0))
        b_m = np.broadcast_to(b.reshape(1, n_rays), (c_count, n_rays))[mask]
        t1 = (-b_m - sqrt_disc) / 2.0
        t2 = (-b_m + sqrt_disc) / 2.0
        t1_valid = t1 > 1e-9
        t2_valid = t2 > 1e-9
        best = np.full(t1.shape, np.nan, dtype=float)
        best[t1_valid] = t1[t1_valid]
        replace = ~t1_valid & t2_valid
        best[replace] = t2[replace]
        both = t1_valid & t2_valid
        best[both] = np.minimum(t1[both], t2[both])
        t_cloud[mask] = best

    hit_points = origin.reshape(1, 1, 2) + t_cloud.reshape(c_count, n_rays, 1) * dirs.reshape(1, n_rays, 2)
    hit_angles = np.arctan2(hit_points[:, :, 1], hit_points[:, :, 0])

    two_pi = 2.0 * np.pi
    angle = np.mod(hit_angles, two_pi)
    start = np.mod(starts.reshape(c_count, 1), two_pi)
    end = np.mod(ends.reshape(c_count, 1), two_pi)
    wrap = start > end
    in_arc_normal = (angle >= start) & (angle <= end)
    in_arc_wrap = (angle >= start) | (angle <= end)
    in_arc = np.where(wrap, in_arc_wrap, in_arc_normal)

    accepted = np.isfinite(t_cloud) & in_arc
    t_cloud_masked = np.where(accepted, t_cloud, np.nan)
    with np.errstate(all="ignore"):
        return np.nanmin(t_cloud_masked, axis=0)


def apply_tensor_patch() -> None:
    _camera_2d_mod._batch_cloud_hits_t_best = _batch_cloud_hits_t_best_tensor


def remove_tensor_patch(original_fn) -> None:
    _camera_2d_mod._batch_cloud_hits_t_best = original_fn
