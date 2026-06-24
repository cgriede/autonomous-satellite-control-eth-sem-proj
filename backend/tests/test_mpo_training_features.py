"""Deeper tests for MPO training components beyond fast preflight smoke checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from autonomous_control.controller_agent import MPOAgent
from autonomous_control.controller_observation import (
    ControllerObservation,
    build_controller_observation_from_timestep,
)
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.training_preflight import _minimal_timestep
from autonomous_control.training_runtime import ReplayBuffer, make_attitude_control_env


class MPOAgentCheckpointTest(unittest.TestCase):
    def test_checkpoint_roundtrip_preserves_weights(self):
        env = make_attitude_control_env()
        cfg = MPOConfig(warmup_episodes=0, batch_size=4, buffer_size=32)
        agent = MPOAgent(env, config=cfg)
        before = {k: v.clone() for k, v in agent.pi.state_dict().items()}

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "agent.pt"
            payload = {
                "pi": agent.pi.state_dict(),
                "pi_target": agent.pi_target.state_dict(),
                "q1": agent.q1.state_dict(),
                "q2": agent.q2.state_dict(),
                "q1_target": agent.q1_target.state_dict(),
                "q2_target": agent.q2_target.state_dict(),
                "q_optimizer": agent.q_optimizer.state_dict(),
                "pi_optimizer": agent.pi_optimizer.state_dict(),
                "eta_optimizer": agent.eta_optimizer.state_dict(),
                "log_eta": float(agent.log_eta.detach().cpu().item()),
                "step_counter": agent.step_counter,
                "episode_returns": agent.episode_returns,
            }
            torch.save(payload, path)

            loaded = torch.load(path, map_location=agent.device)
            agent.pi.load_state_dict(loaded["pi"])
            agent.pi_target.load_state_dict(loaded["pi_target"])

        after = agent.pi.state_dict()
        for key in before:
            self.assertTrue(torch.allclose(before[key], after[key]))


class ReplayBufferTest(unittest.TestCase):
    def test_circular_buffer_overwrites_oldest(self):
        device = torch.device("cpu")
        env = make_attitude_control_env()
        layout = env.observation_layout
        buf = ReplayBuffer(4, layout, 1, device)
        obs = build_controller_observation_from_timestep(timestep=_minimal_timestep())
        for i in range(6):
            tagged = ControllerObservation(
                scalars=obs.scalars + float(i),
                vision=obs.vision,
            )
            buf.store(tagged, tagged, np.array([0.0], dtype=np.float32), 0.0, False)
        self.assertEqual(len(buf), 4)


if __name__ == "__main__":
    unittest.main()
