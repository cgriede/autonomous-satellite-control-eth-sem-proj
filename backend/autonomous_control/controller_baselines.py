"""Deterministic, random, and zero-torque baseline policies for controller benchmarking."""

from __future__ import annotations

import numpy as np


class RandomTorquePolicy:
    """Uniform random torque policy within the environment action space."""

    def __init__(self, env, *, rng: np.random.Generator | None = None) -> None:
        self._low = float(env.action_space.low[0])
        self._high = float(env.action_space.high[0])
        self._rng = rng if rng is not None else np.random.default_rng()

    def reset_episode(self) -> None:
        return None

    def get_action(self, obs: np.ndarray, train: bool) -> np.ndarray:
        del obs, train
        return np.array([self._rng.uniform(self._low, self._high)], dtype=np.float64)


class ZeroTorquePolicy:
    """Always outputs zero torque (coast — no reaction wheel actuation)."""

    def reset_episode(self) -> None:
        return None

    def get_action(self, obs: np.ndarray, train: bool) -> np.ndarray:
        del obs, train
        return np.array([0.0], dtype=np.float64)


class DelayedMaxTorquePolicy:
    """
    Coast at 0 N·m for ``delay_s``, then request constant agent torque (stress / violation test).

    Uses ``env._sim_time_s`` set by the rollout driver each step (see movement_constraints_patch).
    """

    def __init__(
        self,
        env,
        *,
        delay_s: float = 5.0,
        tau_scale: float = 1.0,
    ) -> None:
        self._tau_max = float(env.action_space.high[0])
        self._delay_s = float(delay_s)
        self._tau_scale = float(tau_scale)
        self._sim_time_s = 0.0

    def reset_episode(self) -> None:
        self._sim_time_s = 0.0

    def set_sim_time_s(self, sim_time_s: float) -> None:
        self._sim_time_s = float(sim_time_s)

    def get_action(self, obs: np.ndarray, train: bool) -> np.ndarray:
        del obs, train
        if self._sim_time_s < self._delay_s:
            return np.array([0.0], dtype=np.float64)
        return np.array([self._tau_scale * self._tau_max], dtype=np.float64)


class MaxTorqueSweepPolicy:
    """
    Hardcoded baseline:
    linearly sweep torque from +tau_max to -tau_max over `period_s`.
    """

    def __init__(self, env, *, period_s: float = 10.0) -> None:
        self._tau_max = float(env.action_space.high[0])
        dt_s = float(env.dt.to("second").magnitude)
        self._period_steps = max(2, int(round(period_s / dt_s)))
        self._step_idx = 0

    def reset_episode(self) -> None:
        self._step_idx = 0

    def get_action(self, obs: np.ndarray, train: bool) -> np.ndarray:
        del obs, train
        phase = (self._step_idx % self._period_steps) / float(self._period_steps - 1)
        torque = self._tau_max * (1.0 - 2.0 * phase)
        self._step_idx += 1
        return np.array([torque], dtype=np.float64)
