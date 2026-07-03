"""Exp 14 environment setup: multi-env sampling with cloud count override."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from autonomous_control.config.randomness import derive_seed
from environment_definition.constants.SIMULATION import Cloud, GeodeticLonLat
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from simulation.setup_types import EnvironmentSetup, OrbitConfig
from utils.geometry.polar_meridian_track import lat_deg_from_track_offset_deg

from s01_utils.baseline_overflight import (
    BASELINE_CLOUD_BASE_ALTITUDE_BOUNDS,
    BASELINE_CLOUD_MAX_TOP_ALTITUDE,
    BASELINE_CLOUD_RANGE_BOUNDS,
    BASELINE_CLOUD_THICKNESS_BOUNDS,
    build_baseline_target_segments,
)
from s01_utils.cloud_formation import cloud_formation_generator

from _action_constants import N_TARGETS

EXP14_BASE_SEED = 14000
TRAIN_ENV_COUNT = 10
EVAL_ENV_COUNT = 5
EXP14_CLOUD_NUMBER_BOUNDS = (20, 40)
EXP14_SAT_Z_OFFSET_DEG_BOUNDS = (-5.0, 5.0)

SCREEN_MISSION_SEED = 7
SCREEN_CLOUD_SEED = 7


def eval_env_indices() -> tuple[int, ...]:
    return tuple(range(EVAL_ENV_COUNT))


def eval_mission_seed(eval_index: int) -> int:
    return int(derive_seed(EXP14_BASE_SEED, "exp14_eval_mission", int(eval_index)))


def eval_cloud_seed(eval_index: int) -> int:
    return int(derive_seed(EXP14_BASE_SEED, "exp14_eval_cloud", int(eval_index)))


def train_env_seeds(env_index: int) -> dict[str, int]:
    i = int(env_index)
    return {
        "mission_seed": int(derive_seed(EXP14_BASE_SEED, "exp14_mission", i)),
        "cloud_seed": int(derive_seed(EXP14_BASE_SEED, "exp14_cloud", i)),
        "sat_z_seed": int(derive_seed(EXP14_BASE_SEED, "exp14_satz", i)),
    }


def build_exp14_clouds(segments, *, seed: int) -> tuple[Cloud, ...]:
    """Seeded clouds along target corridor with Exp 14 cloud count bounds."""
    if not segments:
        return ()
    first, last = segments[0], segments[-1]
    formation_start = GeodeticLonLat(
        lat=lat_deg_from_track_offset_deg(first.track_offset_lo_deg) * ureg.deg,
        lon=first.endpoint_lon_deg(which="min") * ureg.deg,
    )
    formation_end = GeodeticLonLat(
        lat=lat_deg_from_track_offset_deg(last.track_offset_hi_deg) * ureg.deg,
        lon=last.endpoint_lon_deg(which="max") * ureg.deg,
    )
    clouds = cloud_formation_generator(
        formation_start=formation_start,
        formation_end=formation_end,
        cloud_number_bounds=EXP14_CLOUD_NUMBER_BOUNDS,
        cloud_range_bounds=BASELINE_CLOUD_RANGE_BOUNDS,
        cloud_base_altitude_bounds=BASELINE_CLOUD_BASE_ALTITUDE_BOUNDS,
        cloud_thickness_bounds=BASELINE_CLOUD_THICKNESS_BOUNDS,
        max_top_altitude=BASELINE_CLOUD_MAX_TOP_ALTITUDE,
        rng=np.random.default_rng(int(seed)),
    )
    return tuple(clouds)


def build_exp14_env_setup(
    env_index: int,
    *,
    sample_sat_z_offset: bool = True,
) -> EnvironmentSetup:
    mission_seed = int(derive_seed(EXP14_BASE_SEED, "exp14_mission", int(env_index)))
    cloud_seed = int(derive_seed(EXP14_BASE_SEED, "exp14_cloud", int(env_index)))
    base = build_setup(seed=mission_seed, include_cameras=True)
    orbit = base.orbit or OrbitConfig()
    if sample_sat_z_offset:
        sat_z_rng = np.random.default_rng(
            int(derive_seed(EXP14_BASE_SEED, "exp14_satz", int(env_index)))
        )
        sat_z_deg = float(
            sat_z_rng.uniform(
                EXP14_SAT_Z_OFFSET_DEG_BOUNDS[0],
                EXP14_SAT_Z_OFFSET_DEG_BOUNDS[1],
            )
        )
        orbit = replace(orbit, sat_z_offset=float(sat_z_deg) * ureg.deg)
    segments = build_baseline_target_segments(n_targets=N_TARGETS)
    target_areas = tuple(s.to_observation_target_area() for s in segments)
    clouds = build_exp14_clouds(segments, seed=cloud_seed)
    return replace(
        base,
        orbit=orbit,
        target_areas=target_areas,
        clouds=clouds,
    )


def build_exp14_env_setup_fixed(
    *,
    mission_seed: int = SCREEN_MISSION_SEED,
    cloud_seed: int = SCREEN_CLOUD_SEED,
) -> EnvironmentSetup:
    """Fixed env for hparam screen (no sat_z_offset sampling)."""
    base = build_setup(seed=int(mission_seed), include_cameras=True)
    segments = build_baseline_target_segments(n_targets=N_TARGETS)
    target_areas = tuple(s.to_observation_target_area() for s in segments)
    clouds = build_exp14_clouds(segments, seed=int(cloud_seed))
    return replace(
        base,
        target_areas=target_areas,
        clouds=clouds,
    )


def build_exp14_eval_setup(eval_index: int) -> EnvironmentSetup:
    base = build_setup(seed=eval_mission_seed(eval_index), include_cameras=True)
    segments = build_baseline_target_segments(n_targets=N_TARGETS)
    target_areas = tuple(s.to_observation_target_area() for s in segments)
    clouds = build_exp14_clouds(segments, seed=eval_cloud_seed(eval_index))
    sat_z_rng = np.random.default_rng(
        int(derive_seed(EXP14_BASE_SEED, "exp14_eval_satz", int(eval_index)))
    )
    sat_z_deg = float(
        sat_z_rng.uniform(
            EXP14_SAT_Z_OFFSET_DEG_BOUNDS[0],
            EXP14_SAT_Z_OFFSET_DEG_BOUNDS[1],
        )
    )
    orbit = replace(base.orbit or OrbitConfig(), sat_z_offset=float(sat_z_deg) * ureg.deg)
    return replace(
        base,
        orbit=orbit,
        target_areas=target_areas,
        clouds=clouds,
    )


__all__ = [
    "EVAL_ENV_COUNT",
    "EXP14_BASE_SEED",
    "EXP14_CLOUD_NUMBER_BOUNDS",
    "EXP14_SAT_Z_OFFSET_DEG_BOUNDS",
    "N_TARGETS",
    "SCREEN_CLOUD_SEED",
    "SCREEN_MISSION_SEED",
    "TRAIN_ENV_COUNT",
    "build_exp14_clouds",
    "build_exp14_env_setup",
    "build_exp14_env_setup_fixed",
    "build_exp14_eval_setup",
    "eval_cloud_seed",
    "eval_env_indices",
    "eval_mission_seed",
    "train_env_seeds",
]
