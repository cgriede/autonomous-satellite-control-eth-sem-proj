"""Frozen baseline fixtures for sensor ray batch hypothesis experiments."""

from __future__ import annotations

import pickle
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

from environment_definition.constants.SIMULATION import GeodeticLonLat, RenderMode, SimulationConfig
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup

_S01_DIR = Path(__file__).resolve().parents[3] / "notebooks" / "s01"
if str(_S01_DIR) not in sys.path:
    sys.path.insert(0, str(_S01_DIR))

from s01_utils.cloud_formation import cloud_formation_generator  # noqa: E402

EXPERIMENT_ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = EXPERIMENT_ROOT / "fixtures"
HIGH_CLOUD_FIXTURE = FIXTURES_DIR / "high_cloud_seed42.pkl"

BASELINE_SEED = 0
BASELINE_RNG = np.random.default_rng(42)
HIGH_CLOUD_RNG = np.random.default_rng(42)

# low_cloud_dual — parity + episode speed (matches cloud_kernel_speed frozen baseline)
LOW_CLOUD_NUMBER_BOUNDS = (5, 6)
LOW_CLOUD_RANGE_BOUNDS = (10, 50) * ureg.km
LOW_CLOUD_BASE_BOUNDS = (4, 12) * ureg.km
LOW_CLOUD_THICKNESS_BOUNDS = (1, 16) * ureg.km
LOW_MAX_TOP = 20 * ureg.km

# high_cloud_notebook — matches 02-clouds.ipynb / run_high_cloud_benchmark.py
HIGH_CLOUD_NUMBER_BOUNDS = (50, 200)
HIGH_CLOUD_RANGE_BOUNDS = (1, 100) * ureg.km
HIGH_CLOUD_BASE_BOUNDS = (4, 12) * ureg.km
HIGH_CLOUD_THICKNESS_BOUNDS = (1, 16) * ureg.km
HIGH_MAX_TOP = 20 * ureg.km

FORMATION_START = GeodeticLonLat(lat=75.0 * ureg.deg, lon=0.0 * ureg.deg)
FORMATION_END = GeodeticLonLat(lat=75.0 * ureg.deg, lon=180.0 * ureg.deg)


def build_low_cloud_clouds() -> tuple:
    return tuple(
        cloud_formation_generator(
            formation_start=FORMATION_START,
            formation_end=FORMATION_END,
            cloud_base_altitude_bounds=LOW_CLOUD_BASE_BOUNDS,
            cloud_thickness_bounds=LOW_CLOUD_THICKNESS_BOUNDS,
            cloud_range_bounds=LOW_CLOUD_RANGE_BOUNDS,
            cloud_number_bounds=LOW_CLOUD_NUMBER_BOUNDS,
            max_top_altitude=LOW_MAX_TOP,
            rng=BASELINE_RNG,
        )
    )


def build_low_cloud_setup():
    clouds = build_low_cloud_clouds()
    return replace(build_setup(seed=BASELINE_SEED, include_cameras=True), clouds=clouds)


def _generate_high_cloud_clouds() -> tuple:
    return tuple(
        cloud_formation_generator(
            formation_start=FORMATION_START,
            formation_end=FORMATION_END,
            cloud_base_altitude_bounds=HIGH_CLOUD_BASE_BOUNDS,
            cloud_thickness_bounds=HIGH_CLOUD_THICKNESS_BOUNDS,
            cloud_range_bounds=HIGH_CLOUD_RANGE_BOUNDS,
            cloud_number_bounds=HIGH_CLOUD_NUMBER_BOUNDS,
            max_top_altitude=HIGH_MAX_TOP,
            rng=HIGH_CLOUD_RNG,
        )
    )


def load_high_cloud_clouds() -> tuple:
    """Load or create frozen high-cloud tuple (identical across control/treatment)."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    if HIGH_CLOUD_FIXTURE.is_file():
        with HIGH_CLOUD_FIXTURE.open("rb") as fh:
            return pickle.load(fh)
    clouds = _generate_high_cloud_clouds()
    with HIGH_CLOUD_FIXTURE.open("wb") as fh:
        pickle.dump(clouds, fh)
    return clouds


def build_high_cloud_setup():
    clouds = load_high_cloud_clouds()
    return replace(build_setup(seed=BASELINE_SEED, include_cameras=True), clouds=clouds)


def build_baseline_sim_config() -> SimulationConfig:
    return SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast")
