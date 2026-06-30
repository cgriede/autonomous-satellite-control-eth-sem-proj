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

from .controller_observation import (
    ControllerObservation,
    ControllerObservationLayout,
    controller_observation_layout,
)
from .feature_selection import ControllerFeatureConfig, mission_scalar_key_names, select_controller_inputs_from_timestep
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
    *,
    n_mission_targets: int = 0,
) -> int:
    """Fixed-size MPO state vector width for selected timestep keys.

    Args:
        secondary_camera_observation_line_n_bins: Bin count for the secondary camera
            observation line. Pass 200 for dual-camera s01 setups; 0 for single-camera
            (the secondary codes array will be empty and contribute 0 dimensions).
        n_mission_targets: Mission target count for per-target bearing-error scalars.
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

    mission_keys = mission_scalar_key_names(
        n_targets=int(n_mission_targets),
        include_budget=cfg.include_capture_budget,
        include_captured_mask=cfg.include_captured_target_mask,
        include_bearings=cfg.include_target_bearing_errors,
    )
    obs_dim += len(mission_keys)

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
    return np.asarray(flat_features, dtype=np.float32)


class ReplayBuffer:
    def __init__(
        self,
        size: int,
        layout: ControllerObservationLayout,
        action_size: int,
        device: torch.device,
    ) -> None:
        self.size = int(size)
        self.device = device
        self.layout = layout
        self.scalars = np.zeros((self.size, layout.scalar_dim), dtype=np.float32)
        self.next_scalars = np.zeros((self.size, layout.scalar_dim), dtype=np.float32)
        self.vision: dict[str, np.ndarray] = {
            layout.vision_cache_key(key): np.zeros(
                (self.size, seq_len),
                dtype=np.int8,
            )
            for key, seq_len in zip(layout.vision_keys, layout.vision_seq_lens)
        }
        self.next_vision: dict[str, np.ndarray] = {
            key: np.zeros_like(arr) for key, arr in self.vision.items()
        }
        self.actions = np.zeros((self.size, action_size), dtype=np.float32)
        self.rewards = np.zeros((self.size,), dtype=np.float32)
        self.done = np.zeros((self.size,), dtype=np.float32)
        self.ptr = 0
        self.count = 0

    def __len__(self) -> int:
        return self.count

    def store(
        self,
        obs: ControllerObservation,
        next_obs: ControllerObservation,
        action: np.ndarray,
        reward: float,
        done: bool,
    ) -> None:
        self.scalars[self.ptr] = obs.scalars
        self.next_scalars[self.ptr] = next_obs.scalars
        for key, line in zip(self.layout.vision_keys, obs.vision):
            cache_key = self.layout.vision_cache_key(key)
            self.vision[cache_key][self.ptr] = line
        for key, line in zip(self.layout.vision_keys, next_obs.vision):
            cache_key = self.layout.vision_cache_key(key)
            self.next_vision[cache_key][self.ptr] = line
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = reward
        self.done[self.ptr] = float(done)
        self.ptr = (self.ptr + 1) % self.size
        self.count = min(self.count + 1, self.size)

    def sample(
        self, batch_size: int
    ) -> tuple[
        tuple[torch.Tensor, tuple[torch.Tensor, ...]],
        torch.Tensor,
        tuple[torch.Tensor, tuple[torch.Tensor, ...]],
        torch.Tensor,
        torch.Tensor,
    ]:
        idxs = np.random.randint(0, self.count, size=batch_size)
        scalars = torch.as_tensor(self.scalars[idxs], dtype=torch.float32, device=self.device)
        next_scalars = torch.as_tensor(
            self.next_scalars[idxs], dtype=torch.float32, device=self.device
        )
        vision = tuple(
            torch.as_tensor(self.vision[self.layout.vision_cache_key(key)][idxs], device=self.device)
            for key in self.layout.vision_keys
        )
        next_vision = tuple(
            torch.as_tensor(
                self.next_vision[self.layout.vision_cache_key(key)][idxs],
                device=self.device,
            )
            for key in self.layout.vision_keys
        )
        action = torch.as_tensor(self.actions[idxs], dtype=torch.float32, device=self.device)
        done = torch.as_tensor(self.done[idxs], dtype=torch.float32, device=self.device)
        reward = torch.as_tensor(self.rewards[idxs], dtype=torch.float32, device=self.device)
        return (scalars, vision), action, (next_scalars, next_vision), done, reward


@dataclass
class EpisodeResult:
    episode_return: float
    steps: int
    states: list[np.ndarray]
    simulation_series: SimulationStateSeries
    configured_controller_update_interval_s: float
    effective_controller_update_interval_s: float
    effective_controller_update_interval_steps: int
    learning_stats: Any | None = None
    ended_early_on_budget: bool = False
    configured_episode_steps: int = 0
    vector_hold_last_count: int | None = None


def make_attitude_control_env(
    *,
    render_mode: str | None = None,
    reward_config: RewardConfig | None = None,
    feature_config: ControllerFeatureConfig | None = None,
    secondary_camera_observation_line_n_bins: int = 0,
    n_mission_targets: int = 0,
    observation_layout: ControllerObservationLayout | None = None,
) -> Any:
    _ = render_mode
    _ = reward_config
    cfg = feature_config if feature_config is not None else ControllerFeatureConfig()
    layout = (
        observation_layout
        if observation_layout is not None
        else controller_observation_layout(
            feature_config=cfg,
            secondary_camera_observation_line_n_bins=secondary_camera_observation_line_n_bins,
            n_mission_targets=int(n_mission_targets),
        )
    )
    obs_dim = layout.scalar_dim + sum(layout.vision_seq_lens)
    high = np.full((obs_dim,), np.finfo(np.float32).max, dtype=np.float32)
    tau_max_nm = float(cast(Any, SATELLITE.reaction_wheel_max_torque).to(ureg.N * ureg.m).magnitude)

    @dataclass(frozen=True)
    class _EnvAdapter:
        observation_space: Any
        action_space: Any
        observation_layout: ControllerObservationLayout
        dt: Any
        max_episode_steps: int

    return _EnvAdapter(
        observation_space=spaces.Box(-high, high, dtype=np.float32),
        observation_layout=layout,
        action_space=spaces.Box(
            low=np.array([-1.0, -1.0], dtype=np.float32),
            high=np.array([1.0, 1.0], dtype=np.float32),
            shape=(2,),
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
    warmup_controller: str = "baseline",
    warmup_baseline_period_s: float = 60.0,
    feature_config: ControllerFeatureConfig | None = None,
    satellite_altitude: Any | None = None,
    np_rng: np.random.Generator | None = None,
    verbose_print: int = 0,
    setup=None,  # EnvironmentSetup | None
    collect_states: bool = True,
) -> EpisodeResult:
    """Backward-compatible wrapper — delegates to EpisodeRunner.run_serial.

    When `setup` is provided it is used directly. Otherwise a default s01 setup is
    constructed from `satellite_altitude` (or the s00 module-level constant).
    """
    from simulation.setup_types import OrbitConfig, EnvironmentSetup
    from .episode_runner import EpisodeRunner

    # Compatibility shim: canonical episode length is owned by SimulationStepper.
    _ = max_steps

    if setup is not None:
        effective_setup = setup
    else:
        run_altitude = satellite_altitude if satellite_altitude is not None else SATELLITE_ALTITUDE
        effective_setup = EnvironmentSetup(
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
        collect_states=collect_states,
    )

