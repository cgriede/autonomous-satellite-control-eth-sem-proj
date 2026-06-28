"""Monkeypatch SIMULATION timestep / controller interval for overnight dt profiles."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

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


def get_applied_dt_profile() -> dict[str, float] | None:
    return dict(_APPLIED) if _APPLIED is not None else None


def apply_dt_profile(profile: DtProfile) -> None:
    global _APPLIED, _ORIGINAL_SIMULATION
    import environment_definition.constants.SIMULATION as sim_mod

    if _ORIGINAL_SIMULATION is None:
        _ORIGINAL_SIMULATION = sim_mod.SIMULATION
    sim_mod.SIMULATION = replace(
        _ORIGINAL_SIMULATION,
        simulation_timestep=float(profile.sim_dt_s) * ureg.s,
        controller_update_interval=float(profile.controller_interval_s) * ureg.s,
    )
    _APPLIED = {
        "sim_dt_s": float(profile.sim_dt_s),
        "controller_interval_s": float(profile.controller_interval_s),
        "effective_controller_interval_s": float(profile.effective_controller_interval_s),
        "label": profile.label,
    }


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
    import environment_definition.constants.SIMULATION as sim_mod

    sim_mod.SIMULATION = _ORIGINAL_SIMULATION
    _APPLIED = None
