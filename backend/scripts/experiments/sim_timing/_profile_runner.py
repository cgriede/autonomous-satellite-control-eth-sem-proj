"""Instrumented coast rollout + optional render/export timing."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

EXPERIMENT_ROOT = Path(__file__).resolve().parent
SENSOR_RAY_BATCH = EXPERIMENT_ROOT.parent / "sensor_ray_batch"
if str(SENSOR_RAY_BATCH) not in sys.path:
    sys.path.insert(0, str(SENSOR_RAY_BATCH))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

from environment_definition.constants.SIMULATION import SimulationConfig
from simulation.stepper_factory import build_stepper

from _hooks import install, install_render_hooks, uninstall
from _timing_collector import TimingCollector

from _timing_fixtures import (  # noqa: E402
    build_baseline_sim_config,
    build_high_cloud_setup,
    build_low_cloud_setup,
    build_sat_sim_interactive_setup,
    build_sat_sim_interactive_sim_config,
)


def run_instrumented_episode(
    setup,
    *,
    simulation_config: SimulationConfig | None = None,
    show_progress: bool = False,
) -> tuple[Any, TimingCollector]:
    """Run controller rollout with timing hooks; returns (SimulationStateSeries, collector)."""
    sim_cfg = simulation_config or build_baseline_sim_config()
    resolved = setup.resolve(require_camera=False)
    collector = TimingCollector()

    install(collector)
    try:
        stepper = build_stepper(resolved, simulation_config=sim_cfg)
        tau_max_nm = float(
            resolved.satellite.reaction_wheel_max_torque
            .to(resolved.ureg.N * resolved.ureg.m)
            .magnitude
        )

        from simulation.stepper import _build_simulation_controller

        controller = _build_simulation_controller(
            controller_mode=str(sim_cfg.controller_mode),
            tau_max_nm=tau_max_nm,
            dt=stepper._dt,
            rng=np.random.default_rng(sim_cfg.controller_seed),
        )
        controller_obs = np.zeros(1, dtype=np.float64)
        torque_cmd_nm = 0.0
        total_steps = max(0, int(stepper._t_s.shape[0]) - 1)

        loop_t0 = time.perf_counter()
        for _ in range(total_steps):
            if stepper.done:
                break
            if stepper.should_update_controller():
                t_ctrl = time.perf_counter()
                action = controller.get_action(controller_obs, train=False)
                collector.add("controller_actuator", time.perf_counter() - t_ctrl)
                torque_cmd_nm = float(np.asarray(action, dtype=np.float64).reshape(-1)[0])
            stepper.step(wheel_torque_cmd_nm=torque_cmd_nm)

        collector.sim_loop_wall_s = time.perf_counter() - loop_t0
        series = stepper.finalize_series()
    finally:
        uninstall()

    return series, collector


def run_instrumented_with_render(
    setup,
    *,
    out_path: Path,
    simulation_config: SimulationConfig | None = None,
) -> TimingCollector:
    """Sim + render/export with shared collector."""
    series, collector = run_instrumented_episode(
        setup,
        simulation_config=simulation_config,
        show_progress=False,
    )

    install_render_hooks(collector)
    try:
        from environment_definition.constants.SIMULATION import RenderMode
        from render.render_main import render_from_series

        out_path.parent.mkdir(parents=True, exist_ok=True)
        render_from_series(
            simulation_series=series,
            render_mode=RenderMode.EXPORT,
            output_path=out_path,
        )
    finally:
        uninstall()

    return collector


def profile_scenario(scenario: str, *, with_render: bool = False) -> dict[str, Any]:
    if scenario == "low_cloud":
        setup = build_low_cloud_setup()
        sim_cfg = build_baseline_sim_config()
    elif scenario == "high_cloud":
        setup = build_high_cloud_setup()
        sim_cfg = build_baseline_sim_config()
    elif scenario == "sat_sim_interactive":
        setup = build_sat_sim_interactive_setup()
        sim_cfg = build_sat_sim_interactive_sim_config()
    else:
        raise ValueError(f"Unknown scenario: {scenario!r}")

    n_clouds = len(setup.clouds)
    context = {
        "scenario": scenario,
        "n_clouds": n_clouds,
        "with_render": with_render,
        "include_cameras": len(setup.cameras) > 0,
        "controller_mode": str(sim_cfg.controller_mode),
    }

    if with_render:
        out_path = EXPERIMENT_ROOT / "results" / f"{scenario}_preview.mp4"
        collector = run_instrumented_with_render(setup, out_path=out_path, simulation_config=sim_cfg)
    else:
        _, collector = run_instrumented_episode(setup, simulation_config=sim_cfg)
        collector = collector

    return collector.report(top_n=7, extra=context)
