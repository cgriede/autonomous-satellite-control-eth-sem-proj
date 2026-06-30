"""A1 encoder: passthrough scalars + Linear compressors on bearing/mask vectors."""

from __future__ import annotations

from dataclasses import replace

import torch
import torch.nn as nn

from autonomous_control.CNN_1d import (
    CNN1DEncoderConfig,
    ObservationLineCNNEncoder,
    cnn_vision_conv_stack,
)
from autonomous_control.controller_observation import ControllerObservationLayout
from autonomous_control.MLP_model import MLP
from autonomous_control.mpo_config import MPOConfig

from encoders.scalar_split import gather_columns, scalar_group_indices


class CompressedControllerEncoder(nn.Module):
    """Passthrough globals + vector compressors + vision CNN fusion."""

    def __init__(
        self,
        layout: ControllerObservationLayout,
        config: MPOConfig,
        *,
        vector_embed_dim: int = 8,
        activation: type[nn.Module] = nn.ReLU,
    ) -> None:
        super().__init__()
        self.layout = layout
        self.groups = scalar_group_indices(layout)
        embed = int(vector_embed_dim)
        scalar_width = int(config.num_units_actor)
        vision_width = int(config.num_units_actor)

        self.bearing_compress: nn.Module | None = None
        self.mask_compress: nn.Module | None = None
        if self.groups.bearing_dim > 0:
            self.bearing_compress = nn.Sequential(
                nn.Linear(self.groups.bearing_dim, embed),
                activation(),
            )
        if self.groups.mask_dim > 0:
            self.mask_compress = nn.Sequential(
                nn.Linear(self.groups.mask_dim, embed),
                activation(),
            )

        scalar_in_dim = self.groups.passthrough_dim + (
            embed if self.bearing_compress is not None else 0
        ) + (embed if self.mask_compress is not None else 0)
        scalar_sizes = [scalar_in_dim] + [scalar_width] * int(config.num_layers_scalar_encoder)
        self.scalar_net = MLP(scalar_sizes, activation=activation, dropout=0.0)

        conv_channels, kernel_sizes, strides = cnn_vision_conv_stack(int(config.num_cnn_layers))
        cnn_template = CNN1DEncoderConfig(
            code_embed_dim=int(config.code_embed_dim),
            embedding_dim=int(config.cnn_embedding_dim),
            max_target_index=int(config.max_target_index),
            conv_channels=conv_channels,
            kernel_sizes=kernel_sizes,
            strides=strides,
        )
        self.vision_encoders = nn.ModuleList(
            ObservationLineCNNEncoder(replace(cnn_template, seq_len=int(seq_len)))
            for seq_len in layout.vision_seq_lens
        )
        vision_in_dim = sum(int(enc.embedding_dim) for enc in self.vision_encoders)
        if vision_in_dim > 0:
            vision_sizes = [vision_in_dim] + [vision_width] * int(config.num_layers_vision_fusion)
            self.vision_net: nn.Module | None = MLP(
                vision_sizes, activation=activation, dropout=0.0
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
        parts: list[torch.Tensor] = [gather_columns(scalars, self.groups.passthrough)]
        if self.bearing_compress is not None:
            parts.append(self.bearing_compress(gather_columns(scalars, self.groups.bearing)))
        if self.mask_compress is not None:
            parts.append(self.mask_compress(gather_columns(scalars, self.groups.mask)))
        h_scalar = self.scalar_net(torch.cat(parts, dim=-1))

        if not self.vision_encoders:
            return h_scalar
        if len(vision_codes) != len(self.vision_encoders):
            raise ValueError(
                f"Expected {len(self.vision_encoders)} vision streams, got {len(vision_codes)}."
            )
        vision_embeddings = [
            encoder(codes) for encoder, codes in zip(self.vision_encoders, vision_codes)
        ]
        assert self.vision_net is not None
        h_vision = self.vision_net(torch.cat(vision_embeddings, dim=-1))
        return torch.cat([h_scalar, h_vision], dim=-1)
