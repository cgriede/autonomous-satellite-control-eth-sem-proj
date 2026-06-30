"""Central MPO hyperparameter configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

import torch.nn as nn

from environment_definition.constants.SIMULATION import SIMULATION

from .reward import RewardConfig

LOG_STD_MAX = 2.0
LOG_STD_MIN = -5.0


@dataclass(frozen=True)
class MPOConfig:
    buffer_size: int = 50_000
    tau: float = 0.005
    learning_rate_q: float = 4.5e-4
    learning_rate_pi: float = 1.5e-4
    learning_rate_eta: float = 1.0e-3
    target_kl_mu: float = 0.1
    target_kl_sigma: float = 0.01
    eps_eta: float = 0.1
    learning_rate_alpha: float = 1e-3
    num_samples_q: int = 80
    num_samples_pi: int = 40
    num_layers_actor: int = 1
    num_units_actor: int = 90
    actor_dropout: float = 0.15
    num_layers_critic: int = 2
    num_units_critic: int = 140
    batch_size: int = 256
    gamma: float = 0.99
    warmup_episodes: int = 10
    learn_rate_scheduling: bool = False
    activation_actor: type[nn.Module] = nn.ELU
    reverse_kl: bool = False
    decoupled_kl: bool = True
    code_embed_dim: int = 8
    cnn_embedding_dim: int = 32
    num_cnn_layers: int = 2
    num_layers_scalar_encoder: int = 1
    num_layers_vision_fusion: int = 1
    max_target_index: int = 35
    max_steps_per_episode: int = int(SIMULATION.max_episode_steps)
    # Per-component reward flags (routed into env and run_simulation via training
    # runtime / render call sites). See autonomous_control.reward for semantics.
    reward: RewardConfig = field(default_factory=RewardConfig)

    def __post_init__(self) -> None:
        if self.num_cnn_layers not in (1, 2, 3):
            raise ValueError("num_cnn_layers must be 1, 2, or 3.")


__all__ = ["MPOConfig", "RewardConfig", "LOG_STD_MAX", "LOG_STD_MIN"]
