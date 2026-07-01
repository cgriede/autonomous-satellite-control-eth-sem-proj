"""Experiment-only reward patch: sparse (production) for Exp 13."""

from __future__ import annotations

from typing import Any, Literal

RewardForkMode = Literal["sparse"]

_MODE: RewardForkMode = "sparse"
_ORIGINAL_COMPUTE: Any = None
_PATCHED = False


def reward_fork_mode() -> RewardForkMode:
    return _MODE


def activate_reward_fork(mode: RewardForkMode = "sparse") -> None:
    global _MODE, _ORIGINAL_COMPUTE, _PATCHED
    import autonomous_control.reward as reward_mod
    from autonomous_control.reward import set_reward_credit_mode

    if mode != "sparse":
        raise ValueError(f"Exp 13 supports sparse only; got {mode!r}")
    if not _PATCHED:
        _ORIGINAL_COMPUTE = reward_mod.compute_reward
        reward_mod.compute_reward = _patched_compute_reward  # type: ignore[assignment]
        _PATCHED = True
    _MODE = mode
    set_reward_credit_mode("sparse")


def _patched_compute_reward(*args: Any, **kwargs: Any) -> Any:
    assert _ORIGINAL_COMPUTE is not None
    return _ORIGINAL_COMPUTE(*args, **kwargs)


__all__ = ["RewardForkMode", "activate_reward_fork", "reward_fork_mode"]
