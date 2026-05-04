"""Controller agent implementation for MPO plus linear baseline policy."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from .action_adapter import POLICY_RAW_DIM
from .controller_actor import Actor
from .controller_critic import Critic
from .mpo_config import MPOConfig
from .training_runtime import ReplayBuffer


class LinearDummyPolicy:
    def __init__(self, obs_dim: int, *, rng: np.random.Generator | None = None) -> None:
        if obs_dim < 1:
            raise ValueError("obs_dim must be >= 1.")
        self._rng = rng if rng is not None else np.random.default_rng()
        scale = 0.01
        self._w = self._rng.normal(scale=scale, size=(POLICY_RAW_DIM, obs_dim)).astype(
            np.float64
        )
        self._b = self._rng.normal(scale=scale, size=(POLICY_RAW_DIM,)).astype(np.float64)

    @property
    def w(self) -> np.ndarray:
        return self._w

    @property
    def b(self) -> np.ndarray:
        return self._b

    def forward(self, obs: np.ndarray) -> np.ndarray:
        if obs.shape != (self._w.shape[1],):
            raise ValueError(f"Expected obs shape ({self._w.shape[1]},), got {obs.shape}.")
        return (self._w @ obs + self._b).astype(np.float64)


class MPOAgent:
    def __init__(self, env: Any, config: MPOConfig | None = None) -> None:
        self.config = config if config is not None else MPOConfig()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")

        self.obs_size = int(np.prod(env.observation_space.shape))
        self.action_size = int(np.prod(env.action_space.shape))
        self.action_low = torch.tensor(env.action_space.low, dtype=torch.float32, device=self.device)
        self.action_high = torch.tensor(
            env.action_space.high, dtype=torch.float32, device=self.device
        )
        self.action_scale = (self.action_high - self.action_low) / 2
        self.action_bias = (self.action_high + self.action_low) / 2

        self.pi = Actor(
            self.action_low,
            self.action_high,
            self.obs_size,
            self.action_size,
            self.config.num_layers_actor,
            self.config.num_units_actor,
            self.config.activation_actor,
            self.config.actor_dropout,
        ).to(self.device)
        self.pi_target = Actor(
            self.action_low,
            self.action_high,
            self.obs_size,
            self.action_size,
            self.config.num_layers_actor,
            self.config.num_units_actor,
            self.config.activation_actor,
            self.config.actor_dropout,
        ).to(self.device)

        self.q1 = Critic(
            self.obs_size,
            self.action_size,
            self.config.num_layers_critic,
            self.config.num_units_critic,
        ).to(self.device)
        self.q2 = Critic(
            self.obs_size,
            self.action_size,
            self.config.num_layers_critic,
            self.config.num_units_critic,
        ).to(self.device)
        self.q1_target = Critic(
            self.obs_size,
            self.action_size,
            self.config.num_layers_critic,
            self.config.num_units_critic,
        ).to(self.device)
        self.q2_target = Critic(
            self.obs_size,
            self.action_size,
            self.config.num_layers_critic,
            self.config.num_units_critic,
        ).to(self.device)
        self.q1_target.load_state_dict(self.q1.state_dict())
        self.q2_target.load_state_dict(self.q2.state_dict())
        self.pi_target.load_state_dict(self.pi.state_dict())

        self.q_optimizer = optim.Adam(
            list(self.q2.parameters()) + list(self.q1.parameters()),
            lr=self.config.learning_rate_q,
        )
        self.pi_optimizer = optim.Adam(self.pi.parameters(), lr=self.config.learning_rate_pi)
        self.log_eta = torch.tensor(1.0, device=self.device, requires_grad=True)
        self.eta_optimizer = optim.Adam([self.log_eta], lr=self.config.learning_rate_eta)

        self.buffer = ReplayBuffer(
            self.config.buffer_size, self.obs_size, self.action_size, self.device
        )
        self.step_counter = 0
        self.current_ep_return = 0.0
        self.episode_returns: list[float] = []
        self.lr_reduction_stage = 0
        self.current_actor_lr = self.config.learning_rate_pi
        self.exploration_steps = self.config.warmup_episodes * self.config.max_steps_per_episode
        self.metrics: dict[str, list[float]] = {
            "qloss": [],
            "piloss": [],
            "etaloss": [],
            "eta": [],
            "kl": [],
            "return": [],
        }

    def _soft_update(self, target: nn.Module, source: nn.Module) -> None:
        for target_param, param in zip(target.parameters(), source.parameters()):
            target_param.data.copy_(
                self.config.tau * param.data + (1.0 - self.config.tau) * target_param.data
            )

    def _maybe_schedule_actor_lr(self, last_return: float) -> None:
        if self.lr_reduction_stage >= 2 or not self.config.learn_rate_scheduling:
            return
        new_lr = self.current_actor_lr
        if last_return >= -100 and self.lr_reduction_stage < 1:
            new_lr = self.current_actor_lr / 2
            self.lr_reduction_stage = 1
        if last_return >= -30 and self.lr_reduction_stage < 2:
            new_lr = self.current_actor_lr / 5
            self.lr_reduction_stage = 2
        if new_lr != self.current_actor_lr:
            for group in self.pi_optimizer.param_groups:
                group["lr"] = new_lr
            self.current_actor_lr = new_lr

    def train(self) -> dict[str, float] | None:
        if len(self.buffer) < self.config.batch_size or self.step_counter < self.exploration_steps:
            return None

        obs, action, next_obs, done, reward = self.buffer.sample(self.config.batch_size)
        last_return = self.episode_returns[-1] if self.episode_returns else -200.0
        self.metrics["return"].append(float(last_return))
        self._maybe_schedule_actor_lr(last_return)

        with torch.no_grad():
            dist_target = self.pi_target(next_obs)
            next_actions_samples = dist_target.sample((self.config.num_samples_q,))
            next_actions_rescaled = (
                torch.tanh(next_actions_samples) * self.action_scale + self.action_bias
            )
            next_obs_expanded = next_obs.unsqueeze(0).repeat(self.config.num_samples_q, 1, 1)
            q_target_all = torch.min(
                self.q1_target(next_obs_expanded, next_actions_rescaled),
                self.q2_target(next_obs_expanded, next_actions_rescaled),
            )
            q_next = q_target_all.reshape(self.config.num_samples_q, self.config.batch_size, 1).mean(
                dim=0
            )
            y = reward.unsqueeze(1) + (1 - done.unsqueeze(1)) * self.config.gamma * q_next

        loss_fn = nn.MSELoss()
        q1_loss = loss_fn(self.q1(obs, action), y)
        q2_loss = loss_fn(self.q2(obs, action), y)
        q_loss = q1_loss + q2_loss
        self.metrics["qloss"].append(float(q_loss.item()))

        self.q_optimizer.zero_grad()
        q_loss.backward()
        self.q_optimizer.step()

        dist_online = self.pi(obs)
        actions_gaussian = dist_online.rsample((self.config.num_samples_pi,))
        actions_tanh = torch.tanh(actions_gaussian)
        actions_squashed = actions_tanh * self.action_scale + self.action_bias
        obs_expanded = obs.unsqueeze(0).repeat(self.config.num_samples_pi, 1, 1)
        q1_values_samples = self.q1(obs_expanded, actions_squashed).detach()

        eta = torch.exp(self.log_eta).detach()
        self.metrics["eta"].append(float(eta.item()))
        weights = torch.softmax(q1_values_samples / eta, dim=0).squeeze(-1)

        log_prob_gaussian = dist_online.log_prob(actions_gaussian).sum(-1)
        jacobian = torch.log(1 - actions_tanh.pow(2) + 1e-6).sum(-1)
        log_prob_samples = log_prob_gaussian - jacobian
        pi_loss = -(weights * log_prob_samples).mean()
        self.metrics["piloss"].append(float(pi_loss.item()))

        self.pi_optimizer.zero_grad()
        pi_loss.backward()
        self.pi_optimizer.step()

        dist_new = self.pi(obs)
        if self.config.decoupled_kl:
            kl_mu = 0.5 * torch.mean(
                ((dist_online.loc - dist_new.loc) ** 2) / (dist_new.scale**2 + 1e-8)
            )
            kl_sigma = torch.mean(
                torch.log(dist_new.scale / (dist_online.scale + 1e-8) + 1e-8)
                - 1
                + (dist_online.scale**2 + 1e-8) / (dist_new.scale**2 + 1e-8)
                + ((dist_online.loc - dist_new.loc) ** 2) / (2 * (dist_new.scale**2 + 1e-8))
            )
            kl = kl_mu + kl_sigma
            eta_loss = torch.exp(self.log_eta) * (self.config.target_kl_mu - kl_mu).detach()
            eta_loss = eta_loss + torch.exp(self.log_eta) * (
                self.config.target_kl_sigma - kl_sigma
            ).detach()
        else:
            with torch.no_grad():
                if self.config.reverse_kl:
                    kl = torch.distributions.kl_divergence(dist_new, dist_online).mean()
                else:
                    kl = torch.distributions.kl_divergence(dist_online, dist_new).mean()
            target_kl = self.config.target_kl_mu + self.config.target_kl_sigma
            eta_loss = torch.exp(self.log_eta) * (target_kl - kl).detach()

        self.metrics["kl"].append(float(kl.item()))
        self.metrics["etaloss"].append(float(eta_loss.item()))

        self.eta_optimizer.zero_grad()
        eta_loss.backward()
        self.eta_optimizer.step()

        self._soft_update(self.q1_target, self.q1)
        self._soft_update(self.q2_target, self.q2)
        self._soft_update(self.pi_target, self.pi)

        return {
            "q_loss": float(q_loss.item()),
            "pi_loss": float(pi_loss.item()),
            "eta_loss": float(eta_loss.item()),
            "eta": float(torch.exp(self.log_eta).item()),
            "kl": float(kl.item()),
        }

    def get_action(self, obs: np.ndarray, train: bool) -> np.ndarray:
        obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=self.device)
        if train and self.step_counter < self.exploration_steps:
            return np.array([np.random.uniform(-1.0, 1.0)], dtype=np.float64)

        with torch.no_grad():
            dist = self.pi(obs_tensor)
            action_gaussian = dist.rsample() if train else dist.mean
            action_scaled = torch.tanh(action_gaussian) * self.action_scale + self.action_bias
        return action_scaled.detach().cpu().numpy().astype(np.float64)

    def store(self, transition: tuple[np.ndarray, np.ndarray, float, np.ndarray, bool]) -> None:
        obs, action, reward, next_obs, done = transition
        self.current_ep_return += float(reward)
        self.step_counter += 1
        if done:
            self.episode_returns.append(self.current_ep_return)
            self.current_ep_return = 0.0
        self.buffer.store(obs, next_obs, action, reward, done)
