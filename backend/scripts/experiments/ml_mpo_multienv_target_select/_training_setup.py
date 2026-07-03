"""Build agent + observation layout for Exp 14 runs."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from autonomous_control.controller_observation import controller_observation_layout
from autonomous_control.mpo_config import MPOConfig

from _factorized_mpo_agent import FactoredMPOAgent, build_factored_mpo_agent
from _profile_baseline import FEATURE_CONFIG, SCREEN_ARMS, ScreenArmSpec, mpo_config_for_arm
from _exp14_reward_fork import RewardForkMode, activate_reward_fork, exp14_reward_config


@dataclass
class Exp14TrainingContext:
    agent: FactoredMPOAgent
    mpo_config: MPOConfig
    feature_config: Any
    observation_layout: Any
    reward_config: Any
    reward_mode: RewardForkMode
    secondary_camera_bins: int
    n_mission_targets: int
    entropy_coef: float


def build_training_context(
    setup,
    *,
    arm: ScreenArmSpec | None = None,
    mpo_config: MPOConfig | None = None,
    entropy_coef: float | None = None,
) -> Exp14TrainingContext:
    reward_mode: RewardForkMode = (
        arm.reward_mode if arm is not None else "exp14_sparse"
    )
    reward_config = activate_reward_fork(reward_mode)
    resolved = setup.resolve(require_camera=True)
    n_targets = len(resolved.target_areas or ())
    secondary_bins = int(resolved.secondary_camera_observation_line_n_bins)
    obs_layout = controller_observation_layout(
        feature_config=FEATURE_CONFIG,
        secondary_camera_observation_line_n_bins=secondary_bins,
        n_mission_targets=n_targets,
    )
    if arm is not None:
        cfg = replace(mpo_config_for_arm(arm), reward=exp14_reward_config(reward_mode))
        ent = float(arm.entropy_coef)
    else:
        default_arm = SCREEN_ARMS[0]
        cfg = replace(
            mpo_config if mpo_config is not None else mpo_config_for_arm(default_arm),
            reward=exp14_reward_config(reward_mode),
        )
        ent = float(entropy_coef if entropy_coef is not None else default_arm.entropy_coef)
    agent = build_factored_mpo_agent(
        mpo_config=cfg,
        feature_config=FEATURE_CONFIG,
        secondary_camera_bins=secondary_bins,
        n_mission_targets=n_targets,
        observation_layout=obs_layout,
        entropy_coef=ent,
    )
    return Exp14TrainingContext(
        agent=agent,
        mpo_config=cfg,
        feature_config=FEATURE_CONFIG,
        observation_layout=obs_layout,
        reward_config=reward_config,
        reward_mode=reward_mode,
        secondary_camera_bins=secondary_bins,
        n_mission_targets=n_targets,
        entropy_coef=ent,
    )


__all__ = ["Exp14TrainingContext", "build_training_context"]
