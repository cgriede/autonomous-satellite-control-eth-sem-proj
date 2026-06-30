"""Experiment-only reward patches: sparse (production) and dense (H6 formula)."""

from __future__ import annotations

from typing import Any, Literal

RewardForkMode = Literal["sparse", "dense", "dense_latent_10x_applied"]

_MODE: RewardForkMode = "sparse"
_ORIGINAL_COMPUTE: Any = None
_PATCHED = False


def _is_dense_mode(mode: RewardForkMode) -> bool:
    return mode in ("dense", "dense_latent_10x_applied")


def reward_fork_mode() -> RewardForkMode:
    return _MODE


def activate_reward_fork(mode: RewardForkMode) -> None:
    global _MODE, _ORIGINAL_COMPUTE, _PATCHED
    import autonomous_control.reward as reward_mod
    from autonomous_control.reward import set_reward_credit_mode

    if not _PATCHED:
        _ORIGINAL_COMPUTE = reward_mod.compute_reward
        reward_mod.compute_reward = _patched_compute_reward  # type: ignore[assignment]
        _PATCHED = True
    _MODE = mode
    set_reward_credit_mode("dense" if _is_dense_mode(mode) else "sparse")


def deactivate_reward_fork() -> None:
    global _PATCHED, _MODE
    if not _PATCHED or _ORIGINAL_COMPUTE is None:
        return
    import autonomous_control.reward as reward_mod
    from autonomous_control.reward import set_reward_credit_mode

    reward_mod.compute_reward = _ORIGINAL_COMPUTE
    _PATCHED = False
    _MODE = "sparse"
    set_reward_credit_mode("sparse")


def _patched_compute_reward(signals: Any, cfg: Any) -> tuple[float, dict[str, float]]:
    assert _ORIGINAL_COMPUTE is not None
    total, components = _ORIGINAL_COMPUTE(signals, cfg)
    if _is_dense_mode(_MODE):
        latent = float(components.get("latent_capture_reward", 0.0))
        applied = float(components.get("image_quality_capture_reward", 0.0))
        total = float(total) - applied + applied * 10.0 + latent
    return float(total), components
