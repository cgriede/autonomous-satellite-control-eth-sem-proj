"""Tests for multimodal controller encoder and actor/critic wiring."""

from __future__ import annotations

import unittest

import numpy as np
import torch

from autonomous_control.controller_actor import Actor
from autonomous_control.controller_critic import Critic
from autonomous_control.controller_encoder import ControllerEncoder
from autonomous_control.controller_observation import (
    ControllerObservation,
    controller_observation_layout,
)
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.training_runtime import make_attitude_control_env


class ControllerEncoderTest(unittest.TestCase):
    def test_encoder_output_dim_dual_path(self) -> None:
        layout = controller_observation_layout()
        config = MPOConfig(num_units_actor=24, num_layers_scalar_encoder=1, num_layers_vision_fusion=1)
        encoder = ControllerEncoder(layout, config, activation=config.activation_actor)
        self.assertEqual(encoder.output_dim, 48)

        batch = 3
        scalars = torch.randn(batch, layout.scalar_dim)
        vision = tuple(
            torch.zeros(batch, seq_len, dtype=torch.int8)
            for seq_len in layout.vision_seq_lens
        )
        out = encoder(scalars, vision)
        self.assertEqual(tuple(out.shape), (batch, 48))

    def test_actor_and_critic_forward(self) -> None:
        env = make_attitude_control_env()
        layout = env.observation_layout
        config = MPOConfig(num_units_actor=16, num_layers_actor=1, num_units_critic=20, num_layers_critic=1)
        action_low = torch.tensor(env.action_space.low, dtype=torch.float32)
        action_high = torch.tensor(env.action_space.high, dtype=torch.float32)
        actor = Actor(action_low, action_high, layout, 1, config)
        critic = Critic(layout, 1, config)

        scalars = torch.randn(2, layout.scalar_dim)
        vision = tuple(
            torch.zeros(2, seq_len, dtype=torch.int8) for seq_len in layout.vision_seq_lens
        )
        actions = torch.zeros(2, 1)

        dist = actor(scalars, vision)
        self.assertEqual(tuple(dist.mean.shape), (2, 1))
        q = critic(scalars, vision, actions)
        self.assertEqual(tuple(q.shape), (2, 1))


if __name__ == "__main__":
    unittest.main()
