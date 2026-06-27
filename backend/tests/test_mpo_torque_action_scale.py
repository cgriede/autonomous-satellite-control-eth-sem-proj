"""MPO get_action dim-0 maps tanh saturation to env.action_space torque bounds."""

from __future__ import annotations

import unittest

import numpy as np
import torch
from torch.distributions import Normal

from autonomous_control.controller_agent import MPOAgent
from autonomous_control.controller_observation import ControllerObservation
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.training_runtime import make_attitude_control_env


class _SaturatedPi(torch.nn.Module):
    def __init__(self, *, gaussian_mean: float) -> None:
        super().__init__()
        self._gaussian_mean = float(gaussian_mean)

    def forward(self, scalars, vision):
        batch = int(scalars.shape[0])
        mean = torch.full((batch, 2), self._gaussian_mean, device=scalars.device)
        log_std = torch.zeros_like(mean)
        return Normal(mean, log_std.exp())


class MpoTorqueActionScaleTest(unittest.TestCase):
    def test_tanh_saturation_maps_to_normalized_torque_bounds(self):
        env = make_attitude_control_env()
        agent = MPOAgent(env, config=MPOConfig())
        obs = ControllerObservation(
            scalars=np.zeros(agent.layout.scalar_dim, dtype=np.float32),
            vision=tuple(np.zeros(n, dtype=np.int8) for n in agent.layout.vision_seq_lens),
        )

        agent.pi = _SaturatedPi(gaussian_mean=10.0)
        out_pos = agent.get_action(obs, train=False)
        self.assertAlmostEqual(float(out_pos[0]), 1.0, places=4)

        agent.pi = _SaturatedPi(gaussian_mean=-10.0)
        out_neg = agent.get_action(obs, train=False)
        self.assertAlmostEqual(float(out_neg[0]), -1.0, places=4)


if __name__ == "__main__":
    unittest.main()
