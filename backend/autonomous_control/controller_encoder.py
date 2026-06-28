"""Dual-path controller encoder: scalar MLP + vision 1D-CNN fusion."""

from __future__ import annotations

from dataclasses import replace

import torch
import torch.nn as nn

from .CNN_1d import (
    CNN1DEncoderConfig,
    ObservationLineCNNEncoder,
    cnn_vision_conv_stack,
)
from .controller_observation import ControllerObservationLayout
from .MLP_model import MLP
from .mpo_config import MPOConfig


class ControllerEncoder(nn.Module):
    """Encode scalar features and vision code lines into one latent vector.

    Architecture::

        s1, s2, … -> scalar MLP -> h_scalar
        v1, v2, … -> 1D-CNN each -> concat -> vision MLP -> h_vision
        output = concat(h_scalar, h_vision)
    """

    def __init__(
        self,
        layout: ControllerObservationLayout,
        config: MPOConfig,
        *,
        activation: type[nn.Module] = nn.ReLU,
    ) -> None:
        super().__init__()
        self.layout = layout
        scalar_width = int(config.num_units_actor)
        vision_width = int(config.num_units_actor)
        scalar_sizes = [layout.scalar_dim] + [scalar_width] * int(
            config.num_layers_scalar_encoder
        )
        self.scalar_net = MLP(
            scalar_sizes,
            activation=activation,
            dropout=0.0,
        )

        conv_channels, kernel_sizes, strides = cnn_vision_conv_stack(
            int(config.num_cnn_layers),
        )
        cnn_template = CNN1DEncoderConfig(
            code_embed_dim=int(config.code_embed_dim),
            embedding_dim=int(config.cnn_embedding_dim),
            max_target_index=int(config.max_target_index),
            conv_channels=conv_channels,
            kernel_sizes=kernel_sizes,
            strides=strides,
        )
        self.vision_encoders = nn.ModuleList(
            ObservationLineCNNEncoder(
                replace(cnn_template, seq_len=int(seq_len)),
            )
            for seq_len in layout.vision_seq_lens
        )
        vision_in_dim = sum(int(enc.embedding_dim) for enc in self.vision_encoders)
        if vision_in_dim > 0:
            vision_sizes = [vision_in_dim] + [vision_width] * int(
                config.num_layers_vision_fusion
            )
            self.vision_net: nn.Module | None = MLP(
                vision_sizes,
                activation=activation,
                dropout=0.0,
            )
            self._output_dim = scalar_width + vision_width
        else:
            self.vision_net = None
            self._output_dim = scalar_width

    @property
    def output_dim(self) -> int:
        return int(self._output_dim)

    def forward(
        self,
        scalars: torch.Tensor,
        vision_codes: tuple[torch.Tensor, ...],
    ) -> torch.Tensor:
        if scalars.ndim == 1:
            scalars = scalars.unsqueeze(0)
        if scalars.ndim != 2:
            raise ValueError(f"Expected scalars (batch, S), got {tuple(scalars.shape)}.")
        if len(vision_codes) != len(self.vision_encoders):
            raise ValueError(
                f"Expected {len(self.vision_encoders)} vision streams, got {len(vision_codes)}."
            )

        h_scalar = self.scalar_net(scalars)
        if not self.vision_encoders:
            return h_scalar

        vision_embeddings = [
            encoder(codes) for encoder, codes in zip(self.vision_encoders, vision_codes)
        ]
        assert self.vision_net is not None
        h_vision = self.vision_net(torch.cat(vision_embeddings, dim=-1))
        return torch.cat([h_scalar, h_vision], dim=-1)


__all__ = ["ControllerEncoder"]
