"""Reproduce clouds+target-grid reward for debug session 1a7e56."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
S01 = BACKEND / "notebooks" / "s01"
if str(S01) not in sys.path:
    sys.path.insert(0, str(S01))

from environment_definition.constants import ureg
from environment_definition.constants.MISSION import LON_GLOBAL
from environment_definition.constants.SIMULATION import OBSERVATION_TARGET, RenderMode, SimulationConfig
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from s01_utils.cloud_formation import cloud_formation_generator
from simulation.run_simulation import run_simulation
from utils.geometry.polar_meridian_track import build_target_grid_polar_meridian

clouds = cloud_formation_generator(
    formation_start=__import__(
        "environment_definition.constants.SIMULATION", fromlist=["GeodeticLonLat"]
    ).GeodeticLonLat(lat=75.0 * ureg.deg, lon=0.0 * ureg.deg),
    formation_end=__import__(
        "environment_definition.constants.SIMULATION", fromlist=["GeodeticLonLat"]
    ).GeodeticLonLat(lat=75.0 * ureg.deg, lon=180.0 * ureg.deg),
    cloud_base_altitude_bounds=(4, 12) * ureg.km,
    cloud_thickness_bounds=(1, 16) * ureg.km,
    max_top_altitude=20 * ureg.km,
    cloud_range_bounds=(1, 100) * ureg.km,
    cloud_number_bounds=(50, 200),
    rng=np.random.default_rng(42),
)
segments = build_target_grid_polar_meridian(
    anchor_lat=80 * ureg.deg,
    anchor_lon=LON_GLOBAL,
    n_targets=50,
    target_size=15 * ureg.kilometer,
    spacing=40 * ureg.kilometer,
)
targets = [s.to_observation_target_area() for s in segments]
setup = replace(
    build_setup(seed=0, include_cameras=True),
    target_areas=tuple(targets),
    clouds=tuple(clouds),
)
series = run_simulation(
    setup=setup,
    simulation_config=SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast"),
)
rew = series.simulation_reward[1:]
codes = series.camera_observation_line_codes
n_tgt_per_step = np.sum(codes == np.int8(OBSERVATION_TARGET), axis=1)
print(f"frames={len(series.t_s)} mean_reward={float(np.mean(rew)):.3f}")
print(f"max_reward={float(np.max(rew)):.3f} at step {int(np.argmax(rew))}")
print(f"last30 max_reward={float(np.max(rew[-30:])):.3f}")
print(f"steps with reward>-50: {int(np.sum(rew > -50))}")
print(f"steps reward>-100 but 0 target bins: {int(np.sum((rew > -100) & (n_tgt_per_step[1:] == 0)))}")
