from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import numpy as np

from environment_definition.constants import EARTH_RADIUS, SIMULATION, UREG as ureg
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE_ALTITUDE
from simulation.camera_2d import (
    compute_cloud_arc_specs_at_time,
    simulate_camera_observation_line_1d,
    simulate_camera_strip_2d,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark sensor/camera kernel backends.")
    parser.add_argument("--iters", type=int, default=200)
    parser.add_argument("--n-bins", type=int, default=SIMULATION.camera_observation_line_n_bins)
    parser.add_argument("--ray-samples", type=int, default=SIMULATION.camera_pixel_ray_samples)
    return parser.parse_args()


def _bench_strip(*, backend: str, iters: int, ray_samples: int) -> float:
    sat_xy = np.array([6800.0, 200.0], dtype=float)
    bore = np.array([-1.0, 0.0], dtype=float)
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    started = time.perf_counter()
    for i in range(iters):
        simulate_camera_strip_2d(
            sat_pos_xy_km=sat_xy,
            boresight_dir_unit_xy=bore,
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=earth_r,
            sim_time_s=float(i),
            sim_total_s=float(iters),
            pixel_ray_samples=ray_samples,
            kernel_backend=backend,
        )
    return time.perf_counter() - started


def _bench_line(*, backend: str, iters: int, n_bins: int) -> float:
    sat_xy = np.array([6800.0, 200.0], dtype=float)
    bore = np.array([-1.0, 0.0], dtype=float)
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    started = time.perf_counter()
    for i in range(iters):
        cloud_specs = compute_cloud_arc_specs_at_time(
            sim_time_s=float(i),
            sim_total_s=float(iters),
            earth_radius_km=earth_r,
        )
        simulate_camera_observation_line_1d(
            sat_pos_xy_km=sat_xy,
            boresight_dir_unit_xy=bore,
            altitude=SATELLITE_ALTITUDE,
            earth_radius_km=earth_r,
            sim_time_s=float(i),
            sim_total_s=float(iters),
            n_bins=int(n_bins),
            cloud_arc_specs=cloud_specs,
            kernel_backend=backend,
        )
    return time.perf_counter() - started


def main() -> None:
    args = parse_args()
    for backend in ("python", "accelerated"):
        strip_t = _bench_strip(backend=backend, iters=args.iters, ray_samples=args.ray_samples)
        line_t = _bench_line(
            backend=backend,
            iters=args.iters,
            n_bins=args.n_bins,
        )
        print(
            f"[{backend}] strip={strip_t:.4f}s line={line_t:.4f}s total={strip_t + line_t:.4f}s"
        )


if __name__ == "__main__":
    main()
