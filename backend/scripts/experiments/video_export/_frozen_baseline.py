"""Frozen fixtures for video export timing (reuses sensor_ray_batch setups)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SENSOR_RAY_BATCH = Path(__file__).resolve().parent.parent / "sensor_ray_batch"
_spec = importlib.util.spec_from_file_location(
    "sensor_ray_batch_frozen_baseline",
    _SENSOR_RAY_BATCH / "_frozen_baseline.py",
)
assert _spec and _spec.loader
_sensor_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sensor_mod)

build_baseline_sim_config = _sensor_mod.build_baseline_sim_config
build_high_cloud_setup = _sensor_mod.build_high_cloud_setup
