"""SAC agent with selectable flat (A0) or compressed (A1) encoder."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from autonomous_control.controller_observation import (
    ControllerObservation,
    controller_observation_to_tensors,
)
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.training_runtime import ReplayBuffer

from encoder_agents.modular_actor import ModularActor
from encoder_agents.modular_critic import ModularCritic

EncoderMode = Literal["flat", "compress"]


class _CheckpointStubOptimizer:
    def state_dict(self) -> dict:
        return {}

    def load_state_dict(self, *_args, **_kwargs) -> None:
        return None


class SACModularAgent:
    """SAC fork with ModularActor/ModularCritic encoder modes."""

    def __init__(
        self,
        env: Any,
        config: MPOConfig | None = None,
        *,
        alpha: float = 0.2,
        encoder_mode: EncoderMode = "compress",
        vector_embed_dim: int = 8,
    ) -> None:
        self.config = config if config is not None else MPOConfig()
        self.alpha = float(alpha)
        self.encoder_mode = encoder_mode
        self.vector_embed_dim = int(vector_embed_dim)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(
            f"Using device: {self.device} (SACModularAgent mode={encoder_mode} "
            f"vector_embed_dim={vector_embed_dim})"
        )

        layout = getattr(env, "observation_layout", None)
        if layout is None:
            raise ValueError("env must expose observation_layout for SACModularAgent.")
        self.observation_layout = layout
        self.layout = layout
        self.action_size = int(env.action_space.shape[0])

        action_low = torch.tensor(env.action_space.low, dtype=torch.float32, device=self.device)
        action_high = torch.tensor(env.action_space.high, dtype=torch.float32, device=self.device)
        action_size = self.action_size

        enc_kw = dict(
            encoder_mode=encoder_mode,
            vector_embed_dim=vector_embed_dim,
        )
        self.pi = ModularActor(
            action_low, action_high, layout, action_size, self.config, **enc_kw
        ).to(self.device)
        self.pi_target = ModularActor(
            action_low, action_high, layout, action_size, self.config, **enc_kw
        ).to(self.device)
        self.pi_target.load_state_dict(self.pi.state_dict())

        self.q1 = ModularCritic(layout, action_size, self.config, **enc_kw).to(self.device)
        self.q2 = ModularCritic(layout, action_size, self.config, **enc_kw).to(self.device)
        self.q1_target = ModularCritic(layout, action_size, self.config, **enc_kw).to(self.device)
        self.q2_target = ModularCritic(layout, action_size, self.config, **enc_kw).to(self.device)
        self.q1_target.load_state_dict(self.q1.state_dict())
        self.q2_target.load_state_dict(self.q2.state_dict())

        self.action_scale = (action_high - action_low) / 2
        self.action_bias = (action_high + action_low) / 2

        self.q_optimizer = optim.Adam(
            list(self.q1.parameters()) + list(self.q2.parameters()),
            lr=self.config.learning_rate_q,
        )
        self.pi_optimizer = optim.Adam(self.pi.parameters(), lr=self.config.learning_rate_pi)

        self.buffer = ReplayBuffer(
            self.config.buffer_size,
            layout,
            action_size,
            self.device,
        )
        self.step_counter = 0
        self.current_ep_return = 0.0
        self.episode_returns: list[float] = []
        self.metrics: dict[str, list[float]] = {
            "qloss": [],
            "piloss": [],
            "return": [],
        }
        self.log_eta = torch.tensor(0.0, device=self.device)
        self.eta_optimizer = _CheckpointStubOptimizer()

    def _soft_update(self, target: nn.Module, source: nn.Module) -> None:
        for target_param, param in zip(target.parameters(), source.parameters()):
            target_param.data.copy_(
                self.config.tau * param.data + (1.0 - self.config.tau) * target_param.data
            )

    def _obs_tensors(
        self, obs: ControllerObservation
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, ...]]:
        return controller_observation_to_tensors(obs, device=self.device)

    def _squash_log_prob(
        self, dist: torch.distributions.Normal, actions_gaussian: torch.Tensor
    ) -> torch.Tensor:
        actions_tanh = torch.tanh(actions_gaussian)
        log_prob = dist.log_prob(actions_gaussian).sum(-1)
        jacobian = torch.log(1 - actions_tanh.pow(2) + 1e-6).sum(-1)
        return log_prob - jacobian

    def train(self) -> dict[str, float] | None:
        if len(self.buffer) < self.config.batch_size:
            return None

        (obs_scalars, obs_vision), action, (next_scalars, next_vision), done, reward = (
            self.buffer.sample(self.config.batch_size)
        )
        last_return = self.episode_returns[-1] if self.episode_returns else -200.0
        self.metrics["return"].append(float(last_return))

        with torch.no_grad():
            dist_next = self.pi_target(next_scalars, next_vision)
            next_actions = dist_next.rsample()
            next_actions_squashed = torch.tanh(next_actions) * self.action_scale + self.action_bias
            q_next = torch.min(
                self.q1_target(next_scalars, next_vision, next_actions_squashed),
                self.q2_target(next_scalars, next_vision, next_actions_squashed),
            )
            next_log_prob = self._squash_log_prob(dist_next, next_actions)
            target = reward.unsqueeze(1) + (1 - done.unsqueeze(1)) * self.config.gamma * (
                q_next - self.alpha * next_log_prob.unsqueeze(1)
            )

        q1_pred = self.q1(obs_scalars, obs_vision, action)
        q2_pred = self.q2(obs_scalars, obs_vision, action)
        q_loss = nn.functional.mse_loss(q1_pred, target) + nn.functional.mse_loss(q2_pred, target)
        self.metrics["qloss"].append(float(q_loss.item()))

        self.q_optimizer.zero_grad()
        q_loss.backward()
        self.q_optimizer.step()

        dist = self.pi(obs_scalars, obs_vision)
        actions_pi = dist.rsample()
        actions_squashed = torch.tanh(actions_pi) * self.action_scale + self.action_bias
        q_pi = torch.min(
            self.q1(obs_scalars, obs_vision, actions_squashed),
            self.q2(obs_scalars, obs_vision, actions_squashed),
        )
        log_prob = self._squash_log_prob(dist, actions_pi)
        pi_loss = (self.alpha * log_prob.unsqueeze(1) - q_pi).mean()
        self.metrics["piloss"].append(float(pi_loss.item()))

        self.pi_optimizer.zero_grad()
        pi_loss.backward()
        self.pi_optimizer.step()

        self._soft_update(self.q1_target, self.q1)
        self._soft_update(self.q2_target, self.q2)
        self._soft_update(self.pi_target, self.pi)

        return {
            "q_loss": float(q_loss.item()),
            "pi_loss": float(pi_loss.item()),
            "alpha": self.alpha,
        }

    def get_action(self, obs: ControllerObservation, train: bool) -> np.ndarray:
        scalars, vision = self._obs_tensors(obs)
        with torch.no_grad():
            dist = self.pi(scalars, vision)
            if train:
                action_gaussian = dist.rsample()
            else:
                action_gaussian = dist.mean
            action_scaled = torch.tanh(action_gaussian) * self.action_scale + self.action_bias
        return action_scaled.cpu().numpy().reshape(-1).astype(np.float64)

    def store(
        self, transition: tuple[ControllerObservation, np.ndarray, float, ControllerObservation, bool]
    ) -> None:
        obs, action, rew, next_obs, done = transition
        self.current_ep_return += float(rew)
        self.step_counter += 1
        if done:
            self.episode_returns.append(self.current_ep_return)
            self.current_ep_return = 0.0
        self.buffer.store(obs, next_obs, action, rew, done)
