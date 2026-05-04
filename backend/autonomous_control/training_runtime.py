"""Reusable runtime helpers for MPO train/eval scripts."""

from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Any, cast
from rich.pretty import pprint

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
from environment_definition.constants.MISSION import los_theta_offsets_deg
from environment_definition.constants.SIMULATION import (
    OBSERVATION_CLOUD,
    OBSERVATION_EARTH,
    OBSERVATION_LINE_NOT_COMPUTED,
    OBSERVATION_SPACE,
    OBSERVATION_TARGET,
)
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE, SATELLITE_ALTITUDE
from simulation.stepper import SimulationStepper
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
) -> int:
    """Fixed-size MPO state vector width for selected timestep keys."""
    cfg = feature_config if feature_config is not None else ControllerFeatureConfig()
    obs_dim = 0
    n_bins = int(SIMULATION.camera_observation_line_n_bins)

    for key in cfg.selected_keys:
        if key == "camera_observation_line_codes":
            # one value per line, NOT one-hot
            obs_dim += n_bins
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
        if key == "camera_observation_line_codes":
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
) -> Any:
    _ = render_mode
    _ = reward_config
    obs_dim = controller_observation_dim()
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
) -> EpisodeResult:
    if hasattr(agent, "reset_episode"):
        agent.reset_episode()
    # Compatibility shim: canonical episode length is owned by SimulationStepper.
    _ = max_steps

    controller_mode = "mpo"
    class_name = type(agent).__name__.lower()
    if "random" in class_name:
        controller_mode = "random"
    elif "sweep" in class_name or "baseline" in class_name:
        controller_mode = "baseline"

    theta_center = SIMULATION.theta_center.to(ureg.rad).magnitude
    run_satellite_altitude = satellite_altitude if satellite_altitude is not None else SATELLITE_ALTITUDE
    start_angle_deg, end_angle_deg = los_theta_offsets_deg(
        orbit_height=run_satellite_altitude,
        margin_deg=float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude),
    )
    stepper = SimulationStepper(
        simulation_config=SimulationConfig(
            render_mode=RenderMode.HEADLESS,
            controller_mode=controller_mode,  # type: ignore[arg-type]
        ),
        earth_radius=EARTH_RADIUS,
        earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
        satellite=SATELLITE,
        satellite_altitude=run_satellite_altitude,
        theta_center_rad=float(theta_center),
        start_angle_deg=float(start_angle_deg),
        end_angle_deg=float(end_angle_deg),
        sat_motion_span_scale=float(SIMULATION.sat_motion_span_scale),
        sat_z_offset_deg=float(SIMULATION.sat_z_offset.to(ureg.deg).magnitude),
        ureg=ureg,
        camera_pixel_ray_samples=SIMULATION.camera_pixel_ray_samples,
        reward_config=RewardConfig(),
    )
    episode_rng = np_rng if np_rng is not None else np.random.default_rng()
    current_ts = stepper.current_timestep_state()
    obs = build_state_vector_from_timestep(
        timestep=current_ts,
        feature_config=feature_config,
    )
    states: list[np.ndarray] = [obs.copy()]
    current_action_nm = 0.0
    episode_return = 0.0
    steps = 0
    train_mode = mode in {"warmup", "train"}
    episode_total_steps = stepper.total_steps
    progress_bar = tqdm(
        total=int(episode_total_steps) if episode_total_steps is not None else None,
        desc=f"{mode} episode",
        unit="step",
        leave=False,
        dynamic_ncols=True,
        file=sys.stdout,
        disable=verbose_print != 0,
    )
    if verbose_print == 0:
        progress_bar.write(f"[run_episode] start mode={mode} max_steps={episode_total_steps}")
    warmup_policy: Any | None = None
    if mode == "warmup" and warmup_controller == "baseline":
        from .controller_baselines import MaxTorqueSweepPolicy

        warmup_policy = MaxTorqueSweepPolicy(env, period_s=float(warmup_baseline_period_s))
        warmup_policy.reset_episode()
    elif mode == "warmup" and warmup_controller == "random":
        from .controller_baselines import RandomTorquePolicy

        warmup_policy = RandomTorquePolicy(env, rng=episode_rng)
        warmup_policy.reset_episode()
        
    try:
        while not stepper.done and steps < int(episode_total_steps):
            if stepper.should_update_controller():
                if mode == "warmup":
                    if warmup_policy is None:
                        raise RuntimeError("warmup_policy must be configured in warmup mode.")
                    action_vec = warmup_policy.get_action(obs, train=False)
                    current_action_nm = float(np.asarray(action_vec, dtype=np.float64).reshape(-1)[0])

                else:
                    action_vec = agent.get_action(obs, train=train_mode)
                    current_action_nm = float(np.asarray(action_vec, dtype=np.float64).reshape(-1)[0])
            next_ts = stepper.step(wheel_torque_cmd_nm=current_action_nm)
            next_obs = build_state_vector_from_timestep(
                timestep=next_ts,
                feature_config=feature_config,
            )

            #DEBUG INSTRUMENTATION
            if steps % 100 == 0 or stepper.done:
                pprint(f"Step {steps}:")
                pprint(f"  Action (Nm): {current_action_nm:.6f}")
                pprint(next_obs)

            reward = float(next_ts.reward)
            done = bool(stepper.done)
            episode_return += reward
            states.append(next_obs.copy())
            if step_callback is not None:
                step_callback(next_ts)
            if mode in {"warmup", "train"} and hasattr(agent, "store"):
                action_arr = np.array([current_action_nm], dtype=np.float32)
                agent.store((obs, action_arr, reward, next_obs, done))
                if mode == "train":
                    for _ in range(train_updates_per_step):
                        if hasattr(agent, "train"):
                            agent.train()
            obs = next_obs
            current_ts = next_ts
            steps += 1
            progress_bar.update(1)
            if verbose_print == 0 and ((steps % 10) == 0 or done):
                progress_bar.set_postfix(steps=steps, reward=f"{reward:.5f}", refresh=False)
    finally:
        progress_bar.close()
    if verbose_print == 0:
        avg_reward = episode_return / max(1, steps)
        end_msg = (
            f"[run_episode] end mode={mode} steps={steps} "
            f"total_reward={episode_return:.6f} avg_reward={avg_reward:.6f}"
        )
        if _in_notebook():
            print(end_msg)
        else:
            progress_bar.write(end_msg)

    context = stepper.build_episode_context()
    return EpisodeResult(
        episode_return=episode_return,
        steps=steps,
        states=states,
        simulation_series=context.simulation_series,
        configured_controller_update_interval_s=context.configured_controller_update_interval_s,
        effective_controller_update_interval_s=context.effective_controller_update_interval_s,
        effective_controller_update_interval_steps=context.effective_controller_update_interval_steps,
    )

