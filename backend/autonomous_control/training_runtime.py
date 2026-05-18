"""Reusable runtime helpers for MPO train/eval scripts."""

from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Any, cast

import numpy as np
import torch
from gymnasium import spaces
from tqdm.auto import tqdm
from environment_definition.constants import (
    EARTH_GRAVITATIONAL_PARAMETER,
    EARTH_RADIUS,
    RenderMode,
    SIMULATION,
    SimulationConfig,
    UREG as ureg,
)
from environment_definition.constants.SIMULATION import (
    OBSERVATION_CLOUD,
    OBSERVATION_EARTH,
    OBSERVATION_LINE_NOT_COMPUTED,
    OBSERVATION_SPACE,
    OBSERVATION_TARGET,
)
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE, SATELLITE_ALTITUDE
from simulation.state_types import SimulationTimestepState
from simulation.state_types import SimulationStateSeries

from .feature_selection import ControllerFeatureConfig, select_controller_inputs_from_timestep
from .reward import RewardConfig

_OBSERVATION_CODE_ORDER: tuple[np.int8, ...] = (
    np.int8(OBSERVATION_LINE_NOT_COMPUTED),
    np.int8(OBSERVATION_SPACE),
    np.int8(OBSERVATION_EARTH),
    np.int8(OBSERVATION_CLOUD),
    np.int8(OBSERVATION_TARGET),
)


def controller_observation_dim(
    feature_config: ControllerFeatureConfig | None = None,
    secondary_camera_observation_line_n_bins: int = 0,
) -> int:
    # #region agent log
    import json, time, pathlib
    _log_path = pathlib.Path("debug-c2d20e.log")
    _log_path.open("a").write(json.dumps({"sessionId": "c2d20e", "hypothesisId": "H-A", "location": "training_runtime.py:controller_observation_dim", "message": "called", "data": {"secondary_camera_observation_line_n_bins": secondary_camera_observation_line_n_bins}, "timestamp": int(time.time() * 1000)}) + "\n")
    # #endregion
    """Fixed-size MPO state vector width for selected timestep keys.

    Args:
        secondary_camera_observation_line_n_bins: Bin count for the secondary camera
            observation line. Pass 200 for dual-camera s01 setups; 0 for single-camera
            (the secondary codes array will be empty and contribute 0 dimensions).
    """
    cfg = feature_config if feature_config is not None else ControllerFeatureConfig()
    obs_dim = 0
    n_bins = int(SIMULATION.camera_observation_line_n_bins)

    for key in cfg.selected_keys:
        if key == "camera_observation_line_codes":
            # one value per line, NOT one-hot
            obs_dim += n_bins
        elif key == "secondary_camera_observation_line_codes":
            obs_dim += int(secondary_camera_observation_line_n_bins)
        elif key == "camera_ground_center_xy_km":
            raise ValueError(
                "camera_ground_center_xy_km is not available on SimulationTimestepState."
            )
        else:
            obs_dim += 1

    return obs_dim


def _in_notebook() -> bool:
    try:
        from IPython import get_ipython  # type: ignore
    except Exception:
        return False
    shell = get_ipython()
    if shell is None:
        return False
    return shell.__class__.__name__ == "ZMQInteractiveShell"

def build_state_vector_from_timestep(
    *,
    timestep: SimulationTimestepState,
    feature_config: ControllerFeatureConfig | None = None,
) -> np.ndarray:
    """Build controller `state_vector`; vision arrays become fixed one-hot features."""
    selected = select_controller_inputs_from_timestep(
        timestep=timestep,
        feature_config=feature_config,
    )
    flat_features: list[float] = []
    for key, value in selected.items():
        if key in ("camera_observation_line_codes", "secondary_camera_observation_line_codes"):
            arr: np.ndarray = np.asarray(value, dtype=np.float32).reshape(-1)
            flat_features.extend(arr.tolist())
            continue

        if isinstance(value, (bool, int, float, np.generic)):
            flat_features.append(float(value))
            continue
        if isinstance(value, np.ndarray):
            arr = np.asarray(value, dtype=np.float32).reshape(-1)
            if arr.size == 1:
                flat_features.append(float(arr[0]))
                continue
        raise TypeError(
            f"Unsupported controller feature type for key '{key}': {type(value).__name__}"
        )
    result_arr = np.asarray(flat_features, dtype=np.float32)
    # #region agent log
    import json, time, pathlib
    _log_path = pathlib.Path("debug-c2d20e.log")
    _log_path.open("a").write(json.dumps({"sessionId": "c2d20e", "hypothesisId": "H-A", "location": "training_runtime.py:build_state_vector_from_timestep", "message": "obs produced", "data": {"obs_size": int(result_arr.shape[0])}, "timestamp": int(time.time() * 1000)}) + "\n")
    # #endregion
    return result_arr


class ReplayBuffer:
    def __init__(self, size: int, obs_size: int, action_size: int, device: torch.device) -> None:
        self.size = int(size)
        self.device = device
        self.obs = np.zeros((self.size, obs_size), dtype=np.float32)
        self.next_obs = np.zeros((self.size, obs_size), dtype=np.float32)
        self.actions = np.zeros((self.size, action_size), dtype=np.float32)
        self.rewards = np.zeros((self.size,), dtype=np.float32)
        self.done = np.zeros((self.size,), dtype=np.float32)
        self.ptr = 0
        self.count = 0

    def __len__(self) -> int:
        return self.count

    def store(
        self,
        obs: np.ndarray,
        next_obs: np.ndarray,
        action: np.ndarray,
        reward: float,
        done: bool,
    ) -> None:
        # #region agent log
        import json, time, pathlib
        _log_path = pathlib.Path("debug-c2d20e.log")
        _log_path.open("a").write(json.dumps({"sessionId": "c2d20e", "hypothesisId": "H-A", "location": "training_runtime.py:ReplayBuffer.store", "message": "buffer store attempt", "data": {"buffer_obs_size": self.obs.shape[1], "incoming_obs_size": int(obs.shape[0])}, "timestamp": int(time.time() * 1000)}) + "\n")
        # #endregion
        self.obs[self.ptr] = obs
        self.next_obs[self.ptr] = next_obs
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = reward
        self.done[self.ptr] = float(done)
        self.ptr = (self.ptr + 1) % self.size
        self.count = min(self.count + 1, self.size)

    def sample(
        self, batch_size: int
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        idxs = np.random.randint(0, self.count, size=batch_size)
        obs = torch.as_tensor(self.obs[idxs], dtype=torch.float32, device=self.device)
        action = torch.as_tensor(self.actions[idxs], dtype=torch.float32, device=self.device)
        next_obs = torch.as_tensor(self.next_obs[idxs], dtype=torch.float32, device=self.device)
        done = torch.as_tensor(self.done[idxs], dtype=torch.float32, device=self.device)
        reward = torch.as_tensor(self.rewards[idxs], dtype=torch.float32, device=self.device)
        return obs, action, next_obs, done, reward


@dataclass
class EpisodeResult:
    episode_return: float
    steps: int
    states: list[np.ndarray]
    simulation_series: SimulationStateSeries
    configured_controller_update_interval_s: float
    effective_controller_update_interval_s: float
    effective_controller_update_interval_steps: int


def make_attitude_control_env(
    *,
    render_mode: str | None = None,
    reward_config: RewardConfig | None = None,
    secondary_camera_observation_line_n_bins: int = 0,
) -> Any:
    _ = render_mode
    _ = reward_config
    obs_dim = controller_observation_dim(
        secondary_camera_observation_line_n_bins=secondary_camera_observation_line_n_bins
    )
    high = np.full((obs_dim,), np.finfo(np.float32).max, dtype=np.float32)
    tau_max_nm = float(cast(Any, SATELLITE.reaction_wheel_max_torque).to(ureg.N * ureg.m).magnitude)

    @dataclass(frozen=True)
    class _EnvAdapter:
        observation_space: Any
        action_space: Any
        dt: Any
        max_episode_steps: int

    return _EnvAdapter(
        observation_space=spaces.Box(-high, high, dtype=np.float32),
        action_space=spaces.Box(
            low=np.array([-tau_max_nm], dtype=np.float32),
            high=np.array([tau_max_nm], dtype=np.float32),
            shape=(1,),
            dtype=np.float32,
        ),
        dt=SIMULATION.simulation_timestep,
        max_episode_steps=int(SIMULATION.max_episode_steps),
    )


def run_episode(
    env: Any,
    agent: Any,
    *,
    mode: str,
    train_updates_per_step: int = 1,
    max_steps: int | None = None,  # compatibility, ignored in canonical stepper mode
    step_callback: Any | None = None,
    warmup_controller: str = "random",
    warmup_baseline_period_s: float = 60.0,
    feature_config: ControllerFeatureConfig | None = None,
    satellite_altitude: Any | None = None,
    np_rng: np.random.Generator | None = None,
    verbose_print: int = 0,
    setup=None,  # SimulationSetupConfig | None
) -> EpisodeResult:
    """Backward-compatible wrapper — delegates to EpisodeRunner.run_serial.

    When `setup` is provided it is used directly. Otherwise a default s01 setup is
    constructed from `satellite_altitude` (or the s00 module-level constant).
    """
    from simulation.setup_types import OrbitConfig, SimulationSetupConfig
    from .episode_runner import EpisodeRunner

    # Compatibility shim: canonical episode length is owned by SimulationStepper.
    _ = max_steps

    if setup is not None:
        effective_setup = setup
    else:
        run_altitude = satellite_altitude if satellite_altitude is not None else SATELLITE_ALTITUDE
        effective_setup = SimulationSetupConfig(
            satellite=SATELLITE,
            orbit=OrbitConfig(altitude=run_altitude),
        )

    return EpisodeRunner(effective_setup).run_serial(
        agent,
        mode=mode,
        train_updates_per_step=train_updates_per_step,
        step_callback=step_callback,
        warmup_controller=warmup_controller,
        warmup_baseline_period_s=warmup_baseline_period_s,
        feature_config=feature_config,
        np_rng=np_rng,
        verbose_print=verbose_print,
    )

