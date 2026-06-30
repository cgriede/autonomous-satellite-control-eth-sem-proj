"""Actor with flat (A0) or compressed (A1) encoder."""

from __future__ import annotations

from typing import Literal

import torch
import torch.nn as nn

from autonomous_control.controller_encoder import ControllerEncoder
from autonomous_control.controller_observation import ControllerObservationLayout
from autonomous_control.MLP_model import MLP, init_weights_he, init_weights_xavier
from autonomous_control.mpo_config import LOG_STD_MAX, LOG_STD_MIN, MPOConfig

from encoders.compressed_controller_encoder import CompressedControllerEncoder

EncoderMode = Literal["flat", "compress"]


class ModularActor(nn.Module):
    def __init__(
        self,
        action_low: torch.Tensor,
        action_high: torch.Tensor,
        layout: ControllerObservationLayout,
        action_size: int,
        config: MPOConfig,
        *,
        encoder_mode: EncoderMode = "flat",
        vector_embed_dim: int = 8,
    ) -> None:
        super().__init__()
        self.action_scale = (action_high - action_low) / 2
        self.action_bias = (action_high + action_low) / 2
        self.action_size = action_size
        activation = config.activation_actor
        if encoder_mode == "compress":
            self.encoder = CompressedControllerEncoder(
                layout,
                config,
                vector_embed_dim=vector_embed_dim,
                activation=activation,
            )
        else:
            self.encoder = ControllerEncoder(layout, config, activation=activation)
        trunk_dim = self.encoder.output_dim
        self.head = MLP(
            sizes=[trunk_dim]
            + ([config.num_units_actor] * config.num_layers_actor)
            + [2 * action_size],
            activation=activation,
            dropout=config.actor_dropout,
        )
        if activation == nn.ReLU:
            self.head.apply(self._init_actor_weights)
        elif activation == nn.Tanh:
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
            nn.init.uniform_(module.weight.data[: self.action_size], -bound_mean, bound_mean)
            nn.init.uniform_(module.weight.data[self.action_size :], -bound_std, bound_std)
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
        return torch.distributions.Normal(mu, torch.exp(log_std))
