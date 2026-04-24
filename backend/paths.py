"""Project path constants for training/evaluation artifacts."""

from __future__ import annotations

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent
AUTONOMOUS_CONTROL_ROOT = BACKEND_ROOT / "autonomous_control"
MODELS_ROOT = AUTONOMOUS_CONTROL_ROOT / "models"

