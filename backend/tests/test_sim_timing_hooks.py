"""Timing experiment hooks install cleanly and categories are populated."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SIM_TIMING = Path(__file__).resolve().parents[1] / "scripts" / "experiments" / "sim_timing"
if str(SIM_TIMING) not in sys.path:
    sys.path.insert(0, str(SIM_TIMING))

from _hooks import install, uninstall  # noqa: E402
from _profile_runner import run_instrumented_episode  # noqa: E402
from _timing_collector import TimingCollector  # noqa: E402


def test_hooks_install_uninstall_restore_stepper() -> None:
    import simulation.stepper as stepper_mod

    orig = stepper_mod.SimulationStepper.step
    collector = TimingCollector()
    install(collector)
    assert stepper_mod.SimulationStepper.step is not orig
    uninstall()
    assert stepper_mod.SimulationStepper.step is orig


def test_low_cloud_profile_populates_sensor_category() -> None:
    from _frozen_baseline import build_low_cloud_setup

    setup = build_low_cloud_setup()
    series, collector = run_instrumented_episode(setup)
    report = collector.report(top_n=7, extra={"scenario": "low_cloud"})
    assert series.camera_observation_line_codes.shape[0] > 0
    assert report["n_steps"] > 0
    assert report["steps_per_s"] > 0.0
    keys = {row["key"] for row in report["categories"]}
    assert "sensor_camera_rays" in keys
    assert len(report["top_7_consumers"]) <= 7
