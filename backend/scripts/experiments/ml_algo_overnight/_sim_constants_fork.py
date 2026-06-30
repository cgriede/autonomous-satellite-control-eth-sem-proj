"""Monkeypatch SIMULATION timestep / controller interval for overnight dt profiles."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass, replace
from typing import Any

from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

_SIMULATION_MODULE = "environment_definition.constants.SIMULATION"


def _simulation_constants_module():
    """Return SIMULATION.py module (not the SIMULATION instance shadowed on constants)."""
    return importlib.import_module(_SIMULATION_MODULE)


_APPLIED: dict[str, float] | None = None
_ORIGINAL_SIMULATION: Any = None


@dataclass(frozen=True)
class DtProfile:
    sim_dt_s: float
    controller_interval_s: float
    effective_controller_interval_s: float
    label: str = ""


DT_CANDIDATES: tuple[DtProfile, ...] = (
    DtProfile(0.4, 1.0, 0.8, "ref_0.4s"),
    DtProfile(0.8, 0.8, 0.8, "dt_0.8s"),
    DtProfile(1.0, 1.0, 1.0, "dt_1.0s"),
    DtProfile(1.5, 1.5, 1.5, "dt_1.5s"),
)

# Fixed profile for compare-track experiments (H0 winner).
FIXED_COMPARE_DT = next(p for p in DT_CANDIDATES if p.label == "dt_1.5s")


def get_applied_dt_profile() -> dict[str, float] | None:
    return dict(_APPLIED) if _APPLIED is not None else None


def _propagate_simulation_binding(old_sim: Any, new_sim: Any) -> int:
    """Update cached ``from ... import SIMULATION`` bindings across loaded modules."""
    updated = 0
    for mod in sys.modules.values():
        if mod is None:
            continue
        if getattr(mod, "SIMULATION", None) is old_sim:
            setattr(mod, "SIMULATION", new_sim)
            updated += 1
    return updated


def _read_simulation_dt_s(sim: Any) -> tuple[float, float]:
    sim_dt_s = float(sim.simulation_timestep.to(ureg.s).magnitude)
    ctrl_s = float(sim.controller_update_interval.to(ureg.s).magnitude)
    return sim_dt_s, ctrl_s


def require_dt_profile(
    profile: DtProfile,
    *,
    context: str = "",
) -> dict[str, float]:
    """Fail fast if production imports still see the wrong SIMULATION constants."""
    sim_mod = _simulation_constants_module()
    sim_dt_s, ctrl_s = _read_simulation_dt_s(sim_mod.SIMULATION)
    prefix = f"{context}: " if context else ""
    if abs(sim_dt_s - profile.sim_dt_s) > 1e-9 or abs(ctrl_s - profile.controller_interval_s) > 1e-9:
        applied = get_applied_dt_profile()
        raise RuntimeError(
            f"{prefix}SIMULATION mismatch after apply_dt_profile — "
            f"expected sim_dt_s={profile.sim_dt_s}, controller_interval_s={profile.controller_interval_s}; "
            f"module has sim_dt_s={sim_dt_s}, controller_interval_s={ctrl_s}; "
            f"applied_registry={applied}"
        )
    return {
        "sim_dt_s": sim_dt_s,
        "controller_interval_s": ctrl_s,
        "effective_controller_interval_s": float(profile.effective_controller_interval_s),
        "label": profile.label,
    }


def apply_dt_profile(profile: DtProfile) -> None:
    global _APPLIED, _ORIGINAL_SIMULATION
    sim_mod = _simulation_constants_module()

    if _ORIGINAL_SIMULATION is None:
        _ORIGINAL_SIMULATION = sim_mod.SIMULATION

    previous = sim_mod.SIMULATION
    new_sim = replace(
        _ORIGINAL_SIMULATION,
        simulation_timestep=float(profile.sim_dt_s) * ureg.s,
        controller_update_interval=float(profile.controller_interval_s) * ureg.s,
    )
    sim_mod.SIMULATION = new_sim
    _propagate_simulation_binding(previous, new_sim)
    _APPLIED = {
        "sim_dt_s": float(profile.sim_dt_s),
        "controller_interval_s": float(profile.controller_interval_s),
        "effective_controller_interval_s": float(profile.effective_controller_interval_s),
        "label": profile.label,
    }
    require_dt_profile(profile, context="apply_dt_profile")


def apply_dt_profile_from_dict(payload: dict[str, Any]) -> None:
    apply_dt_profile(
        DtProfile(
            sim_dt_s=float(payload["sim_dt_s"]),
            controller_interval_s=float(payload["controller_interval_s"]),
            effective_controller_interval_s=float(
                payload.get(
                    "effective_controller_interval_s",
                    payload["controller_interval_s"],
                )
            ),
            label=str(payload.get("label", "")),
        )
    )


def restore_simulation_constants() -> None:
    global _APPLIED, _ORIGINAL_SIMULATION
    if _ORIGINAL_SIMULATION is None:
        return
    sim_mod = _simulation_constants_module()
    previous = sim_mod.SIMULATION
    sim_mod.SIMULATION = _ORIGINAL_SIMULATION
    _propagate_simulation_binding(previous, _ORIGINAL_SIMULATION)
    _APPLIED = None
