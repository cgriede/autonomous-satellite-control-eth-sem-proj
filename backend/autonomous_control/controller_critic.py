"""Critic network used by the MPO agent."""

from __future__ import annotations

import torch
import torch.nn as nn

from .controller_encoder import ControllerEncoder
from .controller_observation import ControllerObservationLayout
from .MLP_model import MLP
from .mpo_config import MPOConfig


class Critic(nn.Module):
    """MLP Q-function on encoded observations and actions."""

    def __init__(
        self,
        layout: ControllerObservationLayout,
        action_size: int,
        config: MPOConfig,
    ) -> None:
        super().__init__()
        self.encoder = ControllerEncoder(layout, config, activation=nn.ReLU)
        trunk_dim = self.encoder.output_dim
        self.head = MLP(
            [trunk_dim + action_size]
            + ([config.num_units_critic] * config.num_layers_critic)
            + [1]
        )

    def forward(
        self,
        scalars: torch.Tensor,
        vision_codes: tuple[torch.Tensor, ...],
        actions: torch.Tensor,
    ) -> torch.Tensor:
        features = self.encoder(scalars, vision_codes)
        return self.head(torch.cat([features, actions], dim=-1))
