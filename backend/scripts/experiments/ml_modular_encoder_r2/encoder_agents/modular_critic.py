"""Critic with flat (A0) or compressed (A1) encoder."""

from __future__ import annotations

from typing import Literal

import torch
import torch.nn as nn

from autonomous_control.controller_encoder import ControllerEncoder
from autonomous_control.controller_observation import ControllerObservationLayout
from autonomous_control.MLP_model import MLP
from autonomous_control.mpo_config import MPOConfig

from encoders.compressed_controller_encoder import CompressedControllerEncoder

EncoderMode = Literal["flat", "compress"]


class ModularCritic(nn.Module):
    def __init__(
        self,
        layout: ControllerObservationLayout,
        action_size: int,
        config: MPOConfig,
        *,
        encoder_mode: EncoderMode = "flat",
        vector_embed_dim: int = 8,
    ) -> None:
        super().__init__()
        if encoder_mode == "compress":
            self.encoder = CompressedControllerEncoder(
                layout,
                config,
                vector_embed_dim=vector_embed_dim,
                activation=nn.ReLU,
            )
        else:
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
