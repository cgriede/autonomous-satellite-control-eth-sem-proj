from __future__ import annotations

from typing import Any

import numpy as np

from autonomous_control.reward import RewardConfig, RewardSignals, compute_reward
from environment_definition.constants.MISSION import (
    LON_GLOBAL,
    OBSERVATION_TARGET_AREAS,
)
from environment_definition.constants.SIMULATION import OBSERVATION_TARGET
from utils.geodesics.geodesic_helpers import (
    geodesic_distance,
)


class RewardKernel:
    @staticmethod
    def evaluate(
        *,
        sat_pos_xy_km: np.ndarray,
        sat_subpoint_lat_deg: float,
        sat_subpoint_lon_deg: float,
        target_area_intersection_ratio: float,
        target_area_novelty_ratio: float,
        camera_observation_line_codes: np.ndarray,
        wheel_inertia: Any,
        omega_before: Any,
        omega_after: Any,
        reward_config: RewardConfig,
        ureg: Any,
    ) -> float:
        _ = sat_pos_xy_km
        codes = np.asarray(camera_observation_line_codes, dtype=np.int8)
        target_visible = bool(np.any(codes == np.int8(OBSERVATION_TARGET)))
        target_area = OBSERVATION_TARGET_AREAS[0]
        target_center_lat = 0.5 * (
            float(target_area.lat_min.to(ureg.deg).magnitude)
            + float(target_area.lat_max.to(ureg.deg).magnitude)
        )
        distance_to_target = geodesic_distance(
            sat_subpoint_lon_deg * ureg.deg,
            sat_subpoint_lat_deg * ureg.deg,
            LON_GLOBAL,
            target_center_lat * ureg.deg,
        )
        signals = RewardSignals(
            distance_to_target=distance_to_target,
            picture_taken=True,
            target_visible=target_visible,
            target_area_intersection_ratio=float(target_area_intersection_ratio),
            target_area_novelty_ratio=float(target_area_novelty_ratio),
            wheel_inertia=wheel_inertia,
            omega_before=omega_before,
            omega_after=omega_after,
        )
        reward_total, _ = compute_reward(signals=signals, cfg=reward_config)
        return float(reward_total)
