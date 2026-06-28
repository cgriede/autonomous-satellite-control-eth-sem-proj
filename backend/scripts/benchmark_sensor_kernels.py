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
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE_ALTITUDE
from simulation.camera_2d import (
    compute_cloud_arc_specs_at_time,
    simulate_camera_observation_line_1d,
    simulate_camera_strip_2d,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark sensor/camera kernel backends.")
    parser.add_argument("--iters", type=int, default=200)
    parser.add_argument("--n-bins", type=int, default=SIMULATION.camera_observation_line_n_bins)
    parser.add_argument("--ray-samples", type=int, default=96, help="strip_2d legacy benchmark only")
    parser.add_argument(
        "--use-baseline-clouds",
        action="store_true",
        help="Use s01 cloud_formation_generator baseline specs (5–6 clouds) instead of SIMULATION.clouds.",
    )
    return parser.parse_args()


def _cloud_specs(*, use_baseline: bool, sim_total: float) -> list[dict[str, float]]:
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    if use_baseline:
        import sys
        from pathlib import Path

        exp_root = Path(__file__).resolve().parent / "experiments" / "cloud_kernel_speed"
        if str(exp_root) not in sys.path:
            sys.path.insert(0, str(exp_root))
        from _frozen_baseline import build_baseline_setup  # noqa: WPS433

        setup = build_baseline_setup()
        return compute_cloud_arc_specs_at_time(
            sim_time_s=20.0,
            sim_total_s=sim_total,
            earth_radius_km=earth_r,
            clouds=setup.clouds,
        )
    return compute_cloud_arc_specs_at_time(
        sim_time_s=20.0,
        sim_total_s=sim_total,
        earth_radius_km=earth_r,
    )


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


def _bench_line(*, backend: str, iters: int, n_bins: int, use_baseline_clouds: bool) -> float:
    sat_xy = np.array([6800.0, 200.0], dtype=float)
    bore = np.array([-1.0, 0.0], dtype=float)
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    cloud_specs = _cloud_specs(use_baseline=use_baseline_clouds, sim_total=float(iters))
    started = time.perf_counter()
    for i in range(iters):
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
    cloud_specs = _cloud_specs(use_baseline=args.use_baseline_clouds, sim_total=float(args.iters))
    print(f"cloud_count={len(cloud_specs)}")
    for backend in ("python", "accelerated"):
        strip_t = _bench_strip(backend=backend, iters=args.iters, ray_samples=args.ray_samples)
        line_t = _bench_line(
            backend=backend,
            iters=args.iters,
            n_bins=args.n_bins,
            use_baseline_clouds=args.use_baseline_clouds,
        )
        print(
            f"[{backend}] strip={strip_t:.4f}s line={line_t:.4f}s total={strip_t + line_t:.4f}s"
        )


if __name__ == "__main__":
    main()
