"""15 s dense imaging credit window after accepted shutter (experiment-only)."""

from __future__ import annotations

from typing import Any

_CAPTURE_WINDOW_S = 15.0
_remaining_steps = 0
_sim_dt_s = 1.5
_PATCHED_REWARD = False
_PATCHED_SHUTTER = False
_ORIG_COMPUTE: Any = None
_ORIG_APPLY_SHUTTER: Any = None


def reset_capture_window() -> None:
    global _remaining_steps
    _remaining_steps = 0


def configure_capture_window(*, sim_dt_s: float, window_s: float = _CAPTURE_WINDOW_S) -> None:
    global _sim_dt_s
    _sim_dt_s = float(sim_dt_s)


def _window_steps() -> int:
    return max(1, int(round(_CAPTURE_WINDOW_S / max(_sim_dt_s, 1e-9))))


def _on_shutter_accepted() -> None:
    global _remaining_steps
    _remaining_steps = _window_steps()


def _patched_compute_reward(signals: Any, cfg: Any) -> tuple[float, dict[str, float]]:
    assert _ORIG_COMPUTE is not None
    total, components = _ORIG_COMPUTE(signals, cfg)
    global _remaining_steps
    if _remaining_steps > 0:
        latent = float(components.get("latent_capture_reward", 0.0))
        total = float(total) + latent
        _remaining_steps -= 1
    return float(total), components


def _patched_apply_shutter_capture(self: Any, *args: Any, **kwargs: Any) -> Any:
    assert _ORIG_APPLY_SHUTTER is not None
    result = _ORIG_APPLY_SHUTTER(self, *args, **kwargs)
    _on_shutter_accepted()
    return result


def activate_capture_window_fork() -> None:
    global _PATCHED_REWARD, _PATCHED_SHUTTER, _ORIG_COMPUTE, _ORIG_APPLY_SHUTTER
    import autonomous_control.reward as reward_mod
    from simulation.stepper import SimulationStepper

    if not _PATCHED_REWARD:
        _ORIG_COMPUTE = reward_mod.compute_reward
        reward_mod.compute_reward = _patched_compute_reward  # type: ignore[assignment]
        _PATCHED_REWARD = True
    if not _PATCHED_SHUTTER:
        _ORIG_APPLY_SHUTTER = SimulationStepper.apply_shutter_capture
        SimulationStepper.apply_shutter_capture = _patched_apply_shutter_capture  # type: ignore[method-assign]
        _PATCHED_SHUTTER = True
    reset_capture_window()


def deactivate_capture_window_fork() -> None:
    global _PATCHED_REWARD, _PATCHED_SHUTTER, _ORIG_COMPUTE, _ORIG_APPLY_SHUTTER
    if _PATCHED_REWARD and _ORIG_COMPUTE is not None:
        import autonomous_control.reward as reward_mod

        reward_mod.compute_reward = _ORIG_COMPUTE
        _PATCHED_REWARD = False
    if _PATCHED_SHUTTER and _ORIG_APPLY_SHUTTER is not None:
        from simulation.stepper import SimulationStepper

        SimulationStepper.apply_shutter_capture = _ORIG_APPLY_SHUTTER  # type: ignore[method-assign]
        _PATCHED_SHUTTER = False
    _ORIG_COMPUTE = None
    _ORIG_APPLY_SHUTTER = None
    reset_capture_window()
