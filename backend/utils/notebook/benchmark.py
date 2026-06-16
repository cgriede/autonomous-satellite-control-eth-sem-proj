"""Notebook-level benchmark helpers for s01 mission baseline evaluation.

The coast benchmark combines two independent baseline knobs:
1. Coast controller (ZeroTorquePolicy): always 0 N·m reaction-wheel torque.
2. Nadir initialization: build_setup() sets sat_z_offset=0° so body +Z points at Earth center.

Use these to produce a deterministic reference episode for comparing RL/warmup runs.

Note: This module is a notebook utility. It must NOT be imported from mission profiles
or simulation core code (§I: coast benchmark helper lives here, not in mission profile).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from simulation.run_simulation import run_simulation
from simulation.state_types import SimulationStateSeries


@dataclass
class CoastBenchmarkKPIs:
    """Per-episode key performance indicators for a coast benchmark run."""
    seed: int
    total_steps: int
    mean_reward: float
    mean_cloud_blocked_fraction_primary: float
    mean_cloud_blocked_fraction_secondary: float
    target_visibility_rate: float
    initial_frame_center_ray_code: int
    sampled_altitude_km: float


def run_s01_coast_benchmark(
    *,
    seed: int = 0,
    show_progress: bool = True,
) -> tuple[SimulationStateSeries, CoastBenchmarkKPIs]:
    """Run a single s01 episode with the coast (zero-torque) controller and nadir init.

    Both benchmark knobs are active by default:
    - ``build_setup()`` sets ``sat_z_offset=0°`` (nadir initial attitude).
    - ``SimulationConfig(controller_mode="coast")`` outputs 0 N·m every step.

    Args:
        seed: Integer seed for altitude sampling. Different seeds explore the altitude range.
        show_progress: Show tqdm progress bar during the episode.

    Returns:
        ``(series, kpis)`` where ``series`` is the full ``SimulationStateSeries`` and
        ``kpis`` holds the computed benchmark metrics.
    """
    from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
    from environment_definition.constants.observation_codes import is_observation_target_code

    setup = build_setup(seed=seed, include_cameras=True)
    resolved = setup.resolve(require_camera=True)

    sim_cfg = SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast")

    from simulation.stepper_factory import build_stepper
    from simulation.stepper import run_baseline_rollout_from_stepper

    stepper = build_stepper(resolved, simulation_config=sim_cfg, require_camera=True)
    tau_max_nm = float(resolved.satellite.reaction_wheel_max_torque.to(ureg.N * ureg.m).magnitude)

    series = run_baseline_rollout_from_stepper(
        stepper,
        simulation_config=sim_cfg,
        tau_max_nm=tau_max_nm,
        show_progress=show_progress,
    )

    # Compute KPIs
    n = len(series.t_s)
    mean_reward = float(np.mean(series.simulation_reward))
    primary_cloud_fractions = series.camera_cloud_blocked_fraction
    valid_primary = primary_cloud_fractions[np.isfinite(primary_cloud_fractions)]
    mean_cloud_primary = float(np.mean(valid_primary)) if len(valid_primary) > 0 else 0.0
    mean_cloud_secondary = float(np.mean(series.secondary_camera_cloud_blocked_fraction))

    from environment_definition.constants.SIMULATION import OBSERVATION_EARTH

    center_codes = series.camera_center_ray_observation_code
    line_any_target = np.any(
        np.vectorize(is_observation_target_code)(series.camera_observation_line_codes),
        axis=1,
    )
    center_is_target = np.vectorize(is_observation_target_code)(center_codes)
    target_visible_frames = int(np.sum(center_is_target | line_any_target))
    target_visibility_rate = float(target_visible_frames / max(n, 1))

    k0_code = int(series.camera_center_ray_observation_code[0])
    alt_km = float(resolved.altitude.to(ureg.km).magnitude)

    kpis = CoastBenchmarkKPIs(
        seed=seed,
        total_steps=n - 1,
        mean_reward=mean_reward,
        mean_cloud_blocked_fraction_primary=mean_cloud_primary,
        mean_cloud_blocked_fraction_secondary=mean_cloud_secondary,
        target_visibility_rate=target_visibility_rate,
        initial_frame_center_ray_code=k0_code,
        sampled_altitude_km=alt_km,
    )
    return series, kpis


def print_coast_benchmark_kpis(kpis: CoastBenchmarkKPIs) -> None:
    """Print a formatted summary of coast benchmark KPIs."""
    print(f"Coast benchmark (seed={kpis.seed})")
    print(f"  Altitude:              {kpis.sampled_altitude_km:.1f} km")
    print(f"  Steps:                 {kpis.total_steps}")
    print(f"  Mean reward:           {kpis.mean_reward:.3f}")
    print(f"  Cloud blocked (prim):  {kpis.mean_cloud_blocked_fraction_primary:.3f}")
    print(f"  Cloud blocked (scnd):  {kpis.mean_cloud_blocked_fraction_secondary:.3f}")
    print(f"  Target visibility:     {kpis.target_visibility_rate:.3f}")
    print(f"  k=0 center-ray code:   {kpis.initial_frame_center_ray_code} (1=Earth, 3=target)")
