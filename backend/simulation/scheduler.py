from __future__ import annotations

import warnings

import numpy as np

_SCHEDULER_WARNED = False


def resolve_controller_interval_steps(
    *,
    configured_interval_s: float,
    sim_dt_s: float,
) -> tuple[int, float]:
    global _SCHEDULER_WARNED
    interval_s = float(configured_interval_s)
    if interval_s < sim_dt_s:
        interval_s = sim_dt_s
    raw_steps = interval_s / sim_dt_s
    rounded_steps = max(1, int(np.round(raw_steps)))
    if not np.isclose(raw_steps, float(rounded_steps)) and not _SCHEDULER_WARNED:
        effective_interval_s = rounded_steps * sim_dt_s
        warnings.warn(
            "controller_update_interval "
            f"({interval_s:g} s) is not an integer multiple of simulation_timestep "
            f"({sim_dt_s:g} s); using nearest multiple: "
            f"{effective_interval_s:g} s ({rounded_steps} sim step"
            f"{'' if rounded_steps == 1 else 's'}).",
            stacklevel=2,
        )
        _SCHEDULER_WARNED = True
    return rounded_steps, rounded_steps * sim_dt_s
