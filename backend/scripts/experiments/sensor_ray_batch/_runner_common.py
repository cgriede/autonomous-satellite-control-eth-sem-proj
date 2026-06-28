"""Shared timing, parity checks, and fixed-contract JSON for sensor ray batch experiments."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
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
from simulation.sensor_kernel import SensorKernel, SensorTimestepResult

from _frozen_baseline import (
    build_baseline_sim_config,
    build_high_cloud_setup,
    build_low_cloud_setup,
)

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


def write_hypothesis_result(
    path: Path,
    *,
    experiment_id: str,
    hypothesis_id: str,
    phase: str,
    frozen_input: dict[str, Any],
    control: dict[str, Any] | None,
    treatment: dict[str, Any] | None,
    delta: dict[str, Any],
    parity: dict[str, Any],
    instrumentation: dict[str, Any],
    debug_examples: dict[str, Any],
    files_changed: list[str],
    verdict: str,
    closeout: str,
) -> None:
    payload = {
        "experiment_id": experiment_id,
        "hypothesis_id": hypothesis_id,
        "phase": phase,
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_input": frozen_input,
        "control": control,
        "treatment": treatment,
        "delta": delta,
        "parity": parity,
        "instrumentation": instrumentation,
        "debug_examples": debug_examples,
        "files_changed": files_changed,
        "verdict": verdict,
        "closeout": closeout,
    }
    write_result(path, payload)


def cloud_specs_for_setup(setup, *, sim_time_s: float = 20.0, sim_total_s: float = 200.0) -> list[dict[str, float]]:
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    return compute_cloud_arc_specs_at_time(
        sim_time_s=sim_time_s,
        sim_total_s=sim_total_s,
        earth_radius_km=earth_r,
        clouds=setup.clouds,
    )


def _patch_sensor_kernel_evaluate(eval_fn: Any):
    import simulation.sensor_kernel as sensor_kernel_mod

    original = sensor_kernel_mod.SensorKernel.evaluate
    sensor_kernel_mod.SensorKernel.evaluate = staticmethod(eval_fn)
    return sensor_kernel_mod, original


def run_coast_episode(
    setup,
    *,
    sensor_eval_fn: Any | None = None,
) -> dict[str, Any]:
    sim_cfg = build_baseline_sim_config()
    patch_ctx = None
    original = None
    if sensor_eval_fn is not None:
        patch_ctx, original = _patch_sensor_kernel_evaluate(sensor_eval_fn)

    try:
        started = time.perf_counter()
        series = run_simulation(setup=setup, simulation_config=sim_cfg)
        wall_time_s = time.perf_counter() - started
    finally:
        if patch_ctx is not None and original is not None:
            patch_ctx.SensorKernel.evaluate = original

    n_frames = int(series.camera_observation_line_codes.shape[0])
    steps_per_s = n_frames / max(wall_time_s, 1e-9)
    n_clouds = len(setup.clouds)

    sample_indices = np.linspace(0, max(n_frames - 1, 0), num=min(10, n_frames), dtype=int)
    ascii_lines = []
    for idx in sample_indices:
        primary = series.camera_observation_line_codes[int(idx)]
        secondary = series.secondary_camera_observation_line_codes[int(idx)]
        ascii_lines.append(
            {
                "frame": int(idx),
                "primary_ascii": observation_codes_to_ascii_line(primary),
                "secondary_ascii": observation_codes_to_ascii_line(secondary) if secondary.size else "",
                "cloud_blocked_fraction": float(series.camera_cloud_blocked_fraction[int(idx)]),
                "secondary_cloud_fraction": float(series.secondary_camera_cloud_blocked_fraction[int(idx)]),
            }
        )

    return {
        "wall_time_s": float(wall_time_s),
        "n_frames": n_frames,
        "steps_per_s": float(steps_per_s),
        "n_clouds": n_clouds,
        "debug_examples": {"observation_line_samples": ascii_lines},
    }


def _dual_camera_eval_kwargs(setup) -> dict[str, Any]:
    """Single-timestep SensorKernel kwargs for micro-benchmark snapshots."""
    from simulation.camera_2d import boresight_dir_for_mount

    resolved = setup.resolve()
    sat_xy = np.array([6800.0, 200.0], dtype=float)
    z_ang = 0.5
    bore = np.array([np.cos(z_ang), np.sin(z_ang)], dtype=float)
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    cloud_specs = cloud_specs_for_setup(setup, sim_time_s=12.0, sim_total_s=100.0)

    secondary_bore = None
    secondary_fov = None
    n_bins_secondary = 0
    if len(resolved.cameras) > 1:
        scnd = resolved.cameras[1]
        tilt = float(scnd.tilt_off_nadir.to(ureg.rad).magnitude)
        secondary_bore = boresight_dir_for_mount(z_ang, tilt)
        secondary_fov = float(scnd.camera.fov(axis="y").to(ureg.rad).magnitude)
        n_bins_secondary = int(resolved.secondary_camera_observation_line_n_bins)

    return dict(
        sat_pos_xy_km=sat_xy,
        boresight_dir_unit_xy=bore,
        altitude=resolved.altitude,
        earth_radius_km=earth_r,
        sim_time_s=12.0,
        sim_total_s=100.0,
        n_bins=int(SIMULATION.camera_observation_line_n_bins),
        n_clouds=len(setup.clouds),
        clouds=setup.clouds,
        camera_kernel_backend="accelerated",
        n_bins_secondary=n_bins_secondary,
        secondary_boresight_dir_unit_xy=secondary_bore,
        secondary_vertical_fov_rad=secondary_fov,
        target_areas=resolved.target_areas,
        _cloud_specs=cloud_specs,
    )


def bench_sensor_kernel_evaluate(
    *,
    sensor_eval_fn: Any,
    setup,
    n_iters: int = 200,
) -> dict[str, float]:
    """Micro-benchmark full SensorKernel.evaluate (strip + primary + secondary)."""
    kwargs = _dual_camera_eval_kwargs(setup)
    kwargs.pop("_cloud_specs", None)
    t0 = time.perf_counter()
    for _ in range(n_iters):
        sensor_eval_fn(**kwargs)
    total_s = time.perf_counter() - t0
    return {"total_s": float(total_s), "n_iters": n_iters, "per_call_s": total_s / max(n_iters, 1)}


def bench_sensor_kernels_legacy(
    *,
    camera_module: Any,
    cloud_arc_specs: list[dict[str, float]],
    n_iters: int = 200,
) -> dict[str, float]:
    """Micro-benchmark strip + primary line + secondary line (three separate calls)."""
    sat_xy = np.array([6800.0, 200.0], dtype=float)
    bore = np.array([-1.0, 0.0], dtype=float)
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    ray_samples = 96  # legacy simulate_camera_strip_2d benchmark only
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

    total_s = strip_s + primary_line_s + secondary_line_s
    return {
        "strip_s": float(strip_s),
        "primary_line_s": float(primary_line_s),
        "secondary_line_s": float(secondary_line_s),
        "total_s": float(total_s),
        "n_iters": n_iters,
        "per_call_s": total_s / max(n_iters, 1),
    }


def bench_line_python_vs_accelerated(
    *,
    camera_module: Any,
    cloud_arc_specs: list[dict[str, float]],
    iters_python: int = 5,
    iters_accelerated: int = 50,
) -> dict[str, float]:
    sat_xy = np.array([6800.0, 200.0], dtype=float)
    bore = np.array([-1.0, 0.0], dtype=float)
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    n_bins = int(SIMULATION.camera_observation_line_n_bins)
    kwargs = dict(
        sat_pos_xy_km=sat_xy,
        boresight_dir_unit_xy=bore,
        altitude=SATELLITE_ALTITUDE,
        earth_radius_km=earth_r,
        sim_time_s=20.0,
        sim_total_s=200.0,
        n_bins=n_bins,
        cloud_arc_specs=cloud_arc_specs,
    )
    py_s = acc_s = 0.0
    py_iters = acc_iters = 0
    for backend, n_iters in (("python", iters_python), ("accelerated", iters_accelerated)):
        t0 = time.perf_counter()
        for _ in range(n_iters):
            camera_module.simulate_camera_observation_line_1d(**kwargs, kernel_backend=backend)
        elapsed = time.perf_counter() - t0
        if backend == "python":
            py_s, py_iters = elapsed, n_iters
        else:
            acc_s, acc_iters = elapsed, n_iters
    py_per = py_s / py_iters
    acc_per = acc_s / acc_iters
    return {
        "python_iters": py_iters,
        "accelerated_iters": acc_iters,
        "n_clouds": len(cloud_arc_specs),
        "python_line_s_per_call": py_per,
        "accelerated_line_s_per_call": acc_per,
        "line_speedup_per_call": py_per / max(acc_per, 1e-9),
        "production_line_s_per_call": acc_per,
    }


def compare_sensor_results(
    ref: SensorTimestepResult,
    cand: SensorTimestepResult,
) -> dict[str, Any]:
    mismatches: dict[str, int] = {}
    if not np.array_equal(ref.camera_observation_line_codes, cand.camera_observation_line_codes):
        mismatches["camera_observation_line_codes"] = int(
            np.count_nonzero(ref.camera_observation_line_codes != cand.camera_observation_line_codes)
        )
    if not np.array_equal(ref.secondary_camera_observation_line_codes, cand.secondary_camera_observation_line_codes):
        mismatches["secondary_camera_observation_line_codes"] = int(
            np.count_nonzero(
                ref.secondary_camera_observation_line_codes != cand.secondary_camera_observation_line_codes
            )
        )
    if ref.camera_center_ray_observation_code != cand.camera_center_ray_observation_code:
        mismatches["camera_center_ray_observation_code"] = 1
    if ref.camera_center_first_hit_is_cloud != cand.camera_center_first_hit_is_cloud:
        mismatches["camera_center_first_hit_is_cloud"] = 1
    if not np.isclose(ref.camera_cloud_blocked_fraction, cand.camera_cloud_blocked_fraction, equal_nan=True):
        mismatches["camera_cloud_blocked_fraction"] = 1
    if not np.isclose(
        ref.secondary_camera_cloud_blocked_fraction,
        cand.secondary_camera_cloud_blocked_fraction,
        equal_nan=True,
    ):
        mismatches["secondary_camera_cloud_blocked_fraction"] = 1
    if not np.allclose(ref.camera_ground_center_xy_km, cand.camera_ground_center_xy_km, equal_nan=True):
        mismatches["camera_ground_center_xy_km"] = 1
    total = sum(mismatches.values())
    return {"total_mismatches": total, "parity_ok": total == 0, "field_mismatches": mismatches}


def check_sensor_parity(
    *,
    sensor_eval_fn: Any,
    setup,
    n_cases: int = 8,
) -> dict[str, Any]:
    kwargs_base = _dual_camera_eval_kwargs(setup)
    kwargs_base.pop("_cloud_specs", None)
    rng = np.random.default_rng(0)
    examples: list[dict[str, Any]] = []
    total_mismatches = 0

    for i in range(n_cases):
        sat_xy = np.array([6800.0 + 10.0 * i, 200.0 + 5.0 * i], dtype=float)
        z_ang = float(rng.uniform(-0.2, 0.2))
        bore = np.array([np.cos(z_ang), np.sin(z_ang)], dtype=float)
        kw = dict(kwargs_base)
        kw["sat_pos_xy_km"] = sat_xy
        kw["boresight_dir_unit_xy"] = bore
        kw["sim_time_s"] = float(5.0 + i * 3.0)
        if kw.get("secondary_boresight_dir_unit_xy") is not None:
            from simulation.camera_2d import boresight_dir_for_mount

            kw["secondary_boresight_dir_unit_xy"] = boresight_dir_for_mount(z_ang, 0.436)

        ref = SensorKernel.evaluate(**kw)
        cand = sensor_eval_fn(**kw)
        cmp = compare_sensor_results(ref, cand)
        total_mismatches += cmp["total_mismatches"]
        examples.append(
            {
                "case": i,
                "mismatches": cmp["total_mismatches"],
                "field_mismatches": cmp["field_mismatches"],
                "ref_primary_ascii": observation_codes_to_ascii_line(ref.camera_observation_line_codes),
                "cand_primary_ascii": observation_codes_to_ascii_line(cand.camera_observation_line_codes),
                "ref_cloud_blocked_fraction": float(ref.camera_cloud_blocked_fraction),
                "cand_cloud_blocked_fraction": float(cand.camera_cloud_blocked_fraction),
            }
        )

    return {
        "total_mismatches": total_mismatches,
        "parity_ok": total_mismatches == 0,
        "debug_examples": {"parity_cases": examples},
    }


def low_cloud_setup_and_specs():
    setup = build_low_cloud_setup()
    specs = cloud_specs_for_setup(setup)
    return setup, specs


def high_cloud_setup_and_specs():
    setup = build_high_cloud_setup()
    specs = cloud_specs_for_setup(setup)
    return setup, specs
