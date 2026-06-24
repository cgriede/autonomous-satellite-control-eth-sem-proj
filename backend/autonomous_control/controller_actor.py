"""Actor network used by the MPO agent."""

from __future__ import annotations

import torch
import torch.nn as nn

from .controller_encoder import ControllerEncoder
from .controller_observation import ControllerObservationLayout
from .MLP_model import MLP, init_weights_he, init_weights_xavier
from .mpo_config import LOG_STD_MAX, LOG_STD_MIN, MPOConfig


class Actor(nn.Module):
    """Gaussian stochastic actor returning a Normal distribution."""

    def __init__(
        self,
        action_low: torch.Tensor,
        action_high: torch.Tensor,
        layout: ControllerObservationLayout,
        action_size: int,
        config: MPOConfig,
    ) -> None:
        super().__init__()
        self.action_scale = (action_high - action_low) / 2
        self.action_bias = (action_high + action_low) / 2
        self.action_size = action_size
        self.encoder = ControllerEncoder(
            layout,
            config,
            activation=config.activation_actor,
        )
        trunk_dim = self.encoder.output_dim
        self.head = MLP(
            sizes=[trunk_dim]
            + ([config.num_units_actor] * config.num_layers_actor)
            + [2 * action_size],
            activation=config.activation_actor,
            dropout=config.actor_dropout,
        )

        if config.activation_actor == nn.ReLU:
            self.head.apply(self._init_actor_weights)
        elif config.activation_actor == nn.Tanh:
            self.head.apply(init_weights_xavier)
        else:
            self.head.apply(init_weights_he)

    def _init_actor_weights(self, module: nn.Module) -> None:
        if not isinstance(module, nn.Linear):
            return
        if module.out_features == 2 * self.action_size:
            fan_in = module.weight.data.size(1)
            bound_mean = 0.01 / fan_in**0.5
            bound_std = 1.0 / fan_in**0.5
            nn.init.uniform_(
                module.weight.data[: self.action_size], -bound_mean, bound_mean
            )
            nn.init.uniform_(
                module.weight.data[self.action_size :], -bound_std, bound_std
            )
            nn.init.zeros_(module.bias.data)
            return
        nn.init.orthogonal_(module.weight, gain=1.0)
        nn.init.zeros_(module.bias.data)

    def forward(
        self,
        scalars: torch.Tensor,
        vision_codes: tuple[torch.Tensor, ...],
    ) -> torch.distributions.Normal:
        features = self.encoder(scalars, vision_codes)
        mu, log_std = torch.chunk(self.head(features), 2, dim=-1)
        log_std = torch.clamp(log_std, LOG_STD_MIN, LOG_STD_MAX)
        std = torch.exp(log_std)
        return torch.distributions.Normal(mu, std)
