from __future__ import annotations

from typing import Any

import numpy as np

from autonomous_control.reward import RewardConfig, RewardSignals, compute_reward
from environment_definition.constants.MISSION import (
    OBSERVATION_TARGET_STRIPE_END_LAT,
    OBSERVATION_TARGET_STRIPE_END_LON,
    OBSERVATION_TARGET_STRIPE_START_LAT,
    OBSERVATION_TARGET_STRIPE_START_LON,
)
from environment_definition.constants.SIMULATION import OBSERVATION_TARGET
from utils.geodesics.geodesic_helpers import (
    geodesic_distance,
    lonlat_to_z0_plane_angle_deg,
    minor_arc_midpoint_deg,
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
        target_visible = bool(target_area_intersection_ratio > 0.0) or bool(
            np.any(camera_observation_line_codes == np.int8(OBSERVATION_TARGET))
        )
        s0 = lonlat_to_z0_plane_angle_deg(
            OBSERVATION_TARGET_STRIPE_START_LON,
            OBSERVATION_TARGET_STRIPE_START_LAT,
        )
        s1 = lonlat_to_z0_plane_angle_deg(
            OBSERVATION_TARGET_STRIPE_END_LON,
            OBSERVATION_TARGET_STRIPE_END_LAT,
        )
        target_center_lon = minor_arc_midpoint_deg(s0, s1)
        target_center_lat = 0.0
        distance_to_target = geodesic_distance(
            sat_subpoint_lon_deg * ureg.deg,
            sat_subpoint_lat_deg * ureg.deg,
            target_center_lon * ureg.deg,
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
