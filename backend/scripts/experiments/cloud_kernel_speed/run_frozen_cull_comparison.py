"""Fair cull ON vs OFF comparison on one frozen cloud list (>= 100 clouds)."""

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

from environment_definition.constants.SIMULATION import GeodeticLonLat, RenderMode, SimulationConfig
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from simulation.run_simulation import run_simulation
import cloud_fov_cull as cloud_fov_cull_mod

_S01_DIR = BACKEND_DIR / "notebooks" / "s01"
if str(_S01_DIR) not in sys.path:
    sys.path.insert(0, str(_S01_DIR))

from s01_utils.cloud_formation import cloud_formation_generator  # noqa: E402

from _runner_common import write_result  # noqa: E402

# Notebook-like params; count lower bound >= 100 for this benchmark.
FROZEN_CLOUD_NUMBER_BOUNDS = (100, 200)
FROZEN_RNG_SEED = 42
FROZEN_CLOUDS: tuple | None = None

_original_filter = cloud_fov_cull_mod.filter_cloud_specs_for_camera_fov
_cull_telemetry: dict[str, float] = {}


def _reset_cull_telemetry() -> None:
    _cull_telemetry.clear()
    _cull_telemetry.update({"calls": 0.0, "clouds_total_sum": 0.0, "clouds_culled_sum": 0.0})


def _install_counting_filter() -> None:
    def _counting_filter(*args, **kwargs):
        kept, stats = _original_filter(*args, **kwargs)
        _cull_telemetry["calls"] += 1.0
        _cull_telemetry["clouds_total_sum"] += float(stats["clouds_total"])
        _cull_telemetry["clouds_culled_sum"] += float(stats["clouds_culled"])
        return kept, stats

    cloud_fov_cull_mod.filter_cloud_specs_for_camera_fov = _counting_filter  # type: ignore[assignment]


def _restore_filter() -> None:
    cloud_fov_cull_mod.filter_cloud_specs_for_camera_fov = _original_filter  # type: ignore[assignment]


def generate_frozen_clouds() -> tuple:
    global FROZEN_CLOUDS
    if FROZEN_CLOUDS is not None:
        return FROZEN_CLOUDS
    clouds = cloud_formation_generator(
        formation_start=GeodeticLonLat(lat=75.0 * ureg.deg, lon=0.0 * ureg.deg),
        formation_end=GeodeticLonLat(lat=75.0 * ureg.deg, lon=180.0 * ureg.deg),
        cloud_base_altitude_bounds=(4, 12) * ureg.km,
        cloud_thickness_bounds=(1, 16) * ureg.km,
        cloud_range_bounds=(1, 100) * ureg.km,
        cloud_number_bounds=FROZEN_CLOUD_NUMBER_BOUNDS,
        max_top_altitude=20 * ureg.km,
        rng=np.random.default_rng(FROZEN_RNG_SEED),
    )
    if len(clouds) < 100:
        raise RuntimeError(f"Expected >= 100 clouds, got {len(clouds)}")
    FROZEN_CLOUDS = tuple(clouds)
    return FROZEN_CLOUDS


def build_frozen_setup():
    clouds = generate_frozen_clouds()
    return replace(build_setup(seed=0, include_cameras=True), clouds=clouds)


def run_episode(*, cull_enabled: bool) -> dict:
    prev_enabled = cloud_fov_cull_mod.CLOUD_FOV_CULL_ENABLED
    cloud_fov_cull_mod.CLOUD_FOV_CULL_ENABLED = cull_enabled
    _reset_cull_telemetry()
    _install_counting_filter()
    setup = build_frozen_setup()
    sim_cfg = SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast")
    try:
        t0 = time.perf_counter()
        series = run_simulation(setup=setup, simulation_config=sim_cfg)
        wall = time.perf_counter() - t0
    finally:
        _restore_filter()
        cloud_fov_cull_mod.CLOUD_FOV_CULL_ENABLED = prev_enabled

    n = int(series.camera_observation_line_codes.shape[0])
    calls = int(_cull_telemetry["calls"])
    culled_sum = float(_cull_telemetry["clouds_culled_sum"])
    total_sum = float(_cull_telemetry["clouds_total_sum"])
    return {
        "wall_time_s": wall,
        "n_frames": n,
        "steps_per_s": n / max(wall, 1e-9),
        "n_clouds": len(setup.clouds),
        "cull_enabled": cull_enabled,
        "cull_calls": calls,
        "mean_clouds_culled_per_call": culled_sum / max(calls, 1),
        "mean_clouds_total_per_call": total_sum / max(calls, 1),
        "fraction_clouds_culled_per_call": culled_sum / max(total_sum, 1.0),
    }


def main() -> None:
    clouds = generate_frozen_clouds()
    print(f"Frozen cloud count={len(clouds)} (bounds={FROZEN_CLOUD_NUMBER_BOUNDS}, seed={FROZEN_RNG_SEED})")

    print("Running coast episode with cull ON ...")
    ep_cull_on = run_episode(cull_enabled=True)
    print(f"  wall_time_s={ep_cull_on['wall_time_s']:.2f} steps_per_s={ep_cull_on['steps_per_s']:.1f}")

    print("Running coast episode with cull OFF (same frozen clouds) ...")
    ep_cull_off = run_episode(cull_enabled=False)
    print(f"  wall_time_s={ep_cull_off['wall_time_s']:.2f} steps_per_s={ep_cull_off['steps_per_s']:.1f}")

    speedup = ep_cull_off["wall_time_s"] / max(ep_cull_on["wall_time_s"], 1e-9)
    delta_s = ep_cull_off["wall_time_s"] - ep_cull_on["wall_time_s"]
    delta_pct = 100.0 * delta_s / max(ep_cull_off["wall_time_s"], 1e-9)

    payload = {
        "experiment_id": "frozen_cull_comparison",
        "cloud_number_bounds": list(FROZEN_CLOUD_NUMBER_BOUNDS),
        "rng_seed": FROZEN_RNG_SEED,
        "stats": {
            "n_clouds_frozen": len(clouds),
            "episode_cull_on": ep_cull_on,
            "episode_cull_off": ep_cull_off,
            "cull_faster_by_factor": speedup,
            "cull_saves_wall_time_s": delta_s,
            "cull_saves_wall_time_pct": delta_pct,
        },
    }
    out = EXPERIMENT_ROOT / "results" / "frozen_cull_comparison.json"
    write_result(out, payload)
    print(json.dumps(payload["stats"], indent=2))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
