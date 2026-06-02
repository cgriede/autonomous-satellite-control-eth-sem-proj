"""Benchmark optimized kernel with notebook-scale cloud counts (50–200)."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

import numpy as np

from environment_definition.constants import EARTH_RADIUS, SIMULATION, UREG as ureg
from environment_definition.constants.SIMULATION import GeodeticLonLat, RenderMode, SimulationConfig
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE_ALTITUDE
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from simulation.camera_2d import compute_cloud_arc_specs_at_time, simulate_camera_observation_line_1d
from simulation.run_simulation import run_simulation
import cloud_fov_cull as cloud_fov_cull_mod
from cloud_fov_cull import filter_cloud_specs_for_camera_fov

_S01_DIR = BACKEND_DIR / "notebooks" / "s01"
if str(_S01_DIR) not in sys.path:
    sys.path.insert(0, str(_S01_DIR))

from s01_utils.cloud_formation import cloud_formation_generator  # noqa: E402

from _runner_common import bench_sensor_kernels, write_result  # noqa: E402

# Match backend/notebooks/s01/02-clouds.ipynb params cell
NOTEBOOK_CLOUD_NUMBER_BOUNDS = (50, 200)
NOTEBOOK_CLOUD_RANGE_BOUNDS = (1, 100) * ureg.km
NOTEBOOK_CLOUD_BASE_BOUNDS = (4, 12) * ureg.km
NOTEBOOK_CLOUD_THICKNESS_BOUNDS = (1, 16) * ureg.km
NOTEBOOK_MAX_TOP = 20 * ureg.km
NOTEBOOK_RNG = np.random.default_rng(42)


def build_notebook_setup():
    clouds = cloud_formation_generator(
        formation_start=GeodeticLonLat(lat=75.0 * ureg.deg, lon=0.0 * ureg.deg),
        formation_end=GeodeticLonLat(lat=75.0 * ureg.deg, lon=180.0 * ureg.deg),
        cloud_base_altitude_bounds=NOTEBOOK_CLOUD_BASE_BOUNDS,
        cloud_thickness_bounds=NOTEBOOK_CLOUD_THICKNESS_BOUNDS,
        cloud_range_bounds=NOTEBOOK_CLOUD_RANGE_BOUNDS,
        cloud_number_bounds=NOTEBOOK_CLOUD_NUMBER_BOUNDS,
        max_top_altitude=NOTEBOOK_MAX_TOP,
        rng=NOTEBOOK_RNG,
    )
    return replace(build_setup(seed=0, include_cameras=True), clouds=tuple(clouds)), clouds


def run_episode(*, cull_enabled: bool) -> dict:
    prev = cloud_fov_cull_mod.CLOUD_FOV_CULL_ENABLED
    cloud_fov_cull_mod.CLOUD_FOV_CULL_ENABLED = cull_enabled
    setup, clouds = build_notebook_setup()
    sim_cfg = SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast")
    try:
        t0 = time.perf_counter()
        series = run_simulation(setup=setup, simulation_config=sim_cfg)
        wall = time.perf_counter() - t0
    finally:
        cloud_fov_cull_mod.CLOUD_FOV_CULL_ENABLED = prev
    n = int(series.camera_observation_line_codes.shape[0])
    return {
        "wall_time_s": wall,
        "n_frames": n,
        "steps_per_s": n / max(wall, 1e-9),
        "n_clouds": len(clouds),
        "cull_enabled": cull_enabled,
    }


def sample_cull_stats(clouds: tuple, *, n_samples: int = 200) -> dict:
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    specs = compute_cloud_arc_specs_at_time(
        sim_time_s=100.0,
        sim_total_s=500.0,
        earth_radius_km=earth_r,
        clouds=clouds,
    )
    sat_xy = np.array([6800.0, 200.0], dtype=float)
    bore = np.array([-1.0, 0.0], dtype=float)
    n_bins = int(SIMULATION.camera_observation_line_n_bins)
    half_fov = 0.05
    angles = np.linspace(-half_fov, half_fov, n_bins)
    cos_a, sin_a = np.cos(angles), np.sin(angles)
    x, y = float(bore[0]), float(bore[1])
    ray_dirs = np.stack([cos_a * x - sin_a * y, sin_a * x + cos_a * y], axis=1)

    total_culled = 0
    t0 = time.perf_counter()
    for _ in range(n_samples):
        _, stats = filter_cloud_specs_for_camera_fov(sat_xy, ray_dirs, specs)
        total_culled += int(stats["clouds_culled"])
    overhead_us = (time.perf_counter() - t0) / n_samples * 1e6
    return {
        "clouds_total": len(specs),
        "mean_clouds_culled_per_call": total_culled / n_samples,
        "mean_clouds_kept_per_call": len(specs) - total_culled / n_samples,
        "cull_overhead_us_per_call": overhead_us,
    }


def bench_line_python_vs_accelerated(clouds: tuple, *, iters_python: int = 5, iters_accelerated: int = 50) -> dict:
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    specs = compute_cloud_arc_specs_at_time(
        sim_time_s=20.0,
        sim_total_s=200.0,
        earth_radius_km=earth_r,
        clouds=clouds,
    )
    sat_xy = np.array([6800.0, 200.0], dtype=float)
    bore = np.array([-1.0, 0.0], dtype=float)
    n_bins = int(SIMULATION.camera_observation_line_n_bins)
    kwargs = dict(
        sat_pos_xy_km=sat_xy,
        boresight_dir_unit_xy=bore,
        altitude=SATELLITE_ALTITUDE,
        earth_radius_km=earth_r,
        sim_time_s=20.0,
        sim_total_s=200.0,
        n_bins=n_bins,
        cloud_arc_specs=specs,
    )
    for backend, n_iters in (("python", iters_python), ("accelerated", iters_accelerated)):
        t0 = time.perf_counter()
        for _ in range(n_iters):
            simulate_camera_observation_line_1d(**kwargs, kernel_backend=backend)
        elapsed = time.perf_counter() - t0
        if backend == "python":
            py_s = elapsed
            py_iters = n_iters
        else:
            acc_s = elapsed
            acc_iters = n_iters
    py_per = py_s / py_iters
    acc_per = acc_s / acc_iters
    return {
        "python_iters": py_iters,
        "accelerated_iters": acc_iters,
        "n_clouds": len(clouds),
        "python_line_s_total": py_s,
        "accelerated_line_s_total": acc_s,
        "python_line_s_per_call": py_per,
        "accelerated_line_s_per_call": acc_per,
        "line_speedup_per_call": py_per / max(acc_per, 1e-9),
    }


def main() -> None:
    setup, clouds = build_notebook_setup()
    print(f"n_clouds={len(clouds)}")

    ep_cull_on = run_episode(cull_enabled=True)
    ep_cull_off = run_episode(cull_enabled=False)
    cull_stats = sample_cull_stats(clouds)
    line_bench = bench_line_python_vs_accelerated(clouds)
    specs = compute_cloud_arc_specs_at_time(
        sim_time_s=20.0,
        sim_total_s=200.0,
        earth_radius_km=float(EARTH_RADIUS.to(ureg.km).magnitude),
        clouds=clouds,
    )
    import simulation.camera_2d as camera_2d

    micro = bench_sensor_kernels(camera_module=camera_2d, cloud_arc_specs=specs, n_iters=50)

    payload = {
        "experiment_id": "high_cloud_notebook",
        "cloud_number_bounds": list(NOTEBOOK_CLOUD_NUMBER_BOUNDS),
        "stats": {
            "n_clouds": len(clouds),
            "episode_cull_on": ep_cull_on,
            "episode_cull_off": ep_cull_off,
            "episode_speedup_cull_vs_no_cull": ep_cull_off["wall_time_s"] / max(ep_cull_on["wall_time_s"], 1e-9),
            "cull_stats_sampled": cull_stats,
            "line_benchmark": line_bench,
            "micro_benchmark_accelerated": micro,
        },
    }
    out = EXPERIMENT_ROOT / "results" / "high_cloud_notebook.json"
    write_result(out, payload)
    print(json.dumps(payload["stats"], indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
