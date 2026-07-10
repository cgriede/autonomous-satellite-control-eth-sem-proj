"""Exp 15 env setup: per-episode seeds; cloud bounds frozen from Exp 14."""

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

# Distinct from Exp 14 (14000) so train/eval cohorts do not collide.
EXP15_BASE_SEED = 15000
EVAL_ENV_COUNT = 5
# Frozen Exp 14 cloud bounds — do not widen here (Exp 16).
EXP15_CLOUD_NUMBER_BOUNDS = (20, 40)
EXP15_SAT_Z_OFFSET_DEG_BOUNDS = (-5.0, 5.0)

WARMUP_MISSION_SEED = 7
WARMUP_CLOUD_SEED = 7


def eval_env_indices() -> tuple[int, ...]:
    return tuple(range(EVAL_ENV_COUNT))


def episode_seeds(episode_index: int) -> dict[str, int]:
    """Reproducible per-episode mission/cloud/attitude seeds."""
    i = int(episode_index)
    return {
        "mission_seed": int(derive_seed(EXP15_BASE_SEED, "exp15_ep_mission", i)),
        "cloud_seed": int(derive_seed(EXP15_BASE_SEED, "exp15_ep_cloud", i)),
        "sat_z_seed": int(derive_seed(EXP15_BASE_SEED, "exp15_ep_satz", i)),
        "episode_index": i,
    }


def eval_episode_seeds(eval_index: int) -> dict[str, int]:
    """Held-out eval seeds (disjoint namespace from train episodes)."""
    i = int(eval_index)
    return {
        "mission_seed": int(derive_seed(EXP15_BASE_SEED, "exp15_eval_mission", i)),
        "cloud_seed": int(derive_seed(EXP15_BASE_SEED, "exp15_eval_cloud", i)),
        "sat_z_seed": int(derive_seed(EXP15_BASE_SEED, "exp15_eval_satz", i)),
        "eval_index": i,
    }


def build_exp15_clouds(segments, *, seed: int) -> tuple[Cloud, ...]:
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
        cloud_number_bounds=EXP15_CLOUD_NUMBER_BOUNDS,
        cloud_range_bounds=BASELINE_CLOUD_RANGE_BOUNDS,
        cloud_base_altitude_bounds=BASELINE_CLOUD_BASE_ALTITUDE_BOUNDS,
        cloud_thickness_bounds=BASELINE_CLOUD_THICKNESS_BOUNDS,
        max_top_altitude=BASELINE_CLOUD_MAX_TOP_ALTITUDE,
        rng=np.random.default_rng(int(seed)),
    )
    return tuple(clouds)


def build_exp15_env_setup_from_seeds(
    *,
    mission_seed: int,
    cloud_seed: int,
    sat_z_seed: int | None = None,
    sample_sat_z_offset: bool = True,
) -> EnvironmentSetup:
    base = build_setup(seed=int(mission_seed), include_cameras=True)
    orbit = base.orbit or OrbitConfig()
    if sample_sat_z_offset:
        z_seed = int(sat_z_seed) if sat_z_seed is not None else int(mission_seed)
        sat_z_rng = np.random.default_rng(z_seed)
        sat_z_deg = float(
            sat_z_rng.uniform(
                EXP15_SAT_Z_OFFSET_DEG_BOUNDS[0],
                EXP15_SAT_Z_OFFSET_DEG_BOUNDS[1],
            )
        )
        orbit = replace(orbit, sat_z_offset=float(sat_z_deg) * ureg.deg)
    segments = build_baseline_target_segments(n_targets=N_TARGETS)
    target_areas = tuple(s.to_observation_target_area() for s in segments)
    clouds = build_exp15_clouds(segments, seed=int(cloud_seed))
    return replace(
        base,
        orbit=orbit,
        target_areas=target_areas,
        clouds=clouds,
    )


def build_exp15_episode_setup(episode_index: int) -> EnvironmentSetup:
    seeds = episode_seeds(episode_index)
    return build_exp15_env_setup_from_seeds(
        mission_seed=seeds["mission_seed"],
        cloud_seed=seeds["cloud_seed"],
        sat_z_seed=seeds["sat_z_seed"],
    )


def build_exp15_eval_setup(eval_index: int) -> EnvironmentSetup:
    seeds = eval_episode_seeds(eval_index)
    return build_exp15_env_setup_from_seeds(
        mission_seed=seeds["mission_seed"],
        cloud_seed=seeds["cloud_seed"],
        sat_z_seed=seeds["sat_z_seed"],
    )


def build_exp15_warmup_setup() -> EnvironmentSetup:
    return build_exp15_env_setup_from_seeds(
        mission_seed=WARMUP_MISSION_SEED,
        cloud_seed=WARMUP_CLOUD_SEED,
        sample_sat_z_offset=False,
    )


# Back-compat aliases so copied Exp 14 modules keep importing.
EXP14_BASE_SEED = EXP15_BASE_SEED
EXP14_CLOUD_NUMBER_BOUNDS = EXP15_CLOUD_NUMBER_BOUNDS
EXP14_SAT_Z_OFFSET_DEG_BOUNDS = EXP15_SAT_Z_OFFSET_DEG_BOUNDS
SCREEN_MISSION_SEED = WARMUP_MISSION_SEED
SCREEN_CLOUD_SEED = WARMUP_CLOUD_SEED
TRAIN_ENV_COUNT = 1


def build_exp14_clouds(segments, *, seed: int) -> tuple[Cloud, ...]:
    return build_exp15_clouds(segments, seed=seed)


def build_exp14_env_setup(env_index: int, *, sample_sat_z_offset: bool = True) -> EnvironmentSetup:
    return build_exp15_episode_setup(int(env_index))


def build_exp14_env_setup_fixed(
    *,
    mission_seed: int = WARMUP_MISSION_SEED,
    cloud_seed: int = WARMUP_CLOUD_SEED,
) -> EnvironmentSetup:
    return build_exp15_env_setup_from_seeds(
        mission_seed=int(mission_seed),
        cloud_seed=int(cloud_seed),
        sample_sat_z_offset=False,
    )


def build_exp14_eval_setup(eval_index: int) -> EnvironmentSetup:
    return build_exp15_eval_setup(eval_index)


def eval_mission_seed(eval_index: int) -> int:
    return int(eval_episode_seeds(eval_index)["mission_seed"])


def eval_cloud_seed(eval_index: int) -> int:
    return int(eval_episode_seeds(eval_index)["cloud_seed"])


def train_env_seeds(env_index: int) -> dict[str, int]:
    return episode_seeds(env_index)


__all__ = [
    "EVAL_ENV_COUNT",
    "EXP15_BASE_SEED",
    "EXP15_CLOUD_NUMBER_BOUNDS",
    "EXP15_SAT_Z_OFFSET_DEG_BOUNDS",
    "N_TARGETS",
    "WARMUP_CLOUD_SEED",
    "WARMUP_MISSION_SEED",
    "build_exp15_clouds",
    "build_exp15_episode_setup",
    "build_exp15_env_setup_from_seeds",
    "build_exp15_eval_setup",
    "build_exp15_warmup_setup",
    "episode_seeds",
    "eval_episode_seeds",
    "eval_env_indices",
    # aliases
    "EXP14_BASE_SEED",
    "EXP14_CLOUD_NUMBER_BOUNDS",
    "EXP14_SAT_Z_OFFSET_DEG_BOUNDS",
    "SCREEN_CLOUD_SEED",
    "SCREEN_MISSION_SEED",
    "TRAIN_ENV_COUNT",
    "build_exp14_clouds",
    "build_exp14_env_setup",
    "build_exp14_env_setup_fixed",
    "build_exp14_eval_setup",
    "eval_cloud_seed",
    "eval_mission_seed",
    "train_env_seeds",
]
