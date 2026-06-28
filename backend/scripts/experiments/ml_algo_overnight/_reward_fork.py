"""Experiment-only reward patches (dense latent + amplified applied capture)."""

from __future__ import annotations

from typing import Any, Literal

RewardForkMode = Literal["sparse", "dense_latent_10x_applied"]

_MODE: RewardForkMode = "sparse"
_ORIGINAL_COMPUTE: Any = None
_PATCHED = False


def reward_fork_mode() -> RewardForkMode:
    return _MODE


def activate_reward_fork(mode: RewardForkMode) -> None:
    global _MODE, _ORIGINAL_COMPUTE, _PATCHED
    import autonomous_control.reward as reward_mod

    if not _PATCHED:
        _ORIGINAL_COMPUTE = reward_mod.compute_reward
        reward_mod.compute_reward = _patched_compute_reward  # type: ignore[assignment]
        _PATCHED = True
    _MODE = mode


def deactivate_reward_fork() -> None:
    global _PATCHED, _MODE
    if not _PATCHED or _ORIGINAL_COMPUTE is None:
        return
    import autonomous_control.reward as reward_mod

    reward_mod.compute_reward = _ORIGINAL_COMPUTE
    _PATCHED = False
    _MODE = "sparse"


def _patched_compute_reward(signals: Any, cfg: Any) -> tuple[float, dict[str, float]]:
    assert _ORIGINAL_COMPUTE is not None
    total, components = _ORIGINAL_COMPUTE(signals, cfg)
    if _MODE == "dense_latent_10x_applied":
        latent = float(components.get("latent_capture_reward", 0.0))
        applied = float(components.get("image_quality_capture_reward", 0.0))
        total = float(total) - applied + applied * 10.0 + latent
    return float(total), components
