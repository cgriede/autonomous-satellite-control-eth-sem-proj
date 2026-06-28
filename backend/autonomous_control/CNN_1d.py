"""1D-CNN vision encoder for observation-line code arrays.

Simulation outputs one int8 label per cross-track bin (space / earth / cloud / target).
:class:`ObservationLineCNNEncoder` embeds those codes and runs a shared :class:`CNN1DEncoder`
stack. Instantiate one encoder per camera (primary / secondary) with that camera's bin count.

:class:`CNN1DEncoder` is also usable directly on any ``(batch, C, L)`` float tensor.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
import torch
import torch.nn as nn

from environment_definition.constants.SIMULATION import (
    OBSERVATION_CLOUD,
    OBSERVATION_EARTH,
    OBSERVATION_LINE_NOT_COMPUTED,
    OBSERVATION_SPACE,
    OBSERVATION_TARGET,
)

# Embedding index 0 is reserved for unknown / out-of-vocabulary codes.
_UNKNOWN_CODE_INDEX = 0
_NOT_COMPUTED_CODE_INDEX = 1
_SPACE_CODE_INDEX = 2
_EARTH_CODE_INDEX = 3
_CLOUD_CODE_INDEX = 4
_TARGET_CODE_INDEX_BASE = 5
_INT8_LUT_OFFSET = 128


def _build_code_index_lut(*, max_target_index: int) -> torch.Tensor:
    """Map int8 observation codes to contiguous embedding indices via ``code + 128``."""
    if max_target_index < 0:
        raise ValueError("max_target_index must be >= 0.")
    lut = torch.zeros(256, dtype=torch.long)
    lut[_INT8_LUT_OFFSET + int(OBSERVATION_LINE_NOT_COMPUTED)] = _NOT_COMPUTED_CODE_INDEX
    lut[_INT8_LUT_OFFSET + int(OBSERVATION_SPACE)] = _SPACE_CODE_INDEX
    lut[_INT8_LUT_OFFSET + int(OBSERVATION_EARTH)] = _EARTH_CODE_INDEX
    lut[_INT8_LUT_OFFSET + int(OBSERVATION_CLOUD)] = _CLOUD_CODE_INDEX
    target_base = int(OBSERVATION_TARGET)
    for target_index in range(max_target_index + 1):
        lut[_INT8_LUT_OFFSET + target_base + target_index] = (
            _TARGET_CODE_INDEX_BASE + target_index
        )
    return lut


def observation_code_vocab_size(*, max_target_index: int) -> int:
    """Number of embedding rows: unknown + 4 base classes + target slots T0..T{max}."""
    return _TARGET_CODE_INDEX_BASE + int(max_target_index) + 1


def _as_batched_codes(codes: torch.Tensor | np.ndarray) -> tuple[torch.Tensor, bool]:
    if isinstance(codes, np.ndarray):
        tensor = torch.as_tensor(codes)
    else:
        tensor = codes
    if tensor.ndim == 1:
        return tensor.unsqueeze(0), True
    if tensor.ndim == 2:
        return tensor, False
    raise ValueError(f"codes must be 1D or 2D, got shape {tuple(tensor.shape)}.")


def observation_codes_to_indices(
    codes: torch.Tensor,
    code_index_lut: torch.Tensor,
) -> torch.Tensor:
    """Map int8 observation-line codes to embedding indices ``(batch, L)``."""
    code_values = codes.to(dtype=torch.long)
    lut_indices = code_values + _INT8_LUT_OFFSET
    lut_indices = lut_indices.clamp(0, code_index_lut.shape[0] - 1)
    return code_index_lut[lut_indices]


def _conv1d_output_length(
    length: int,
    *,
    kernel_size: int,
    stride: int,
    padding: int,
) -> int:
    if length == 0:
        return 0
    return (length + 2 * padding - kernel_size) // stride + 1


_DEFAULT_CNN_CONV_CHANNELS = (16, 32, 64)
_DEFAULT_CNN_STRIDES = (2, 2, 2)
_CNN_KERNEL_BY_NUM_LAYERS = {1: 3, 2: 5, 3: 7}


def cnn_vision_conv_stack(
    num_layers: int,
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    """Return ``(conv_channels, kernel_sizes, strides)`` for vision 1D-CNN depth.

    ``num_layers`` must be 1, 2, or 3. Each depth uses a uniform kernel size:
    1 → 3, 2 → 5, 3 → 7.
    """
    if num_layers not in _CNN_KERNEL_BY_NUM_LAYERS:
        raise ValueError("num_layers must be 1, 2, or 3.")
    kernel = _CNN_KERNEL_BY_NUM_LAYERS[num_layers]
    conv_channels = _DEFAULT_CNN_CONV_CHANNELS[:num_layers]
    kernel_sizes = (kernel,) * num_layers
    strides = _DEFAULT_CNN_STRIDES[:num_layers]
    return conv_channels, kernel_sizes, strides


@dataclass(frozen=True)
class CNN1DEncoderConfig:
    """Hyper-parameters for a reusable 1D strip encoder."""

    in_channels: int = 3
    seq_len: int = 100
    embedding_dim: int = 32
    conv_channels: tuple[int, ...] = (16, 32)
    kernel_sizes: tuple[int, ...] = (5, 5)
    strides: tuple[int, ...] = (2, 2)
    dropout: float = 0.0
    code_embed_dim: int = 8
    max_target_index: int = 35

    def __post_init__(self) -> None:
        if self.in_channels < 1:
            raise ValueError("in_channels must be >= 1.")
        if self.seq_len < 0:
            raise ValueError("seq_len must be >= 0.")
        if self.embedding_dim < 1:
            raise ValueError("embedding_dim must be >= 1.")
        if self.code_embed_dim < 1:
            raise ValueError("code_embed_dim must be >= 1.")
        if self.max_target_index < 0:
            raise ValueError("max_target_index must be >= 0.")
        if not self.conv_channels:
            raise ValueError("conv_channels must be non-empty.")
        if len(self.kernel_sizes) != len(self.conv_channels):
            raise ValueError("kernel_sizes must match conv_channels length.")
        if len(self.strides) != len(self.conv_channels):
            raise ValueError("strides must match conv_channels length.")
        if any(k < 1 for k in self.kernel_sizes):
            raise ValueError("kernel_sizes must be >= 1.")
        if any(s < 1 for s in self.strides):
            raise ValueError("strides must be >= 1.")
        if not (0.0 <= self.dropout < 1.0):
            raise ValueError("dropout must be in [0, 1).")

    @property
    def final_conv_channels(self) -> int:
        return int(self.conv_channels[-1])

    @property
    def num_code_embeddings(self) -> int:
        return observation_code_vocab_size(max_target_index=self.max_target_index)


class CNN1DEncoder(nn.Module):
    """1D convolutional stack with global pooling → fixed-size embedding.

    Input: ``(batch, in_channels, seq_len)``
    Output: ``(batch, embedding_dim)``

    When ``seq_len == 0`` at runtime the encoder returns a zero embedding so the
    same module can represent a disabled secondary camera line.
    """

    def __init__(self, config: CNN1DEncoderConfig | None = None) -> None:
        super().__init__()
        self.config = config if config is not None else CNN1DEncoderConfig()
        self.embedding_dim = int(self.config.embedding_dim)

        layers: list[nn.Module] = []
        in_ch = int(self.config.in_channels)
        length = int(self.config.seq_len)
        for out_ch, kernel, stride in zip(
            self.config.conv_channels,
            self.config.kernel_sizes,
            self.config.strides,
        ):
            padding = int(kernel // 2)
            layers.append(
                nn.Conv1d(
                    in_channels=in_ch,
                    out_channels=int(out_ch),
                    kernel_size=int(kernel),
                    stride=int(stride),
                    padding=padding,
                )
            )
            layers.append(nn.ReLU(inplace=True))
            in_ch = int(out_ch)
            length = _conv1d_output_length(
                length,
                kernel_size=int(kernel),
                stride=int(stride),
                padding=padding,
            )
        self.conv = nn.Sequential(*layers)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(self.config.final_conv_channels, self.embedding_dim),
            nn.ReLU(inplace=True),
        )
        if self.config.dropout > 0.0:
            self.head.add_module("dropout", nn.Dropout(p=self.config.dropout))

        if length < 1 and self.config.seq_len > 0:
            raise ValueError(
                "Conv stack collapses seq_len to zero; reduce strides or kernels."
            )

        self._post_init_weights()

    def _post_init_weights(self) -> None:
        for module in self.modules():
            if isinstance(module, nn.Conv1d):
                nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Linear):
                nn.init.kaiming_normal_(module.weight, mode="fan_in", nonlinearity="relu")
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim == 2:
            x = x.unsqueeze(0)
        if x.ndim != 3:
            raise ValueError(f"Expected input (batch, C, L), got shape {tuple(x.shape)}.")
        batch_size = int(x.shape[0])
        if int(x.shape[-1]) == 0:
            return x.new_zeros((batch_size, self.embedding_dim))

        features = self.conv(x)
        pooled = self.pool(features)
        return self.head(pooled)


class ObservationLineCNNEncoder(nn.Module):
    """Observation-line int8 codes → learned embedding → :class:`CNN1DEncoder`.

    Use one instance per camera stream (primary / secondary) with that camera's
    ``seq_len`` (bin count). Disabled cameras with ``L=0`` yield a zero vector.
    """

    def __init__(self, config: CNN1DEncoderConfig | None = None) -> None:
        super().__init__()
        self.config = config if config is not None else CNN1DEncoderConfig()
        lut = _build_code_index_lut(max_target_index=self.config.max_target_index)
        self.register_buffer("code_index_lut", lut, persistent=False)
        self.code_embed = nn.Embedding(
            num_embeddings=self.config.num_code_embeddings,
            embedding_dim=int(self.config.code_embed_dim),
        )
        cnn_config = replace(
            self.config,
            in_channels=int(self.config.code_embed_dim),
        )
        self.cnn = CNN1DEncoder(cnn_config)

    @property
    def embedding_dim(self) -> int:
        return self.cnn.embedding_dim

    def encode_codes(self, codes: torch.Tensor | np.ndarray) -> torch.Tensor:
        """Embed int8 codes to ``(batch, code_embed_dim, L)``."""
        batched, _ = _as_batched_codes(codes)
        if int(batched.shape[-1]) == 0:
            batch_size = int(batched.shape[0])
            return batched.new_zeros((batch_size, self.config.code_embed_dim, 0))
        indices = observation_codes_to_indices(batched, self.code_index_lut)
        embedded = self.code_embed(indices)
        return embedded.transpose(1, 2)

    def forward(self, codes: torch.Tensor | np.ndarray) -> torch.Tensor:
        batched, _ = _as_batched_codes(codes)
        if int(batched.shape[-1]) == 0:
            batch_size = int(batched.shape[0])
            return batched.new_zeros((batch_size, self.embedding_dim))

        signal = self.encode_codes(batched)
        return self.cnn(signal)


# Backward-compatible alias for the initial stub name.
CNN1D = CNN1DEncoder

__all__ = [
    "CNN1D",
    "CNN1DEncoder",
    "CNN1DEncoderConfig",
    "ObservationLineCNNEncoder",
    "cnn_vision_conv_stack",
    "observation_code_vocab_size",
    "observation_codes_to_indices",
]
