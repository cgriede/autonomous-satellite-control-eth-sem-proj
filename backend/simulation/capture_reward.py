"""Capture reward series derived from canonical :class:`SimulationStateSeries` outputs."""

from __future__ import annotations

import numpy as np

from autonomous_control.reward import applied_capture_reward, latent_capture_reward
from environment_definition.constants.AUTONOMOUS_CONTROL_REWARD import REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT
from environment_definition.constants.SATELLITE import MAX_PRIMARY_CAPTURES_PER_ORBIT
from simulation.capture_target import (
    dominant_capture_target_index,
    primary_target_pixel_coverage,
    target_visible_from_codes,
)
from simulation.state_types import SimulationStateSeries
from simulation.take_picture import (
    TakePictureBudget,
    TakePictureConfig,
    resolve_capture_frame_index,
    resolve_capture_time_window_s,
)


def cloud_fraction_at_index(series: SimulationStateSeries, k: int) -> float:
    cloud = float(series.camera_cloud_blocked_fraction[k])
    return 0.0 if not np.isfinite(cloud) else float(np.clip(cloud, 0.0, 1.0))


def sim_dt_s(series: SimulationStateSeries) -> float:
    t_s = np.asarray(series.t_s, dtype=float)
    if t_s.shape[0] < 2:
        return float(series.metadata.sim_dt_s) if series.metadata.sim_dt_s > 0 else 0.4
    return float(np.median(np.diff(t_s)))


def latent_capture_reward_series(
    series: SimulationStateSeries,
    *,
    k_capture: float = REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT,
) -> np.ndarray:
    """Per-frame hypothetical shutter credit (coverage × quality)."""
    n = int(series.t_s.shape[0])
    out = np.zeros(n, dtype=float)
    for k in range(n):
        codes = series.camera_observation_line_codes[k]
        dominant = dominant_capture_target_index(codes)
        visible = dominant is not None
        quality = float(series.camera_image_quality[k])
        if not np.isfinite(quality):
            quality = 0.0
        out[k] = latent_capture_reward(
            target_visible=visible,
            primary_target_pixel_coverage=primary_target_pixel_coverage(
                codes, target_index=dominant
            ),
            camera_image_quality=quality,
            camera_cloud_blocked_fraction=cloud_fraction_at_index(series, k),
            k_capture=k_capture,
        )
    return out


def applied_capture_reward_series(
    series: SimulationStateSeries,
    *,
    cmd_steps: tuple[int, ...],
    max_pictures: int = MAX_PRIMARY_CAPTURES_PER_ORBIT,
    capture_latency_steps: int = 0,
    k_capture: float = REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT,
) -> np.ndarray:
    """Sparse per-frame agent credit on budgeted shutter events."""
    n = int(series.t_s.shape[0])
    out = np.zeros(n, dtype=float)
    if not cmd_steps:
        return out
    budget = TakePictureBudget.from_config(TakePictureConfig(max_pictures_per_episode=max_pictures))
    for cmd_step in cmd_steps:
        capture_k = resolve_capture_frame_index(
            cmd_step=cmd_step,
            n_steps=n,
            capture_latency_steps=capture_latency_steps,
        )
        if capture_k is None:
            continue
        codes = series.camera_observation_line_codes[capture_k]
        dominant = dominant_capture_target_index(codes)
        shutter_ok, reward_eligible = budget.attempt_capture(dominant)
        if not shutter_ok:
            continue
        quality = float(series.camera_image_quality[capture_k])
        if not np.isfinite(quality):
            quality = 0.0
        out[capture_k] = applied_capture_reward(
            picture_taken=True,
            capture_target_novel=reward_eligible,
            target_visible=dominant is not None,
            primary_target_pixel_coverage=primary_target_pixel_coverage(
                codes, target_index=dominant
            ),
            camera_image_quality=quality,
            camera_cloud_blocked_fraction=cloud_fraction_at_index(series, capture_k),
            k_capture=k_capture,
        )
    return out


def capture_time_windows_s(
    series: SimulationStateSeries,
    cmd_steps: tuple[int, ...],
    *,
    capture_latency_steps: int = 0,
) -> list[tuple[float, float]]:
    """Exposure intervals [t0, t1] for each take-picture command (render bands)."""
    t_s = np.asarray(series.t_s, dtype=float)
    dt_s = sim_dt_s(series)
    windows: list[tuple[float, float]] = []
    for cmd_step in cmd_steps:
        if cmd_step < 0 or cmd_step >= t_s.shape[0]:
            continue
        windows.append(
            resolve_capture_time_window_s(
                t_cmd_s=float(t_s[cmd_step]),
                sim_dt_s=dt_s,
                capture_latency_steps=capture_latency_steps,
            )
        )
    return windows


def captured_target_indices_at_step(
    series: SimulationStateSeries,
    sim_idx: int,
    *,
    cmd_steps: tuple[int, ...],
    max_pictures: int = MAX_PRIMARY_CAPTURES_PER_ORBIT,
    capture_latency_steps: int = 0,
) -> frozenset[int]:
    """Targets already imaged by take-picture commands at or before ``sim_idx``."""
    budget = TakePictureBudget.from_config(TakePictureConfig(max_pictures_per_episode=max_pictures))
    n = int(series.t_s.shape[0])
    k_limit = int(sim_idx)
    for cmd_step in cmd_steps:
        if int(cmd_step) > k_limit:
            break
        capture_k = resolve_capture_frame_index(
            cmd_step=int(cmd_step),
            n_steps=n,
            capture_latency_steps=capture_latency_steps,
        )
        if capture_k is None:
            continue
        codes = series.camera_observation_line_codes[capture_k]
        dominant = dominant_capture_target_index(codes)
        budget.attempt_capture(dominant)
    return frozenset(budget.captured_target_indices)


__all__ = [
    "applied_capture_reward_series",
    "capture_time_windows_s",
    "captured_target_indices_at_step",
    "cloud_fraction_at_index",
    "latent_capture_reward_series",
    "sim_dt_s",
]
