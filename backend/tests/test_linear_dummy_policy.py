import unittest

import numpy as np

from autonomous_control.action_adapter import POLICY_RAW_DIM
from autonomous_control.controller_agent import LinearDummyPolicy


class LinearDummyPolicyTest(unittest.TestCase):
    def test_forward_shape(self):
        obs_dim = 5
        p = LinearDummyPolicy(obs_dim, rng=np.random.default_rng(0))
        out = p.forward(np.zeros(obs_dim, dtype=np.float64))
        self.assertEqual(out.shape, (POLICY_RAW_DIM,))


if __name__ == "__main__":
    unittest.main()
