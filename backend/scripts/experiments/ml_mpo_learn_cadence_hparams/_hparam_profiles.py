"""Track B — one-at-a-time MPO hyperparameter screen arms (Phase 2 B0)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HparamArmSpec:
    arm_id: str
    mpo_overrides: dict[str, Any]
    note: str = ""


# Baseline cadence (winner from Track A) applied at run time; these only override MPO fields.
HPARAM_SCREEN_ARMS: tuple[HparamArmSpec, ...] = (
    HparamArmSpec("hparam_default", {}, "MPOConfig defaults + Exp 8 shared overrides"),
    HparamArmSpec("hparam_lr_pi_low", {"learning_rate_pi": 5e-5}, "actor LR low"),
    HparamArmSpec("hparam_lr_pi_high", {"learning_rate_pi": 4.5e-4}, "actor LR high"),
    HparamArmSpec("hparam_lr_q_low", {"learning_rate_q": 1.5e-4}, "critic LR low"),
    HparamArmSpec("hparam_lr_q_high", {"learning_rate_q": 1e-3}, "critic LR high"),
    HparamArmSpec("hparam_lr_eta_low", {"learning_rate_eta": 3e-4}, "dual LR low"),
    HparamArmSpec("hparam_lr_eta_high", {"learning_rate_eta": 3e-3}, "dual LR high"),
    HparamArmSpec("hparam_batch_128", {"batch_size": 128}, "batch size 128"),
    HparamArmSpec("hparam_batch_512", {"batch_size": 512}, "batch size 512"),
    HparamArmSpec("hparam_kl_mu_high", {"target_kl_mu": 0.2}, "trust region mu high"),
    HparamArmSpec("hparam_samples_low", {"num_samples_q": 40, "num_samples_pi": 20}, "fewer MPO samples"),
    HparamArmSpec("hparam_samples_high", {"num_samples_q": 120, "num_samples_pi": 60}, "more MPO samples"),
)


def hparam_arm_by_id(arm_id: str) -> HparamArmSpec:
    for arm in HPARAM_SCREEN_ARMS:
        if arm.arm_id == arm_id:
            return arm
    raise KeyError(f"Unknown hparam arm_id: {arm_id!r}")


__all__ = ["HPARAM_SCREEN_ARMS", "HparamArmSpec", "hparam_arm_by_id"]
