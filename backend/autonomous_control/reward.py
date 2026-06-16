"""
Reward components and combiner used by simulation + RL env.

Public API:
- :func:`distance_band_reward` (distance/visibility term)
- :func:`energy_reward` (energy penalty term)
- :func:`latent_capture_reward` (hypothetical shutter credit: coverage × quality)
- :func:`applied_capture_reward` (latent credit only when a picture is taken)
- :func:`compute_reward` (combines enabled components from :class:`RewardConfig`)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from environment_definition.constants.AUTONOMOUS_CONTROL_REWARD import (
    CAMERA_VIEWING_DISTANCE_THRESHOLD,
    OPTIMAL_GROUND_RANGE,
    REWARD_AREA_INTERSECTION_WEIGHT,
    REWARD_AREA_NOVELTY_WEIGHT,
    REWARD_ENERGY_LINEAR_COEFFICIENT,
    REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

if TYPE_CHECKING:
    from pint import Quantity


@dataclass(frozen=True)
class RewardConfig:
    """
    Per-component toggles and weights for the canonical reward.

    Kept lightweight (no torch/ML imports) so that ``simulation/run_simulation.py``
    can import it without pulling the training stack. Re-exported from
    ``autonomous_control.mpo_config`` and embedded in ``MPOConfig.reward``.
    """

    enable_distance_reward: bool = True
    enable_outer_gate: bool = True
    enable_energy: bool = False
    enable_area_intersection: bool = False
    enable_area_novelty: bool = False
    # Cloud penalty (§H): scales down / gates distance term when camera strip is cloud-blocked.
    enable_cloud_penalty: bool = False
    # Optional secondary-camera cloud penalty (wide-FOV strip, §H).
    enable_secondary_cloud_penalty: bool = False
    k_energy: float = float(REWARD_ENERGY_LINEAR_COEFFICIENT)
    k_area_intersection: float = float(REWARD_AREA_INTERSECTION_WEIGHT)
    k_area_novelty: float = float(REWARD_AREA_NOVELTY_WEIGHT)
    # Penalty weight: reward multiplier reduction per unit cloud-blocked fraction.
    k_cloud_penalty: float = 1.0
    # Take-picture mode: latent = coverage × quality; applied only on shutter (budget-limited).
    enable_image_quality_capture: bool = False
    k_image_quality_capture: float = float(REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT)


@dataclass(frozen=True)
class RewardSignals:
    """
    Per-step signals consumed by :func:`compute_reward`.

    Both sim-side and env-side callers populate this. Energy inputs are optional
    and only used when ``RewardConfig.enable_energy`` is true.
    """

    distance_to_target: Any  # pint Quantity (length)
    picture_taken: bool
    target_visible: bool
    # Primary-camera normalized quality [0, 1] at capture frame (take-picture mode).
    camera_image_quality: float = 0.0
    # Primary 1D observation line: fraction of bins on the dominant target (take-picture coverage).
    primary_target_pixel_coverage: float = 0.0
    # Applied capture credit only when the shutter fires on a not-yet-downlinked target index.
    capture_target_novel: bool = True
    target_area_intersection_ratio: float = 0.0
    target_area_novelty_ratio: float = 0.0
    # Cloud signals (§H): fraction of primary/secondary strip blocked by clouds [0, 1].
    camera_cloud_blocked_fraction: float = 0.0
    secondary_camera_cloud_blocked_fraction: float = 0.0
    wheel_inertia: Any | None = None  # pint Quantity (kg*m^2)
    omega_before: Any | None = None  # pint Quantity (rad/s)
    omega_after: Any | None = None  # pint Quantity (rad/s)


def _distance_m(q: "Quantity") -> float:
    return float(q.to(ureg.m).magnitude)


def energy_from_wheel_momentum_change(
    *,
    wheel_inertia: "Quantity",
    omega_before: "Quantity",
    omega_after: "Quantity",
) -> "Quantity":
    """
    Kinetic-energy proxy associated with a change in wheel angular momentum:

        E = (ΔH)² / (2 I_w),   ΔH = |H₁ - H₀|,   H = I_w ω

    Returns energy in joules.
    """
    if wheel_inertia.to(ureg.kg * ureg.m**2).magnitude <= 0.0:
        raise ValueError("wheel_inertia must be positive.")

    i_si = wheel_inertia.to(ureg.kg * ureg.m**2)
    w0 = omega_before.to(ureg.rad / ureg.s)
    w1 = omega_after.to(ureg.rad / ureg.s)
    h0 = (i_si * w0).to(ureg.kg * ureg.m**2 / ureg.s)
    h1 = (i_si * w1).to(ureg.kg * ureg.m**2 / ureg.s)
    dh_mag = abs((h1 - h0).to(ureg.kg * ureg.m**2 / ureg.s).magnitude)
    dh = dh_mag * (ureg.kg * ureg.m**2 / ureg.s)
    e = dh**2 / (2.0 * i_si)
    return e.to(ureg.joule)


def distance_band_reward(
    *,
    distance_to_target: "Quantity",
    d_op: "Quantity",
    viewing_threshold: "Quantity",
    picture_taken: bool,
    target_visible: bool,
    outer_gate_enabled: bool = True,
) -> float:
    """
    Distance-based reward term.

    Piecewise behavior:
    - If ``outer_gate_enabled`` and ``distance_to_target > viewing_threshold``: return ``0``.
    - Else if picture is missing or target is not visible: return ``-100``.
    - Else (inside LOS and target visible): return ``-100 + 100 * scalar`` where
      ``scalar = (v_t - d_eff) / (v_t - d_op)``,
      ``d_eff = min(max(d, d_op), v_t)``, and ``v_t`` is ``viewing_threshold``.

    This makes the in-LOS reward equal to:
    - ``0`` at the optimal distance ``d_op``,
    - ``-100`` at the LOS threshold ``viewing_threshold``,
    - and clamps to ``0`` for ``d < d_op``.
    """
    d_v = _distance_m(distance_to_target)
    v_t = _distance_m(viewing_threshold)
    d_op_m = _distance_m(d_op)
    if v_t <= d_op_m:
        raise ValueError("Require viewing_threshold > d_op for distance-band reward.")

    # Primary camera must see target pixels; no "free" zero reward when far but not imaging.
    if not picture_taken or not target_visible:
        return -100.0

    if outer_gate_enabled and d_v > v_t:
        return 0.0

    d_eff = min(max(d_v, d_op_m), v_t)
    denom = v_t - d_op_m
    scalar = (v_t - d_eff) / denom
    return -100.0 + 100.0 * scalar


def latent_capture_reward(
    *,
    target_visible: bool,
    primary_target_pixel_coverage: float,
    camera_image_quality: float,
    camera_cloud_blocked_fraction: float = 0.0,
    k_capture: float,
) -> float:
    """
    Hypothetical shutter credit if the agent took a picture at this instant.

    Extends the legacy area-coverage term with normalized image quality::

        latent = k_capture * coverage * quality * (1 - cloud_frac)

    where ``coverage`` is the primary-camera target pixel fraction [0, 1].
    """
    if not target_visible:
        return 0.0
    coverage = float(np.clip(primary_target_pixel_coverage, 0.0, 1.0))
    q = float(np.clip(camera_image_quality, 0.0, 1.0))
    if not np.isfinite(q):
        return 0.0
    cloud = float(np.clip(camera_cloud_blocked_fraction, 0.0, 1.0))
    return k_capture * coverage * q * (1.0 - cloud)


def applied_capture_reward(
    *,
    picture_taken: bool,
    target_visible: bool,
    primary_target_pixel_coverage: float,
    camera_image_quality: float,
    camera_cloud_blocked_fraction: float = 0.0,
    k_capture: float,
    capture_target_novel: bool = True,
) -> float:
    """Agent credit on shutter when ``picture_taken`` and ``capture_target_novel``."""
    if not picture_taken or not capture_target_novel:
        return 0.0
    return latent_capture_reward(
        target_visible=target_visible,
        primary_target_pixel_coverage=primary_target_pixel_coverage,
        camera_image_quality=camera_image_quality,
        camera_cloud_blocked_fraction=camera_cloud_blocked_fraction,
        k_capture=k_capture,
    )


def image_quality_capture_reward(
    *,
    picture_taken: bool,
    camera_image_quality: float,
    camera_cloud_blocked_fraction: float = 0.0,
    k_capture: float,
    target_visible: bool = True,
    primary_target_pixel_coverage: float = 1.0,
) -> float:
    """Backward-compatible alias for :func:`applied_capture_reward` (full coverage assumed by default)."""
    return applied_capture_reward(
        picture_taken=picture_taken,
        target_visible=target_visible,
        primary_target_pixel_coverage=primary_target_pixel_coverage,
        camera_image_quality=camera_image_quality,
        camera_cloud_blocked_fraction=camera_cloud_blocked_fraction,
        k_capture=k_capture,
    )


def energy_reward(
    *,
    wheel_inertia: "Quantity",
    omega_before: "Quantity",
    omega_after: "Quantity",
    k_energy: float,
) -> float:
    """Energy penalty term: ``-k_energy * E`` where ``E`` is in joules."""
    e = energy_from_wheel_momentum_change(
        wheel_inertia=wheel_inertia,
        omega_before=omega_before,
        omega_after=omega_after,
    )
    e_j = float(e.to(ureg.joule).magnitude)
    return -k_energy * e_j


def compute_reward(
    *,
    signals: RewardSignals,
    cfg: RewardConfig,
) -> tuple[float, dict[str, float]]:
    """
    Combines distance and energy terms used by simulation and RL env.

    Returns ``(total_reward, components_dict)``. ``components_dict`` always
    contains ``distance_reward`` and ``energy_reward`` keys.

    ``distance_to_target`` must be a pint length Quantity. Energy inputs are
    only required when ``cfg.enable_energy`` is true; otherwise they may be
    ``None``.
    """
    d_v = _distance_m(signals.distance_to_target)
    v_t = _distance_m(CAMERA_VIEWING_DISTANCE_THRESHOLD)
    if v_t <= _distance_m(OPTIMAL_GROUND_RANGE):
        raise ValueError("Require viewing_threshold > d_op for reward.")

    components: dict[str, float] = {
        "distance_reward": 0.0,
        "area_intersection_reward": 0.0,
        "area_novelty_reward": 0.0,
        "energy_reward": 0.0,
        "cloud_penalty": 0.0,
        "secondary_cloud_penalty": 0.0,
        "latent_capture_reward": 0.0,
        "image_quality_capture_reward": 0.0,
    }

    if cfg.enable_distance_reward:
        components["distance_reward"] = distance_band_reward(
            distance_to_target=signals.distance_to_target,
            d_op=OPTIMAL_GROUND_RANGE,
            viewing_threshold=CAMERA_VIEWING_DISTANCE_THRESHOLD,
            picture_taken=signals.picture_taken,
            target_visible=signals.target_visible,
            outer_gate_enabled=cfg.enable_outer_gate,
        )

    if cfg.enable_area_intersection and signals.target_visible and signals.picture_taken:
        area_ratio = float(np.clip(signals.target_area_intersection_ratio, 0.0, 1.0))
        components["area_intersection_reward"] = cfg.k_area_intersection * area_ratio

    if cfg.enable_area_novelty and signals.target_visible and signals.picture_taken:
        novelty_ratio = float(np.clip(signals.target_area_novelty_ratio, 0.0, 1.0))
        components["area_novelty_reward"] = cfg.k_area_novelty * novelty_ratio

    if (
        cfg.enable_energy
        and signals.wheel_inertia is not None
        and signals.omega_before is not None
        and signals.omega_after is not None
        and (not cfg.enable_outer_gate or d_v <= v_t)
    ):
        components["energy_reward"] = energy_reward(
            wheel_inertia=signals.wheel_inertia,
            omega_before=signals.omega_before,
            omega_after=signals.omega_after,
            k_energy=cfg.k_energy,
        )

    if cfg.enable_cloud_penalty:
        cloud_frac = float(np.clip(signals.camera_cloud_blocked_fraction, 0.0, 1.0))
        components["cloud_penalty"] = -cfg.k_cloud_penalty * cloud_frac

    if cfg.enable_secondary_cloud_penalty:
        scnd_frac = float(np.clip(signals.secondary_camera_cloud_blocked_fraction, 0.0, 1.0))
        components["secondary_cloud_penalty"] = -cfg.k_cloud_penalty * scnd_frac

    if cfg.enable_image_quality_capture:
        coverage = float(np.clip(signals.primary_target_pixel_coverage, 0.0, 1.0))
        if coverage <= 0.0 and signals.target_visible:
            coverage = float(np.clip(signals.target_area_intersection_ratio, 0.0, 1.0))
        components["latent_capture_reward"] = latent_capture_reward(
            target_visible=signals.target_visible,
            primary_target_pixel_coverage=coverage,
            camera_image_quality=signals.camera_image_quality,
            camera_cloud_blocked_fraction=signals.camera_cloud_blocked_fraction,
            k_capture=cfg.k_image_quality_capture,
        )
        components["image_quality_capture_reward"] = applied_capture_reward(
            picture_taken=signals.picture_taken,
            capture_target_novel=signals.capture_target_novel,
            target_visible=signals.target_visible,
            primary_target_pixel_coverage=coverage,
            camera_image_quality=signals.camera_image_quality,
            camera_cloud_blocked_fraction=signals.camera_cloud_blocked_fraction,
            k_capture=cfg.k_image_quality_capture,
        )

    total = (
        components["distance_reward"]
        + components["area_intersection_reward"]
        + components["area_novelty_reward"]
        + components["energy_reward"]
        + components["cloud_penalty"]
        + components["secondary_cloud_penalty"]
        + components["image_quality_capture_reward"]
    )
    return total, components

__all__ = [
    "RewardConfig",
    "RewardSignals",
    "applied_capture_reward",
    "compute_reward",
    "distance_band_reward",
    "energy_reward",
    "energy_from_wheel_momentum_change",
    "image_quality_capture_reward",
    "latent_capture_reward",
]
