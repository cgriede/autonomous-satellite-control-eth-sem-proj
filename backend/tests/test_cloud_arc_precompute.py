"""Parity: episode cloud-arc precompute matches per-timestep compute_cloud_arc_specs_at_time."""

from __future__ import annotations

import numpy as np
import pytest

from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from simulation.camera_2d import (
    cloud_arc_specs_list_for_frame,
    compute_cloud_arc_specs_at_time,
)
from simulation.run_simulation import run_simulation
from simulation.stepper_factory import build_stepper


def test_precompute_matches_per_timestep_specs() -> None:
    setup = build_setup(seed=0, include_cameras=True)
    resolved = setup.resolve(require_camera=False)
    stepper = build_stepper(
        resolved,
        simulation_config=SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast"),
    )
    n = int(stepper._t_s.shape[0])
    n_clouds = len(setup.clouds)
    assert n_clouds > 0

    for k in (0, n // 2, n - 1):
        ref = compute_cloud_arc_specs_at_time(
            sim_time_s=float(stepper._t_s[k]),
            sim_total_s=stepper._sim_total_s,
            earth_radius_km=stepper._earth_radius_km,
            clouds=setup.clouds,
        )
        cand = cloud_arc_specs_list_for_frame(
            radius_km=stepper._cloud_arc_radius_km,
            start_rad=stepper._cloud_arc_start_rad,
            end_rad=stepper._cloud_arc_end_rad,
            frame_idx=k,
        )
        assert len(ref) == len(cand) == n_clouds
        for r, c in zip(ref, cand):
            assert r["radius_km"] == pytest.approx(c["radius_km"])
            assert r["start_rad"] == pytest.approx(c["start_rad"])
            assert r["end_rad"] == pytest.approx(c["end_rad"])


def test_coast_episode_observation_codes_unchanged_with_precompute() -> None:
    setup = build_setup(seed=0, include_cameras=True)
    sim_cfg = SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast")
    series = run_simulation(setup=setup, simulation_config=sim_cfg)
    assert series.camera_observation_line_codes.shape[0] > 10
    assert np.any(series.camera_observation_line_codes != 0)
