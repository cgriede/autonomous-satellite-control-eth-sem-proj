"""Extend S01 warmup bundle fingerprint with dt + reward_mode (experiment-only)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_OVERNIGHT = Path(__file__).resolve().parents[1] / "ml_algo_overnight"
_spec = importlib.util.spec_from_file_location(
    "ml_overnight_warmup_fingerprint_patch_mpo_dual_torque",
    _OVERNIGHT / "_warmup_fingerprint_patch.py",
)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

activate_warmup_fingerprint_patch = _mod.activate_warmup_fingerprint_patch
deactivate_warmup_fingerprint_patch = _mod.deactivate_warmup_fingerprint_patch
set_warmup_fingerprint_extra = _mod.set_warmup_fingerprint_extra

__all__ = [
    "activate_warmup_fingerprint_patch",
    "deactivate_warmup_fingerprint_patch",
    "set_warmup_fingerprint_extra",
]
