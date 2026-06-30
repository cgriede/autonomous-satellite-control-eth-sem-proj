"""Project path constants for training/evaluation artifacts."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
AUTONOMOUS_CONTROL_ROOT = BACKEND_ROOT / "autonomous_control"

_RUNS_ENV = os.environ.get("AUTO_SAT_RUNS_ROOT") or os.environ.get("AUTO_SAT_MODELS_ROOT")
RUNS_ROOT = Path(_RUNS_ENV if _RUNS_ENV else str(AUTONOMOUS_CONTROL_ROOT / "runs"))

# Backward compatibility (cluster scripts may still set AUTO_SAT_MODELS_ROOT).
MODELS_ROOT = RUNS_ROOT
