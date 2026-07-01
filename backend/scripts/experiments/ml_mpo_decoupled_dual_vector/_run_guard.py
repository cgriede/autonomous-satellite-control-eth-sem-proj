"""Single active ML pipeline job on this host (global mutex)."""

from __future__ import annotations

import sys
from pathlib import Path

_EXPERIMENTS = Path(__file__).resolve().parents[1]
if str(_EXPERIMENTS) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENTS))

from pipeline_run_guard import acquire_pipeline_run_lock  # noqa: E402

_SLUG = Path(__file__).resolve().parent.name


def acquire_experiment_run_lock(*, script: str) -> None:
    acquire_pipeline_run_lock(slug=_SLUG, script=script)
