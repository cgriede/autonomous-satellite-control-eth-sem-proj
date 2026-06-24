"""Tests for 1D-CNN vision encoders."""

from __future__ import annotations

import unittest

import numpy as np
import torch

from autonomous_control.CNN_1d import (
    CNN1DEncoder,
    CNN1DEncoderConfig,
    ObservationLineCNNEncoder,
    _build_code_index_lut,
    observation_code_vocab_size,
    observation_codes_to_indices,
)

_CODE_SPACE = 0
_CODE_EARTH = 1
_CODE_CLOUD = 2
_CODE_TARGET = 3


class TestObservationCodeEmbedding(unittest.TestCase):
    def test_code_index_lut_maps_known_codes(self) -> None:
        lut = _build_code_index_lut(max_target_index=2)
        codes = torch.tensor([[-99, 0, 1, 2, 3, 4, 5]], dtype=torch.int8)
        indices = observation_codes_to_indices(codes, lut)
        self.assertEqual(tuple(indices.shape), (1, 7))
        self.assertEqual(int(indices[0, 0]), 1)
        self.assertEqual(int(indices[0, 1]), 2)
        self.assertEqual(int(indices[0, 2]), 3)
        self.assertEqual(int(indices[0, 3]), 4)
        self.assertEqual(int(indices[0, 4]), 5)
        self.assertEqual(int(indices[0, 5]), 6)
        self.assertEqual(int(indices[0, 6]), 7)

    def test_unknown_code_maps_to_zero(self) -> None:
        lut = _build_code_index_lut(max_target_index=0)
        codes = torch.tensor([[42]], dtype=torch.int8)
        indices = observation_codes_to_indices(codes, lut)
        self.assertEqual(int(indices[0, 0]), 0)

    def test_target_codes_get_distinct_embedding_rows(self) -> None:
        encoder = ObservationLineCNNEncoder(
            CNN1DEncoderConfig(
                seq_len=2,
                code_embed_dim=4,
                max_target_index=2,
                embedding_dim=8,
                conv_channels=(4,),
                kernel_sizes=(1,),
                strides=(1,),
            )
        )
        codes = np.array([[_CODE_TARGET, _CODE_TARGET + 1]], dtype=np.int8)
        embedded = encoder.encode_codes(codes)
        self.assertEqual(tuple(embedded.shape), (1, 4, 2))
        row_t0 = encoder.code_embed.weight[5]
        row_t1 = encoder.code_embed.weight[6]
        self.assertFalse(torch.allclose(row_t0, row_t1))

    def test_empty_observation_line_returns_zero_embedding(self) -> None:
        encoder = ObservationLineCNNEncoder(
            CNN1DEncoderConfig(
                seq_len=0,
                embedding_dim=16,
                conv_channels=(8,),
                kernel_sizes=(3,),
                strides=(1,),
            )
        )
        codes = np.empty(0, dtype=np.int8)
        out = encoder(codes)
        self.assertEqual(tuple(out.shape), (1, 16))
        self.assertTrue(torch.all(out == 0))


class TestCNN1DEncoder(unittest.TestCase):
    def test_encoder_output_dim_matches_config(self) -> None:
        n_bins = 100
        cfg = CNN1DEncoderConfig(seq_len=n_bins, embedding_dim=24)
        encoder = CNN1DEncoder(cfg)
        x = torch.randn(4, 3, n_bins)
        y = encoder(x)
        self.assertEqual(tuple(y.shape), (4, 24))

    def test_vocab_size_includes_targets(self) -> None:
        self.assertEqual(observation_code_vocab_size(max_target_index=35), 41)

    def test_observation_line_encoder_batched(self) -> None:
        n_bins = 20
        cfg = CNN1DEncoderConfig(
            seq_len=n_bins,
            embedding_dim=12,
            conv_channels=(8, 16),
            kernel_sizes=(5, 3),
            strides=(2, 2),
        )
        encoder = ObservationLineCNNEncoder(cfg)
        codes = np.full((2, n_bins), _CODE_EARTH, dtype=np.int8)
        codes[0, :5] = _CODE_TARGET
        codes[1, 10:] = _CODE_CLOUD
        out = encoder(codes)
        self.assertEqual(tuple(out.shape), (2, 12))
        self.assertFalse(torch.all(out == 0))


if __name__ == "__main__":
    unittest.main()
