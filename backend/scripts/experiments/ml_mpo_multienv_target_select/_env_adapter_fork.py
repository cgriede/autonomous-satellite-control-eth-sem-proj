"""Gymnasium env adapter for 52-dim factored actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from gymnasium import spaces

from autonomous_control.controller_observation import (
    ControllerObservationLayout,
    controller_observation_layout,
)
from autonomous_control.feature_selection import ControllerFeatureConfig
from autonomous_control.reward import RewardConfig
from environment_definition.constants import SIMULATION

from _action_constants import N_ACTION_DIMS, N_TARGETS


def make_exp14_attitude_control_env(
    *,
    reward_config: RewardConfig | None = None,
    feature_config: ControllerFeatureConfig | None = None,
    secondary_camera_observation_line_n_bins: int = 0,
    n_mission_targets: int = N_TARGETS,
    observation_layout: ControllerObservationLayout | None = None,
) -> Any:
    _ = reward_config
    cfg = feature_config if feature_config is not None else ControllerFeatureConfig()
    layout = (
        observation_layout
        if observation_layout is not None
        else controller_observation_layout(
            feature_config=cfg,
            secondary_camera_observation_line_n_bins=secondary_camera_observation_line_n_bins,
            n_mission_targets=int(n_mission_targets),
        )
    )
    obs_dim = layout.scalar_dim + sum(layout.vision_seq_lens)
    high = np.full((obs_dim,), np.finfo(np.float32).max, dtype=np.float32)
    target_high = np.ones(N_TARGETS, dtype=np.float32)
    cont_high = np.ones(2, dtype=np.float32)
    action_high = np.concatenate([target_high, cont_high]).astype(np.float32)
    target_low = np.zeros(N_TARGETS, dtype=np.float32)
    cont_low = -np.ones(2, dtype=np.float32)
    action_low = np.concatenate([target_low, cont_low]).astype(np.float32)

    @dataclass(frozen=True)
    class _EnvAdapter:
        observation_space: Any
        action_space: Any
        observation_layout: ControllerObservationLayout
        dt: Any
        max_episode_steps: int

    return _EnvAdapter(
        observation_space=spaces.Box(-high, high, dtype=np.float32),
        observation_layout=layout,
        action_space=spaces.Box(
            low=action_low,
            high=action_high,
            shape=(N_ACTION_DIMS,),
            dtype=np.float32,
        ),
        dt=SIMULATION.simulation_timestep,
        max_episode_steps=int(SIMULATION.max_episode_steps),
    )


__all__ = ["make_exp14_attitude_control_env"]
