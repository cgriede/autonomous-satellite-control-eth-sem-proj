"""Shutter capture evaluation shared by RL episodes and verification parity."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simulation.capture_target import (
    dominant_capture_target_index,
    primary_target_pixel_coverage,
)
from simulation.take_picture import TakePictureBudget, resolve_capture_frame_index


@dataclass(frozen=True)
class ShutterRewardOverride:
    """RewardKernel shutter context for applied capture credit at ``cmd_step``."""

    picture_taken: bool
    capture_target_novel: bool
    target_visible: bool
    camera_image_quality: float
    primary_target_pixel_coverage: float
    camera_cloud_blocked_fraction: float


@dataclass(frozen=True)
class ShutterCaptureResult:
    cmd_step: int
    capture_step: int | None
    override: ShutterRewardOverride
    budget_remaining: int
    dominant_target_index: int | None


def _cloud_fraction_at(cloud: np.ndarray, k: int) -> float:
    value = float(cloud[k])
    return 0.0 if not np.isfinite(value) else float(np.clip(value, 0.0, 1.0))


def evaluate_shutter_from_arrays(
    *,
    cmd_step: int,
    n_steps: int,
    observation_line_codes: np.ndarray,
    camera_image_quality: np.ndarray,
    camera_cloud_blocked_fraction: np.ndarray,
    budget: TakePictureBudget,
    capture_latency_steps: int = 0,
) -> ShutterCaptureResult:
    """Apply one take-picture command; reward uses quality at the resolved capture frame."""
    capture_k = resolve_capture_frame_index(
        cmd_step=int(cmd_step),
        n_steps=int(n_steps),
        capture_latency_steps=int(capture_latency_steps),
    )
    dominant: int | None = None
    if capture_k is not None:
        codes = np.asarray(observation_line_codes[capture_k], dtype=np.int8)
        dominant = dominant_capture_target_index(codes)
        taken, capture_target_novel = budget.attempt_capture(dominant)
    else:
        taken = False
        capture_target_novel = False

    quality = (
        float(camera_image_quality[capture_k])
        if capture_k is not None
        else float("nan")
    )
    cloud = _cloud_fraction_at(camera_cloud_blocked_fraction, capture_k) if capture_k is not None else 0.0
    visible = dominant is not None
    coverage = (
        primary_target_pixel_coverage(
            np.asarray(observation_line_codes[capture_k], dtype=np.int8),
            target_index=dominant,
        )
        if capture_k is not None
        else 0.0
    )
    q = quality if np.isfinite(quality) else 0.0
    override = ShutterRewardOverride(
        picture_taken=taken,
        capture_target_novel=capture_target_novel,
        target_visible=visible,
        camera_image_quality=q,
        primary_target_pixel_coverage=coverage,
        camera_cloud_blocked_fraction=cloud,
    )
    return ShutterCaptureResult(
        cmd_step=int(cmd_step),
        capture_step=capture_k,
        override=override,
        budget_remaining=int(budget.remaining),
        dominant_target_index=dominant,
    )


__all__ = [
    "ShutterCaptureResult",
    "ShutterRewardOverride",
    "evaluate_shutter_from_arrays",
]
