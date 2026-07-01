"""Cadence / duty-cycle arm specs for Exp 13 (sim : collect : learn ratios)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CadenceArmSpec:
    arm_id: str
    ratio_label: str
    sim_dt_s: float
    controller_interval_s: float
    train_every_n_steps: int
    updates_per_step: int
    track: str = "cadence"

    def dt_label(self) -> str:
        if self.sim_dt_s == 1.5 and self.controller_interval_s == 1.5:
            return "dt_1.5s"
        if self.sim_dt_s == 1.5 and self.controller_interval_s == 3.0:
            return "dt_1.5s_ap2"
        return f"sim{self.sim_dt_s}_ap{self.controller_interval_s}"


CADENCE_ARMS: tuple[CadenceArmSpec, ...] = (
    CadenceArmSpec("baseline_1_1_1", "1:1:1", 1.5, 1.5, 1, 1),
    CadenceArmSpec("cadence_1_1_10", "1:1:10", 1.5, 1.5, 10, 10),
    CadenceArmSpec("cadence_1_1_50", "1:1:50", 1.5, 1.5, 50, 50),
    CadenceArmSpec("cadence_1_2_4", "1:2:4", 1.5, 3.0, 4, 4),
    CadenceArmSpec("duty_100x100", "1:1:100", 1.5, 1.5, 100, 100, track="duty"),
)

# cadence_1_1_10 and duty_10x10 are identical knobs — one arm only.


def default_cadence_arms() -> tuple[CadenceArmSpec, ...]:
    return CADENCE_ARMS


def cadence_arm_by_id(arm_id: str) -> CadenceArmSpec:
    for arm in CADENCE_ARMS:
        if arm.arm_id == arm_id:
            return arm
    raise KeyError(f"Unknown cadence arm_id: {arm_id!r}")


def expected_train_updates(stores: int, *, train_every: int, updates: int) -> int:
    stride = max(1, int(train_every))
    burst = max(1, int(updates))
    return (int(stores) // stride) * burst


__all__ = [
    "CADENCE_ARMS",
    "CadenceArmSpec",
    "cadence_arm_by_id",
    "default_cadence_arms",
    "expected_train_updates",
]
