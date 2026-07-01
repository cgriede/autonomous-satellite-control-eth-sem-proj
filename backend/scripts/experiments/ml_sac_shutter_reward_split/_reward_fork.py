"""Experiment shim: sparse vector + torque-effort off (reward flags set on MPOConfig)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

_ORIGINAL_COMPUTE: Any = None
_PATCHED_REWARD = False


def activate_reward_fork() -> None:
    """Sparse production reward + vector torque-effort off."""
    global _ORIGINAL_COMPUTE, _PATCHED_REWARD

    import autonomous_control.reward as reward_mod
    from autonomous_control.reward import set_reward_credit_mode

    if not _PATCHED_REWARD:
        _ORIGINAL_COMPUTE = reward_mod.compute_reward
        reward_mod.compute_reward = _patched_compute_reward  # type: ignore[assignment]
        _PATCHED_REWARD = True
    set_reward_credit_mode("sparse")


def deactivate_reward_fork() -> None:
    global _PATCHED_REWARD, _ORIGINAL_COMPUTE

    if _PATCHED_REWARD and _ORIGINAL_COMPUTE is not None:
        import autonomous_control.reward as reward_mod
        from autonomous_control.reward import set_reward_credit_mode

        reward_mod.compute_reward = _ORIGINAL_COMPUTE
        _PATCHED_REWARD = False
        set_reward_credit_mode("sparse")

    _ORIGINAL_COMPUTE = None


def _patched_compute_reward(signals: Any, cfg: Any) -> tuple[float, dict[str, float]]:
    assert _ORIGINAL_COMPUTE is not None
    cfg = replace(cfg, enable_torque_effort=False)
    total, components = _ORIGINAL_COMPUTE(signals, cfg)
    return float(total), components


__all__ = ["activate_reward_fork", "deactivate_reward_fork"]
