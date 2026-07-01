"""Experiment-only: per-step safe-mode penalty on canonical simulation reward."""

from __future__ import annotations

from typing import Any, Callable

from _penalty_frozen import is_penalized_safety_event, penalty_config

_ORIGINAL_POPULATE: Callable[..., Any] | None = None
_PATCHED = False
_ENABLED = False
_K_PENALTY = 0.0


def safe_mode_penalty_enabled() -> bool:
    return _ENABLED


def k_safe_mode_penalty() -> float:
    return float(_K_PENALTY)


def activate_safe_mode_reward_fork(
    *,
    enable_safe_mode_penalty: bool = True,
    k_safe_mode_penalty: float | None = None,
) -> None:
    """Patch SimulationStepper reward population to subtract safe-mode penalty."""
    global _PATCHED, _ENABLED, _K_PENALTY, _ORIGINAL_POPULATE

    import simulation.stepper as stepper_mod

    cfg = penalty_config()
    _ENABLED = bool(enable_safe_mode_penalty)
    _K_PENALTY = float(
        k_safe_mode_penalty
        if k_safe_mode_penalty is not None
        else cfg.get("k_safe_mode_penalty", 2.0)
    )

    if _PATCHED:
        return

    _ORIGINAL_POPULATE = stepper_mod.SimulationStepper._populate_camera_and_reward

    def _patched_populate(self: Any, *, k: int, prev_omega_wheel: Any) -> None:
        assert _ORIGINAL_POPULATE is not None
        _ORIGINAL_POPULATE(self, k=k, prev_omega_wheel=prev_omega_wheel)
        if not _ENABLED or _K_PENALTY <= 0.0:
            return
        issue_step = int(k) - 1
        if issue_step < 0:
            return
        penalize = any(
            int(ev.get("step", -1)) == issue_step
            and is_penalized_safety_event(str(ev.get("event", "")))
            for ev in getattr(self, "attitude_safety_events", ())
        )
        if penalize:
            self._simulation_reward[k] = float(self._simulation_reward[k]) - _K_PENALTY

    stepper_mod.SimulationStepper._populate_camera_and_reward = _patched_populate  # type: ignore[method-assign]
    _PATCHED = True


def deactivate_safe_mode_reward_fork() -> None:
    global _PATCHED, _ENABLED, _ORIGINAL_POPULATE

    if not _PATCHED or _ORIGINAL_POPULATE is None:
        _ENABLED = False
        return

    import simulation.stepper as stepper_mod

    stepper_mod.SimulationStepper._populate_camera_and_reward = _ORIGINAL_POPULATE  # type: ignore[method-assign]
    _ORIGINAL_POPULATE = None
    _PATCHED = False
    _ENABLED = False


__all__ = [
    "activate_safe_mode_reward_fork",
    "deactivate_safe_mode_reward_fork",
    "k_safe_mode_penalty",
    "safe_mode_penalty_enabled",
]
