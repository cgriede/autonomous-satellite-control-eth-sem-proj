"""
Canonical slide-based reward with per-component flags + legacy helpers.

The canonical entrypoint is :func:`canonical_reward`. Both
``simulation/run_simulation.py`` and ``environment_definition/environment.py``
route through it so that ``SimulationStateSeries.simulation_reward`` and the RL
``env.step`` scalar reward share a single definition.

Reward components (toggle via :class:`RewardConfig`):
- ``slide``              : slide v1 distance term in ``[d_op, d_th]``.
- ``outer_gate``         : zero reward beyond ``viewing_threshold`` (slide gate).
- ``no_picture_penalty`` : ``-100`` if no picture / target not visible / beyond ``d_th``.
- ``energy``             : ``-k_e * E`` from wheel-momentum change.

See ``docs/ml/reward_v1_implementation.md`` for PDF deltas and units.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from environment_definition.constants.AUTONOMOUS_CONTROL_REWARD import (
    CAMERA_VIEWING_DISTANCE_THRESHOLD,
    OPTIMAL_GROUND_RANGE,
    RESOLUTION_GROUND_RANGE_THRESHOLD,
    REWARD_ENERGY_LINEAR_COEFFICIENT,
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

    enable_slide: bool = True
    enable_outer_gate: bool = True
    enable_no_picture_penalty: bool = True
    enable_energy: bool = True
    k_energy: float = float(REWARD_ENERGY_LINEAR_COEFFICIENT)


@dataclass(frozen=True)
class RewardSignals:
    """
    Per-step signals consumed by :func:`canonical_reward`.

    Both sim-side and env-side callers populate this. Energy inputs are optional
    and only used when ``RewardConfig.enable_energy`` is true.
    """

    distance_to_target: Any  # pint Quantity (length)
    picture_taken: bool
    target_visible: bool
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


def reward_v1_slides(
    *,
    distance_to_target: "Quantity",
    d_op: "Quantity",
    d_th: "Quantity",
    viewing_threshold: "Quantity",
    picture_taken: bool,
    target_visible: bool,
) -> float:
    """
    Slide primary-objectives reward (legacy helper, kept for unit tests).

    - If distance_to_target > viewing_threshold: return 0 (outer gate).
    - Else if no picture / target not visible / distance beyond d_th: -100.
    - Else if distance is in [d_op, d_th]: R1 = -100 * d_eff / (d_th - d_op) with d in meters.
    - Else (d < d_op): use d_eff = d_op in the same formula (best resolution band).
    """
    d_v = _distance_m(distance_to_target)
    v_t = _distance_m(viewing_threshold)
    if d_v > v_t:
        return 0.0

    if not picture_taken or not target_visible:
        return -100.0

    d_op_m = _distance_m(d_op)
    d_th_m = _distance_m(d_th)
    if d_th_m <= d_op_m:
        raise ValueError("Require d_th > d_op for slide reward v1.")

    if d_v > d_th_m:
        return -100.0

    d_eff = max(d_v, d_op_m)
    denom = d_th_m - d_op_m
    return -100.0 * d_eff / denom


def reward_v1_with_energy(
    *,
    distance_to_target: "Quantity",
    d_op: "Quantity",
    d_th: "Quantity",
    viewing_threshold: "Quantity",
    picture_taken: bool,
    target_visible: bool,
    energy_joules: "Quantity | None",
    k_e: float,
) -> float:
    """
    Slide reward minus k_e * E [J] (legacy helper, kept for unit tests).

    When outside the viewing gate, returns 0 and does not subtract energy.
    """
    if _distance_m(distance_to_target) > _distance_m(viewing_threshold):
        return 0.0

    r_slide = reward_v1_slides(
        distance_to_target=distance_to_target,
        d_op=d_op,
        d_th=d_th,
        viewing_threshold=viewing_threshold,
        picture_taken=picture_taken,
        target_visible=target_visible,
    )

    if energy_joules is None:
        return r_slide

    e_j = float(energy_joules.to(ureg.joule).magnitude)
    return r_slide - k_e * e_j


def canonical_reward(
    *,
    signals: RewardSignals,
    cfg: RewardConfig,
) -> tuple[float, dict[str, float]]:
    """
    Single canonical reward used by both simulation and RL env.

    Returns ``(total_reward, components_dict)``. ``components_dict`` always
    contains ``slide``, ``no_picture_penalty`` and ``energy`` keys so callers
    can log/decompose. Any component disabled in ``cfg`` contributes ``0.0``.

    ``distance_to_target`` must be a pint length Quantity. Energy inputs are
    only required when ``cfg.enable_energy`` is true; otherwise they may be
    ``None``.
    """
    d_v = _distance_m(signals.distance_to_target)
    v_t = _distance_m(CAMERA_VIEWING_DISTANCE_THRESHOLD)
    d_op_m = _distance_m(OPTIMAL_GROUND_RANGE)
    d_th_m = _distance_m(RESOLUTION_GROUND_RANGE_THRESHOLD)
    if d_th_m <= d_op_m:
        raise ValueError("Require d_th > d_op for canonical reward.")

    components: dict[str, float] = {
        "slide": 0.0,
        "no_picture_penalty": 0.0,
        "energy": 0.0,
    }

    # Outer viewing gate: beyond v_t, slide and no-picture contribute 0. Energy
    # term is also suppressed to match the slide v1 convention.
    if cfg.enable_outer_gate and d_v > v_t:
        return 0.0, components

    in_failure_region = (
        (not signals.picture_taken)
        or (not signals.target_visible)
        or (d_v > d_th_m)
    )

    if in_failure_region:
        if cfg.enable_no_picture_penalty:
            components["no_picture_penalty"] = -100.0
    else:
        if cfg.enable_slide:
            d_eff = max(d_v, d_op_m)
            denom = d_th_m - d_op_m
            components["slide"] = -100.0 * d_eff / denom

    if (
        cfg.enable_energy
        and signals.wheel_inertia is not None
        and signals.omega_before is not None
        and signals.omega_after is not None
    ):
        e = energy_from_wheel_momentum_change(
            wheel_inertia=signals.wheel_inertia,
            omega_before=signals.omega_before,
            omega_after=signals.omega_after,
        )
        e_j = float(e.to(ureg.joule).magnitude)
        components["energy"] = -cfg.k_energy * e_j

    total = components["slide"] + components["no_picture_penalty"] + components["energy"]
    return total, components


def reward_v1_project(
    *,
    distance_to_target: "Quantity",
    picture_taken: bool,
    target_visible: bool,
    wheel_inertia: "Quantity",
    omega_before: "Quantity",
    omega_after: "Quantity",
    cfg: RewardConfig | None = None,
) -> float:
    """
    Convenience wrapper using project constants and the canonical reward.

    Kept as a thin adapter around :func:`canonical_reward` so existing callers
    (tests, docs) continue to work.
    """
    signals = RewardSignals(
        distance_to_target=distance_to_target,
        picture_taken=picture_taken,
        target_visible=target_visible,
        wheel_inertia=wheel_inertia,
        omega_before=omega_before,
        omega_after=omega_after,
    )
    total, _ = canonical_reward(
        signals=signals,
        cfg=cfg if cfg is not None else RewardConfig(),
    )
    return total


__all__ = [
    "RewardConfig",
    "RewardSignals",
    "canonical_reward",
    "energy_from_wheel_momentum_change",
    "reward_v1_slides",
    "reward_v1_with_energy",
    "reward_v1_project",
]
