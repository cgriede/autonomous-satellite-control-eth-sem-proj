"""Fixed dt 1.5s profile for SAC shutter reward split (Exp 9)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

EXPERIMENT_ROOT = Path(__file__).resolve().parent
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"

_spec = importlib.util.spec_from_file_location(
    "ml_overnight_sim_constants_split",
    OVERNIGHT_ROOT / "_sim_constants_fork.py",
)
assert _spec and _spec.loader
_overnight_sim = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _overnight_sim
_spec.loader.exec_module(_overnight_sim)

FIXED_SPLIT_DT = _overnight_sim.FIXED_COMPARE_DT
apply_dt_profile = _overnight_sim.apply_dt_profile
apply_dt_profile_from_dict = _overnight_sim.apply_dt_profile_from_dict
get_applied_dt_profile = _overnight_sim.get_applied_dt_profile
require_dt_profile = _overnight_sim.require_dt_profile

RESULTS_DIR = EXPERIMENT_ROOT / "results"
DT_PROFILE_PATH = RESULTS_DIR / "dt_profile.json"


def write_fixed_split_dt_profile(*, train_episodes: int = 50) -> dict[str, Any]:
    profile = FIXED_SPLIT_DT
    payload = {
        "aborted": False,
        "sim_dt_s": profile.sim_dt_s,
        "controller_interval_s": profile.controller_interval_s,
        "effective_controller_interval_s": profile.effective_controller_interval_s,
        "label": profile.label,
        "train_episodes": int(train_episodes),
        "source": "fixed_split",
    }
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DT_PROFILE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def apply_experiment_dt_profile() -> dict[str, Any]:
    payload = json.loads(DT_PROFILE_PATH.read_text(encoding="utf-8"))
    apply_dt_profile_from_dict(payload)
    return payload


__all__ = [
    "DT_PROFILE_PATH",
    "FIXED_SPLIT_DT",
    "apply_dt_profile",
    "apply_experiment_dt_profile",
    "get_applied_dt_profile",
    "require_dt_profile",
    "write_fixed_split_dt_profile",
]
