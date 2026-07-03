"""Factored MPO agent fork: Categorical target + Gaussian move/shutter."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

from autonomous_control.controller_critic import Critic
from autonomous_control.controller_observation import (
    ControllerObservation,
    controller_observation_to_tensors,
)
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.training_runtime import ReplayBuffer

from _action_constants import N_ACTION_DIMS, N_TARGETS
from _env_adapter_fork import make_exp14_attitude_control_env
from _factorized_actor import FactoredActor


def _require_observation_layout(env: Any):
    layout = getattr(env, "observation_layout", None)
    if layout is None:
        raise ValueError("env must expose observation_layout for FactoredMPOAgent.")
    return layout


class FactoredMPOAgent:
    def __init__(
        self,
        env: Any,
        config: MPOConfig | None = None,
        *,
        n_targets: int = N_TARGETS,
        entropy_coef: float = 0.01,
    ) -> None:
        self.config = config if config is not None else MPOConfig()
        self.n_targets = int(n_targets)
        self.entropy_coef = float(entropy_coef)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")

        self.layout = _require_observation_layout(env)
        self.obs_size = int(np.prod(env.observation_space.shape))
        self.action_size = N_ACTION_DIMS
        self.action_low = torch.tensor(env.action_space.low, dtype=torch.float32, device=self.device)
        self.action_high = torch.tensor(env.action_space.high, dtype=torch.float32, device=self.device)

        actor_cfg = replace(self.config, max_target_index=max(self.n_targets - 1, 0))
        self.pi = FactoredActor(self.layout, self.n_targets, actor_cfg).to(self.device)
        self.pi_target = FactoredActor(self.layout, self.n_targets, actor_cfg).to(self.device)

        self.q1 = Critic(self.layout, self.action_size, self.config).to(self.device)
        self.q2 = Critic(self.layout, self.action_size, self.config).to(self.device)
        self.q1_target = Critic(self.layout, self.action_size, self.config).to(self.device)
        self.q2_target = Critic(self.layout, self.action_size, self.config).to(self.device)
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
        self.log_alpha_mu = torch.tensor(0.0, device=self.device, requires_grad=True)
        self.log_alpha_sigma = torch.tensor(0.0, device=self.device, requires_grad=True)
        self.alpha_optimizer = optim.Adam(
            [self.log_alpha_mu, self.log_alpha_sigma],
            lr=self.config.learning_rate_alpha,
        )

        self.buffer = ReplayBuffer(
            self.config.buffer_size,
            self.layout,
            self.action_size,
            self.device,
        )
        self.step_counter = 0
        self.current_ep_return = 0.0
        self.episode_returns: list[float] = []
        self.metrics: dict[str, list[float]] = {
            "qloss": [],
            "piloss": [],
            "etaloss": [],
            "eta": [],
            "kl": [],
            "kl_mu": [],
            "kl_sigma": [],
            "alpha_mu": [],
            "alpha_sigma": [],
            "return": [],
        }

    def reset_episode(self) -> None:
        pass

    def clear_buffer(self) -> None:
        self.buffer = ReplayBuffer(
            self.config.buffer_size,
            self.layout,
            self.action_size,
            self.device,
        )

    def _soft_update(self, target: nn.Module, source: nn.Module) -> None:
        for target_param, param in zip(target.parameters(), source.parameters()):
            target_param.data.copy_(
                self.config.tau * param.data + (1.0 - self.config.tau) * target_param.data
            )

    def _obs_tensors(
        self, obs: ControllerObservation
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, ...]]:
        return controller_observation_to_tensors(obs, device=self.device)

    def _expand_obs_for_samples(
        self,
        scalars: torch.Tensor,
        vision: tuple[torch.Tensor, ...],
        num_samples: int,
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, ...], int]:
        batch_size = int(scalars.shape[0])
        scalars_expanded = (
            scalars.unsqueeze(0)
            .repeat(num_samples, 1, 1)
            .reshape(num_samples * batch_size, -1)
        )
        vision_expanded = tuple(
            codes.unsqueeze(0)
            .repeat(num_samples, 1, 1)
            .reshape(num_samples * batch_size, codes.shape[-1])
            for codes in vision
        )
        return scalars_expanded, vision_expanded, batch_size

    def _decoupled_kl(
        self,
        mu_online: torch.Tensor,
        std_online: torch.Tensor,
        mu_ref: torch.Tensor,
        std_ref: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        kl_mu = 0.5 * torch.mean(
            ((mu_ref - mu_online) ** 2) / (std_online**2 + 1e-8)
        )
        kl_sigma = torch.mean(
            torch.log(std_online / (std_ref + 1e-8) + 1e-8)
            - 1
            + (std_ref**2 + 1e-8) / (std_online**2 + 1e-8)
            + ((mu_ref - mu_online) ** 2) / (2 * (std_online**2 + 1e-8))
        )
        return kl_mu, kl_sigma, kl_mu + kl_sigma

    def train(self) -> dict[str, float] | None:
        if len(self.buffer) < self.config.batch_size:
            return None

        (obs_scalars, obs_vision), action, (next_scalars, next_vision), done, reward = (
            self.buffer.sample(self.config.batch_size)
        )
        last_return = self.episode_returns[-1] if self.episode_returns else -200.0
        self.metrics["return"].append(float(last_return))

        with torch.no_grad():
            dist_target = self.pi_target(next_scalars, next_vision)
            next_actions_squashed = self.pi_target.sample_stored_actions(
                dist_target,
                self.config.num_samples_q,
            )
            next_actions_flat = next_actions_squashed.reshape(
                self.config.num_samples_q * self.config.batch_size, -1
            )
            next_scalars_expanded, next_vision_expanded, _ = self._expand_obs_for_samples(
                next_scalars, next_vision, self.config.num_samples_q
            )
            q_target_all = torch.min(
                self.q1_target(next_scalars_expanded, next_vision_expanded, next_actions_flat),
                self.q2_target(next_scalars_expanded, next_vision_expanded, next_actions_flat),
            )
            q_next = q_target_all.reshape(
                self.config.num_samples_q, self.config.batch_size, 1
            ).mean(dim=0)
            y = reward.unsqueeze(1) + (1 - done.unsqueeze(1)) * self.config.gamma * q_next

        loss_fn = nn.MSELoss()
        q1_loss = loss_fn(self.q1(obs_scalars, obs_vision, action), y)
        q2_loss = loss_fn(self.q2(obs_scalars, obs_vision, action), y)
        q_loss = q1_loss + q2_loss
        self.metrics["qloss"].append(float(q_loss.item()))

        self.q_optimizer.zero_grad()
        q_loss.backward()
        self.q_optimizer.step()

        dist_online = self.pi(obs_scalars, obs_vision)
        actions_squashed = self.pi.sample_stored_actions(
            dist_online,
            self.config.num_samples_pi,
        )
        obs_scalars_expanded, obs_vision_expanded, _ = self._expand_obs_for_samples(
            obs_scalars, obs_vision, self.config.num_samples_pi
        )
        actions_flat = actions_squashed.reshape(
            self.config.num_samples_pi * self.config.batch_size, -1
        )
        q1_values_samples = self.q1(
            obs_scalars_expanded, obs_vision_expanded, actions_flat
        ).detach().reshape(self.config.num_samples_pi, self.config.batch_size, 1)

        eta = torch.exp(self.log_eta).detach()
        self.metrics["eta"].append(float(eta.item()))
        weights = torch.softmax(q1_values_samples / eta, dim=0).squeeze(-1)

        with torch.no_grad():
            dist_ref = self.pi_target(obs_scalars, obs_vision)

        mu_online, std_online = self.pi.continuous_kl_params(dist_online)
        mu_ref, std_ref = self.pi.continuous_kl_params(dist_ref)
        kl_mu, kl_sigma, kl = self._decoupled_kl(mu_online, std_online, mu_ref, std_ref)

        alpha_mu = torch.exp(self.log_alpha_mu).detach()
        alpha_sigma = torch.exp(self.log_alpha_sigma).detach()
        self.metrics["alpha_mu"].append(float(alpha_mu.item()))
        self.metrics["alpha_sigma"].append(float(alpha_sigma.item()))

        # Detach samples: actions come from rsample() of dist_online, so without detach
        # the score-function gradient and the reparameterization gradient cancel exactly to
        # zero for the Gaussian heads (atanh∘tanh = identity → chain rule gives -1 × +1 = 0).
        # Detaching fixes gradient flow for move/shutter heads in the M-step.
        log_prob_samples = self.pi.log_prob(dist_online, actions_squashed.detach())
        target_entropy = dist_online["target"].entropy()

        pi_loss = (
            -(weights * log_prob_samples).mean()
            + alpha_mu * kl_mu
            + alpha_sigma * kl_sigma
            - self.entropy_coef * target_entropy.mean()
        )
        self.metrics["piloss"].append(float(pi_loss.item()))

        self.pi_optimizer.zero_grad()
        pi_loss.backward()
        self.pi_optimizer.step()

        eta_var = torch.exp(self.log_eta)
        max_q = q1_values_samples.max(dim=0, keepdim=True).values
        log_mean_exp_q = (
            torch.log(torch.exp((q1_values_samples - max_q) / eta_var).mean(dim=0) + 1e-8)
            + max_q / eta_var
        )
        eta_loss = eta_var * self.config.eps_eta + eta_var * log_mean_exp_q.mean()
        self.metrics["etaloss"].append(float(eta_loss.item()))

        self.eta_optimizer.zero_grad()
        eta_loss.backward()
        self.eta_optimizer.step()

        alpha_mu_loss = -torch.exp(self.log_alpha_mu) * (kl_mu.detach() - self.config.target_kl_mu)
        alpha_sigma_loss = -torch.exp(self.log_alpha_sigma) * (
            kl_sigma.detach() - self.config.target_kl_sigma
        )
        alpha_loss = alpha_mu_loss + alpha_sigma_loss

        self.alpha_optimizer.zero_grad()
        alpha_loss.backward()
        self.alpha_optimizer.step()

        self.metrics["kl"].append(float(kl.item()))
        self.metrics["kl_mu"].append(float(kl_mu.item()))
        self.metrics["kl_sigma"].append(float(kl_sigma.item()))

        self._soft_update(self.q1_target, self.q1)
        self._soft_update(self.q2_target, self.q2)
        self._soft_update(self.pi_target, self.pi)

        return {
            "q_loss": float(q_loss.item()),
            "pi_loss": float(pi_loss.item()),
            "eta_loss": float(eta_loss.item()),
            "eta": float(torch.exp(self.log_eta).item()),
            "kl": float(kl.item()),
            "kl_mu": float(kl_mu.item()),
            "kl_sigma": float(kl_sigma.item()),
            "alpha_mu": float(alpha_mu.item()),
            "alpha_sigma": float(alpha_sigma.item()),
        }

    def get_action(self, obs: ControllerObservation, train: bool) -> np.ndarray:
        scalars, vision = self._obs_tensors(obs)
        with torch.no_grad():
            dists = self.pi(scalars, vision)
            sample = self.pi.sample_stored_action(dists, greedy=not train)
        return sample.action[0].cpu().numpy().astype(np.float32)

    def store(
        self,
        transition: tuple[ControllerObservation, np.ndarray, float, ControllerObservation, bool],
    ) -> None:
        obs, action, reward, next_obs, done = transition
        self.current_ep_return += float(reward)
        self.step_counter += 1
        if done:
            self.episode_returns.append(self.current_ep_return)
            self.current_ep_return = 0.0
        self.buffer.store(obs, next_obs, action, reward, done)


def build_factored_mpo_agent(
    *,
    mpo_config: MPOConfig,
    feature_config,
    secondary_camera_bins: int,
    n_mission_targets: int,
    observation_layout,
    entropy_coef: float = 0.01,
) -> FactoredMPOAgent:
    env = make_exp14_attitude_control_env(
        reward_config=mpo_config.reward,
        feature_config=feature_config,
        secondary_camera_observation_line_n_bins=secondary_camera_bins,
        n_mission_targets=n_mission_targets,
        observation_layout=observation_layout,
    )
    return FactoredMPOAgent(
        env,
        config=mpo_config,
        n_targets=n_mission_targets,
        entropy_coef=entropy_coef,
    )


__all__ = ["FactoredMPOAgent", "build_factored_mpo_agent"]
