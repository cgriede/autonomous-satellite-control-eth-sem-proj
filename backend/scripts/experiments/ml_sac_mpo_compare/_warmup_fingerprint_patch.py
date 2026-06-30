"""Extend S01 warmup bundle fingerprint with dt + reward_mode (experiment-only)."""

from __future__ import annotations

import sys
from pathlib import Path

_OVERNIGHT = Path(__file__).resolve().parents[1] / "ml_algo_overnight"
if str(_OVERNIGHT) not in sys.path:
    sys.path.insert(0, str(_OVERNIGHT))

from _warmup_fingerprint_patch import (  # noqa: E402
    activate_warmup_fingerprint_patch,
    deactivate_warmup_fingerprint_patch,
    set_warmup_fingerprint_extra,
)

__all__ = [
    "activate_warmup_fingerprint_patch",
    "deactivate_warmup_fingerprint_patch",
    "set_warmup_fingerprint_extra",
]
