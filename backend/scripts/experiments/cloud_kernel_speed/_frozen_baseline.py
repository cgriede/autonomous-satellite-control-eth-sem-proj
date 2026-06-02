"""Frozen baseline tunables for cloud kernel speed experiments."""

from __future__ import annotations

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

BASELINE_SEED = 0
BASELINE_RNG = np.random.default_rng(42)

FORMATION_START = GeodeticLonLat(lat=75.0 * ureg.deg, lon=0.0 * ureg.deg)
FORMATION_END = GeodeticLonLat(lat=75.0 * ureg.deg, lon=180.0 * ureg.deg)

CLOUD_BASE_ALTITUDE_BOUNDS = (4, 12) * ureg.km
CLOUD_THICKNESS_BOUNDS = (1, 16) * ureg.km
CLOUD_RANGE_BOUNDS = (10, 50) * ureg.km
CLOUD_NUMBER_BOUNDS = (5, 6)
MAX_TOP_ALTITUDE = 20 * ureg.km


def build_baseline_clouds():
    return cloud_formation_generator(
        formation_start=FORMATION_START,
        formation_end=FORMATION_END,
        cloud_base_altitude_bounds=CLOUD_BASE_ALTITUDE_BOUNDS,
        cloud_thickness_bounds=CLOUD_THICKNESS_BOUNDS,
        cloud_range_bounds=CLOUD_RANGE_BOUNDS,
        cloud_number_bounds=CLOUD_NUMBER_BOUNDS,
        max_top_altitude=MAX_TOP_ALTITUDE,
        rng=BASELINE_RNG,
    )


def build_baseline_setup():
    clouds = build_baseline_clouds()
    return replace(
        build_setup(seed=BASELINE_SEED, include_cameras=True),
        clouds=tuple(clouds),
    )


def build_baseline_sim_config() -> SimulationConfig:
    return SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast")
