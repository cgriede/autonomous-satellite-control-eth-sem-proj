"""
Slide reward v1 + optional linear energy penalty from wheel momentum change.

See docs/ml/reward_v1_implementation.md for PDF deltas and unit conventions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from environment_definition.constants.AUTONOMOUS_CONTROL_REWARD import (
    CAMERA_VIEWING_DISTANCE_THRESHOLD,
    OPTIMAL_GROUND_RANGE,
    RESOLUTION_GROUND_RANGE_THRESHOLD,
    REWARD_ENERGY_LINEAR_COEFFICIENT,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

if TYPE_CHECKING:
    from pint import Quantity


def _distance_m(q: Quantity) -> float:
    return float(q.to(ureg.m).magnitude)


def energy_from_wheel_momentum_change(
    *,
    wheel_inertia: Quantity,
    omega_before: Quantity,
    omega_after: Quantity,
) -> Quantity:
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
    distance_to_target: Quantity,
    d_op: Quantity,
    d_th: Quantity,
    viewing_threshold: Quantity,
    picture_taken: bool,
    target_visible: bool,
) -> float:
    """
    Primary objectives only (slide v1).

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
    distance_to_target: Quantity,
    d_op: Quantity,
    d_th: Quantity,
    viewing_threshold: Quantity,
    picture_taken: bool,
    target_visible: bool,
    energy_joules: Quantity | None,
    k_e: float,
) -> float:
    """
    Slide reward minus k_e * E [J]. When outside the viewing gate, returns 0 and does not
    subtract energy.
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


def reward_v1_project(
    *,
    distance_to_target: Quantity,
    picture_taken: bool,
    target_visible: bool,
    wheel_inertia: Quantity,
    omega_before: Quantity,
    omega_after: Quantity,
) -> float:
    """
    Convenience wrapper using project constants from AUTONOMOUS_CONTROL_REWARD.
    """
    e = energy_from_wheel_momentum_change(
        wheel_inertia=wheel_inertia,
        omega_before=omega_before,
        omega_after=omega_after,
    )
    return reward_v1_with_energy(
        distance_to_target=distance_to_target,
        d_op=OPTIMAL_GROUND_RANGE,
        d_th=RESOLUTION_GROUND_RANGE_THRESHOLD,
        viewing_threshold=CAMERA_VIEWING_DISTANCE_THRESHOLD,
        picture_taken=picture_taken,
        target_visible=target_visible,
        energy_joules=e,
        k_e=REWARD_ENERGY_LINEAR_COEFFICIENT,
    )
