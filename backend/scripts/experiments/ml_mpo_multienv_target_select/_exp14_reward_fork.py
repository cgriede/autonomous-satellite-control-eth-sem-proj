"""Exp 14 reward fork: sparse capture credit + optional torque / budget penalties."""

from __future__ import annotations

from typing import Any, Literal

from autonomous_control.reward import RewardConfig, set_reward_credit_mode

RewardForkMode = Literal[
    "exp14_sparse",
    "exp14_sparse_no_torque",
    "exp14_capture_only",
]

_MODE: RewardForkMode = "exp14_sparse"
_ORIGINAL_COMPUTE: Any = None
_PATCHED = False

ALPHA = 1.0
BETA = 0.5
GAMMA = 0.2
DELTA = 0.1
EPSILON = 0.01


def reward_mode_contract(mode: RewardForkMode | None = None) -> dict[str, Any]:
    """Return the *implemented* reward terms for operator-facing metadata."""
    m = mode or _MODE
    # NOTE: ALPHA/BETA/GAMMA/DELTA are design placeholders only.
    # Current implementation routes through canonical RewardConfig switches.
    if m == "exp14_sparse":
        return {
            "mode": m,
            "capture_credit": "enabled",
            "torque_effort_penalty": f"enabled(k_torque_effort={float(EPSILON)})",
            "budget_exhausted_shutter_penalty": "enabled",
            "composite_alpha_beta_gamma_delta": "not_implemented",
        }
    if m == "exp14_sparse_no_torque":
        return {
            "mode": m,
            "capture_credit": "enabled",
            "torque_effort_penalty": "disabled",
            "budget_exhausted_shutter_penalty": "enabled",
            "composite_alpha_beta_gamma_delta": "not_implemented",
        }
    if m == "exp14_capture_only":
        return {
            "mode": m,
            "capture_credit": "enabled",
            "torque_effort_penalty": "disabled",
            "budget_exhausted_shutter_penalty": "disabled",
            "composite_alpha_beta_gamma_delta": "not_implemented",
        }
    raise ValueError(f"Unknown Exp 14 reward mode: {m!r}")


def reward_fork_mode() -> RewardForkMode:
    return _MODE


def exp14_reward_config(mode: RewardForkMode | None = None) -> RewardConfig:
    m = mode or _MODE
    base = dict(
        enable_distance_reward=False,
        enable_image_quality_capture=True,
        enable_shutter_waste_penalty=False,
    )
    if m == "exp14_sparse":
        return RewardConfig(
            **base,
            enable_torque_effort=True,
            k_torque_effort=float(EPSILON),
            enable_budget_exhausted_shutter_penalty=True,
        )
    if m == "exp14_sparse_no_torque":
        return RewardConfig(
            **base,
            enable_torque_effort=False,
            enable_budget_exhausted_shutter_penalty=True,
        )
    if m == "exp14_capture_only":
        return RewardConfig(
            **base,
            enable_torque_effort=False,
            enable_budget_exhausted_shutter_penalty=False,
        )
    raise ValueError(f"Unknown Exp 14 reward mode: {m!r}")


def activate_reward_fork(mode: RewardForkMode = "exp14_sparse") -> RewardConfig:
    global _MODE, _ORIGINAL_COMPUTE, _PATCHED
    import autonomous_control.reward as reward_mod

    if mode not in (
        "exp14_sparse",
        "exp14_sparse_no_torque",
        "exp14_capture_only",
    ):
        raise ValueError(f"Unknown Exp 14 reward mode: {mode!r}")
    if not _PATCHED:
        _ORIGINAL_COMPUTE = reward_mod.compute_reward
        reward_mod.compute_reward = _patched_compute_reward  # type: ignore[assignment]
        _PATCHED = True
    _MODE = mode
    set_reward_credit_mode("sparse")
    return exp14_reward_config(mode)


def deactivate_reward_fork() -> None:
    global _PATCHED, _MODE
    if not _PATCHED or _ORIGINAL_COMPUTE is None:
        return
    import autonomous_control.reward as reward_mod
    from autonomous_control.reward import set_reward_credit_mode

    reward_mod.compute_reward = _ORIGINAL_COMPUTE
    _PATCHED = False
    _MODE = "exp14_sparse"
    set_reward_credit_mode("sparse")


def _patched_compute_reward(signals: Any, cfg: Any) -> tuple[float, dict[str, float]]:
    assert _ORIGINAL_COMPUTE is not None
    merged = exp14_reward_config(_MODE)
    return _ORIGINAL_COMPUTE(signals=signals, cfg=merged)


__all__ = [
    "ALPHA",
    "BETA",
    "DELTA",
    "EPSILON",
    "GAMMA",
    "RewardForkMode",
    "activate_reward_fork",
    "deactivate_reward_fork",
    "exp14_reward_config",
    "reward_mode_contract",
    "reward_fork_mode",
]
