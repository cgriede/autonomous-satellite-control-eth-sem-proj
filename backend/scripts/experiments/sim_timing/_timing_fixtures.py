"""Frozen setups for sim timing profiles (reuses sensor_ray_batch fixtures)."""

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
build_low_cloud_setup = _sensor_mod.build_low_cloud_setup


def build_sat_sim_interactive_setup():
    """Mirror ``simulation_runner.py``: seed=0, bus-only (no camera mounts), S01 clouds."""
    from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup

    return build_setup(seed=0, include_cameras=False)


def build_sat_sim_interactive_sim_config():
    from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig

    return SimulationConfig(render_mode=RenderMode.INTERACTIVE, builtin_torque_policy="random")
