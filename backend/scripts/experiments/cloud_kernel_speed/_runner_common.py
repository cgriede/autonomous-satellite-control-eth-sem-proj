"""Shared timing, parity checks, and JSON output for cloud kernel experiments."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from environment_definition.constants import EARTH_RADIUS, SIMULATION, UREG as ureg
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE_ALTITUDE
from simulation.camera_2d import compute_cloud_arc_specs_at_time, observation_codes_to_ascii_line
from simulation.run_simulation import run_simulation

from _frozen_baseline import build_baseline_sim_config, build_baseline_setup

EXPERIMENT_ROOT = Path(__file__).resolve().parent
RESULTS_DIR = EXPERIMENT_ROOT / "results"


def _json_default(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Not JSON serializable: {type(obj)}")


def write_result(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")


def run_coast_episode(*, camera_module: Any | None = None) -> dict[str, Any]:
    """Run full baseline coast episode; optionally patch camera_2d module."""
    setup = build_baseline_setup()
    sim_cfg = build_baseline_sim_config()

    if camera_module is not None:
        import simulation.sensor_kernel as sensor_kernel_mod

        original = sensor_kernel_mod.simulate_camera_strip_2d, sensor_kernel_mod.simulate_camera_observation_line_1d
        sensor_kernel_mod.simulate_camera_strip_2d = camera_module.simulate_camera_strip_2d
        sensor_kernel_mod.simulate_camera_observation_line_1d = camera_module.simulate_camera_observation_line_1d
        try:
            started = time.perf_counter()
            series = run_simulation(setup=setup, simulation_config=sim_cfg)
            wall_time_s = time.perf_counter() - started
        finally:
            sensor_kernel_mod.simulate_camera_strip_2d, sensor_kernel_mod.simulate_camera_observation_line_1d = original
    else:
        started = time.perf_counter()
        series = run_simulation(setup=setup, simulation_config=sim_cfg)
        wall_time_s = time.perf_counter() - started

    n_frames = int(series.camera_observation_line_codes.shape[0])
    steps_per_s = n_frames / max(wall_time_s, 1e-9)
    n_clouds = len(setup.clouds)

    sample_indices = np.linspace(0, max(n_frames - 1, 0), num=min(10, n_frames), dtype=int)
    ascii_lines = []
    for idx in sample_indices:
        primary = series.camera_observation_line_codes[int(idx)]
        ascii_lines.append(
            {
                "frame": int(idx),
                "primary_ascii": observation_codes_to_ascii_line(primary),
                "cloud_blocked_fraction": float(series.camera_cloud_blocked_fraction[int(idx)]),
            }
        )

    return {
        "wall_time_s": float(wall_time_s),
        "n_frames": n_frames,
        "steps_per_s": float(steps_per_s),
        "n_clouds": n_clouds,
        "debug_examples": {"observation_line_samples": ascii_lines},
    }


def bench_sensor_kernels(
    *,
    camera_module: Any,
    cloud_arc_specs: list[dict[str, float]],
    n_iters: int = 200,
) -> dict[str, float]:
    """Micro-benchmark strip + primary line + secondary line."""
    sat_xy = np.array([6800.0, 200.0], dtype=float)
    bore = np.array([-1.0, 0.0], dtype=float)
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    ray_samples = int(SIMULATION.camera_pixel_ray_samples)
    n_bins = int(SIMULATION.camera_observation_line_n_bins)
    n_bins_secondary = 200

    t0 = time.perf_counter()
    for _ in range(n_iters):
        camera_module.simulate_camera_strip_2d(
            sat_pos_xy_km=sat_xy,
            boresight_dir_unit_xy=bore,
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=earth_r,
            sim_time_s=12.0,
            sim_total_s=100.0,
            pixel_ray_samples=ray_samples,
            kernel_backend="accelerated",
            cloud_arc_specs=cloud_arc_specs,
        )
    strip_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(n_iters):
        camera_module.simulate_camera_observation_line_1d(
            sat_pos_xy_km=sat_xy,
            boresight_dir_unit_xy=bore,
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=earth_r,
            sim_time_s=12.0,
            sim_total_s=100.0,
            n_bins=n_bins,
            cloud_arc_specs=cloud_arc_specs,
            kernel_backend="accelerated",
        )
    primary_line_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(n_iters):
        camera_module.simulate_camera_observation_line_1d(
            sat_pos_xy_km=sat_xy,
            boresight_dir_unit_xy=bore,
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=earth_r,
            sim_time_s=12.0,
            sim_total_s=100.0,
            n_bins=n_bins_secondary,
            cloud_arc_specs=cloud_arc_specs,
            kernel_backend="accelerated",
        )
    secondary_line_s = time.perf_counter() - t0

    return {
        "strip_s": float(strip_s),
        "primary_line_s": float(primary_line_s),
        "secondary_line_s": float(secondary_line_s),
        "total_s": float(strip_s + primary_line_s + secondary_line_s),
        "n_iters": n_iters,
    }


def check_observation_line_parity(
    *,
    camera_module: Any,
    cloud_arc_specs: list[dict[str, float]],
) -> dict[str, Any]:
    """Compare accelerated vs python observation line on fixed snapshots."""
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    cases = [
        {
            "name": "nadir_6clouds",
            "sat_xy": np.array([6800.0, 120.0], dtype=float),
            "bore": np.array([-1.0, 0.02], dtype=float),
            "n_bins": 80,
            "sim_time_s": 20.0,
            "sim_total_s": 200.0,
        },
        {
            "name": "off_nadir",
            "sat_xy": np.array([6800.0, 200.0], dtype=float),
            "bore": np.array([-1.0, 0.0], dtype=float),
            "n_bins": 100,
            "sim_time_s": 12.0,
            "sim_total_s": 100.0,
        },
    ]
    total_mismatches = 0
    examples: list[dict[str, Any]] = []

    for case in cases:
        kwargs = dict(
            sat_pos_xy_km=case["sat_xy"],
            boresight_dir_unit_xy=case["bore"],
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=earth_r,
            sim_time_s=case["sim_time_s"],
            sim_total_s=case["sim_total_s"],
            n_bins=case["n_bins"],
            cloud_arc_specs=cloud_arc_specs,
        )
        py = camera_module.simulate_camera_observation_line_1d(**kwargs, kernel_backend="python")
        acc = camera_module.simulate_camera_observation_line_1d(**kwargs, kernel_backend="accelerated")
        mismatches = int(np.count_nonzero(py.observation_types != acc.observation_types))
        total_mismatches += mismatches
        examples.append(
            {
                "case": case["name"],
                "mismatches": mismatches,
                "python_ascii": observation_codes_to_ascii_line(py.observation_types),
                "accelerated_ascii": observation_codes_to_ascii_line(acc.observation_types),
            }
        )

    return {
        "total_mismatches": total_mismatches,
        "parity_ok": total_mismatches == 0,
        "debug_examples": {"parity_cases": examples},
    }


def baseline_cloud_specs() -> list[dict[str, float]]:
    setup = build_baseline_setup()
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    return compute_cloud_arc_specs_at_time(
        sim_time_s=20.0,
        sim_total_s=200.0,
        earth_radius_km=earth_r,
        clouds=setup.clouds,
    )
