"""
Linear dummy policy: maps observation vector to raw logits for the action adapter.

Output dimension is POLICY_RAW_DIM (torque channel + active-observation logit).
"""

from __future__ import annotations

import numpy as np

from .action_adapter import POLICY_RAW_DIM


class LinearDummyPolicy:
    def __init__(self, obs_dim: int, *, rng: np.random.Generator | None = None) -> None:
        if obs_dim < 1:
            raise ValueError("obs_dim must be >= 1.")
        self._rng = rng if rng is not None else np.random.default_rng()
        scale = 0.01
        self._w = self._rng.normal(scale=scale, size=(POLICY_RAW_DIM, obs_dim)).astype(
            np.float64
        )
        self._b = self._rng.normal(scale=scale, size=(POLICY_RAW_DIM,)).astype(np.float64)

    @property
    def w(self) -> np.ndarray:
        return self._w

    @property
    def b(self) -> np.ndarray:
        return self._b

    def forward(self, obs: np.ndarray) -> np.ndarray:
        if obs.shape != (self._w.shape[1],):
            raise ValueError(
                f"Expected obs shape ({self._w.shape[1]},), got {obs.shape}."
            )
        return (self._w @ obs + self._b).astype(np.float64)
