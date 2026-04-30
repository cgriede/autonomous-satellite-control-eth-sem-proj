from __future__ import annotations

from typing import Any

import numpy as np

from autonomous_control.reward import RewardConfig, RewardSignals, compute_reward
from environment_definition.constants.SIMULATION import OBSERVATION_TARGET


class RewardKernel:
    @staticmethod
    def evaluate(
        *,
        sat_pos_xy_km: np.ndarray,
        target_xy_km: np.ndarray,
        camera_observation_line_codes: np.ndarray,
        wheel_inertia: Any,
        omega_before: Any,
        omega_after: Any,
        reward_config: RewardConfig,
        ureg: Any,
    ) -> float:
        target_visible = bool(np.any(camera_observation_line_codes == np.int8(OBSERVATION_TARGET)))
        distance_to_target_km = float(np.linalg.norm(sat_pos_xy_km - target_xy_km))
        signals = RewardSignals(
            distance_to_target=distance_to_target_km * ureg.km,
            picture_taken=True,
            target_visible=target_visible,
            wheel_inertia=wheel_inertia,
            omega_before=omega_before,
            omega_after=omega_after,
        )
        reward_total, _ = compute_reward(signals=signals, cfg=reward_config)
        return float(reward_total)
