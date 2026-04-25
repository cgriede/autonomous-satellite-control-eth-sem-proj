import unittest

import numpy as np

from autonomous_control.training_runtime import make_attitude_control_env, run_episode
from simulation.state_types import SimulationStateSeries


class _ZeroTorqueAgent:
    def __init__(self) -> None:
        self.transitions = 0

    def get_action(self, obs: np.ndarray, train: bool) -> np.ndarray:
        _ = obs
        _ = train
        return np.array([0.0], dtype=np.float64)

    def store(self, transition):
        _ = transition
        self.transitions += 1

    def train(self):
        return None


class TrainingRuntimeEpisodeArtifactTest(unittest.TestCase):
    def test_run_episode_returns_simulation_series_artifact(self):
        env = make_attitude_control_env()
        agent = _ZeroTorqueAgent()
        result = run_episode(env, agent, mode="train", train_updates_per_step=1)
        self.assertGreater(result.steps, 0)
        self.assertGreaterEqual(len(result.states), 2)
        self.assertIsInstance(result.simulation_series, SimulationStateSeries)
        self.assertGreater(result.effective_controller_update_interval_steps, 0)
        self.assertGreater(result.effective_controller_update_interval_s, 0.0)
        self.assertGreaterEqual(result.configured_controller_update_interval_s, 0.0)


if __name__ == "__main__":
    unittest.main()
