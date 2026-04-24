"""Reusable runtime helpers for MPO train/eval scripts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch

from environment_definition.attitude_control_env import SatelliteAttitudeControlEnv

from .reward import RewardConfig


class ReplayBuffer:
    def __init__(self, size: int, obs_size: int, action_size: int, device: torch.device) -> None:
        self.size = int(size)
        self.device = device
        self.obs = np.zeros((self.size, obs_size), dtype=np.float32)
        self.next_obs = np.zeros((self.size, obs_size), dtype=np.float32)
        self.actions = np.zeros((self.size, action_size), dtype=np.float32)
        self.rewards = np.zeros((self.size,), dtype=np.float32)
        self.done = np.zeros((self.size,), dtype=np.float32)
        self.ptr = 0
        self.count = 0

    def __len__(self) -> int:
        return self.count

    def store(
        self,
        obs: np.ndarray,
        next_obs: np.ndarray,
        action: np.ndarray,
        reward: float,
        done: bool,
    ) -> None:
        self.obs[self.ptr] = obs
        self.next_obs[self.ptr] = next_obs
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = reward
        self.done[self.ptr] = float(done)
        self.ptr = (self.ptr + 1) % self.size
        self.count = min(self.count + 1, self.size)

    def sample(
        self, batch_size: int
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        idxs = np.random.randint(0, self.count, size=batch_size)
        obs = torch.as_tensor(self.obs[idxs], dtype=torch.float32, device=self.device)
        action = torch.as_tensor(self.actions[idxs], dtype=torch.float32, device=self.device)
        next_obs = torch.as_tensor(self.next_obs[idxs], dtype=torch.float32, device=self.device)
        done = torch.as_tensor(self.done[idxs], dtype=torch.float32, device=self.device)
        reward = torch.as_tensor(self.rewards[idxs], dtype=torch.float32, device=self.device)
        return obs, action, next_obs, done, reward


@dataclass
class EpisodeResult:
    episode_return: float
    steps: int
    states: list[np.ndarray]


def make_attitude_control_env(
    *,
    render_mode: str | None = None,
    reward_config: RewardConfig | None = None,
) -> SatelliteAttitudeControlEnv:
    return SatelliteAttitudeControlEnv(render_mode=render_mode, reward_config=reward_config)


def run_episode(
    env: SatelliteAttitudeControlEnv,
    agent: Any,
    *,
    mode: str,
    train_updates_per_step: int = 1,
    max_steps: int | None = None,
) -> EpisodeResult:
    if hasattr(agent, "reset_episode"):
        agent.reset_episode()
    obs, _ = env.reset()
    done = False
    truncated = False
    episode_return = 0.0
    step = 0
    states: list[np.ndarray] = [np.array(obs, dtype=np.float32)]
    max_episode_steps = max_steps if max_steps is not None else env.max_episode_steps

    while not (done or truncated) and step < max_episode_steps:
        train_mode = mode in {"warmup", "train"}
        action = agent.get_action(obs, train=train_mode)
        next_obs, reward, done, truncated, _ = env.step(action)
        episode_return += float(reward)
        states.append(np.array(next_obs, dtype=np.float32))
        if mode in {"warmup", "train"} and hasattr(agent, "store"):
            agent.store((obs, action, float(reward), next_obs, bool(done or truncated)))
            if mode == "train":
                for _ in range(train_updates_per_step):
                    if hasattr(agent, "train"):
                        agent.train()
        obs = next_obs
        step += 1

    return EpisodeResult(episode_return=episode_return, steps=step, states=states)

