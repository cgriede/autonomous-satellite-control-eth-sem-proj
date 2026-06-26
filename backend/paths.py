"""Project path constants for training/evaluation artifacts."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
AUTONOMOUS_CONTROL_ROOT = BACKEND_ROOT / "autonomous_control"
MODELS_ROOT = Path(
    os.environ.get("AUTO_SAT_MODELS_ROOT", str(AUTONOMOUS_CONTROL_ROOT / "models"))
)

