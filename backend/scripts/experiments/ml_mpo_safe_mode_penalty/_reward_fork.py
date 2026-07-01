"""Experiment-only reward patch: sparse (production) + safe-mode penalty hook."""

from __future__ import annotations

from typing import Any, Literal

from _safe_mode_reward_fork import activate_safe_mode_reward_fork, safe_mode_penalty_enabled

RewardForkMode = Literal["sparse"]

_MODE: RewardForkMode = "sparse"
_ORIGINAL_COMPUTE: Any = None
_PATCHED = False


def reward_fork_mode() -> RewardForkMode:
    return _MODE


def activate_reward_fork(
    mode: RewardForkMode = "sparse",
    *,
    enable_safe_mode_penalty: bool = True,
    k_safe_mode_penalty: float | None = None,
) -> None:
    global _MODE, _ORIGINAL_COMPUTE, _PATCHED

    import autonomous_control.reward as reward_mod
    from autonomous_control.reward import set_reward_credit_mode

    if mode != "sparse":
        raise ValueError(f"Exp 10 supports sparse only; got {mode!r}")
    if not _PATCHED:
        _ORIGINAL_COMPUTE = reward_mod.compute_reward
        reward_mod.compute_reward = _patched_compute_reward  # type: ignore[assignment]
        _PATCHED = True
    _MODE = mode
    set_reward_credit_mode("sparse")
    activate_safe_mode_reward_fork(
        enable_safe_mode_penalty=enable_safe_mode_penalty,
        k_safe_mode_penalty=k_safe_mode_penalty,
    )


def deactivate_reward_fork() -> None:
    global _PATCHED, _MODE, _ORIGINAL_COMPUTE

    from _safe_mode_reward_fork import deactivate_safe_mode_reward_fork

    if _PATCHED and _ORIGINAL_COMPUTE is not None:
        import autonomous_control.reward as reward_mod
        from autonomous_control.reward import set_reward_credit_mode

        reward_mod.compute_reward = _ORIGINAL_COMPUTE
        _PATCHED = False
        set_reward_credit_mode("sparse")
    deactivate_safe_mode_reward_fork()
    _ORIGINAL_COMPUTE = None
    _MODE = "sparse"


def _patched_compute_reward(signals: Any, cfg: Any) -> tuple[float, dict[str, float]]:
    assert _ORIGINAL_COMPUTE is not None
    return _ORIGINAL_COMPUTE(signals, cfg)


__all__ = [
    "RewardForkMode",
    "activate_reward_fork",
    "deactivate_reward_fork",
    "reward_fork_mode",
    "safe_mode_penalty_enabled",
]
