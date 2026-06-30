"""Extend S01 warmup bundle fingerprint with dt + arm metadata (experiment-only)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_OVERNIGHT = Path(__file__).resolve().parents[1] / "ml_algo_overnight"
_spec = importlib.util.spec_from_file_location(
    "ml_overnight_warmup_fingerprint_budget",
    _OVERNIGHT / "_warmup_fingerprint_patch.py",
)
assert _spec and _spec.loader
_overnight_wfp = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _overnight_wfp
_spec.loader.exec_module(_overnight_wfp)

activate_warmup_fingerprint_patch = _overnight_wfp.activate_warmup_fingerprint_patch
deactivate_warmup_fingerprint_patch = _overnight_wfp.deactivate_warmup_fingerprint_patch
set_warmup_fingerprint_extra = _overnight_wfp.set_warmup_fingerprint_extra

__all__ = [
    "activate_warmup_fingerprint_patch",
    "deactivate_warmup_fingerprint_patch",
    "set_warmup_fingerprint_extra",
]
