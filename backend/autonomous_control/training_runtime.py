"""Reusable runtime helpers for MPO train/eval scripts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from gymnasium import spaces
from environment_definition.constants import (
    EARTH_GRAVITATIONAL_PARAMETER,
    EARTH_RADIUS,
    RenderMode,
    SIMULATION,
    SimulationConfig,
    UREG as ureg,
)
from environment_definition.constants.MISSION import OBSERVATION_TARGETS
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE, SATELLITE_ALTITUDE
from simulation.stepper import SimulationStepper
from simulation.state_types import SimulationStateSeries
from utils.flight_geometry.line_of_sight import minimum_contact_angle

from .feature_selection import ControllerFeatureConfig, build_controller_state_from_timestep
from .reward import RewardConfig


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
    obs_dim = len(ControllerFeatureConfig().features)
    high = np.full((obs_dim,), np.finfo(np.float32).max, dtype=np.float32)
    tau_max_nm = float(SATELLITE.reaction_wheel_max_torque.to(ureg.N * ureg.m).magnitude)

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
        max_episode_steps=10_000,
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
    alpha = minimum_contact_angle(observer_height=0.0 * ureg.km, orbit_height=SATELLITE_ALTITUDE)
    contact_half_angle_deg = alpha.to(ureg.deg).magnitude
    margin_deg = SIMULATION.contact_margin_angle.to(ureg.deg).magnitude
    start_angle_deg = -(contact_half_angle_deg + margin_deg)
    end_angle_deg = contact_half_angle_deg + margin_deg
    stepper = SimulationStepper(
        simulation_config=SimulationConfig(
            render_mode=RenderMode.HEADLESS,
            controller_mode=controller_mode,  # type: ignore[arg-type]
        ),
        earth_radius=EARTH_RADIUS,
        earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
        satellite=SATELLITE,
        satellite_altitude=SATELLITE_ALTITUDE,
        theta_center_rad=float(theta_center),
        start_angle_deg=float(start_angle_deg),
        end_angle_deg=float(end_angle_deg),
        sat_motion_span_scale=float(SIMULATION.sat_motion_span_scale),
        sat_z_offset_deg=float(SIMULATION.sat_z_offset.to(ureg.deg).magnitude),
        ureg=ureg,
        camera_pixel_ray_samples=SIMULATION.camera_pixel_ray_samples,
        reward_config=RewardConfig(),
    )
    target_angle_rad = float(OBSERVATION_TARGETS[0].angle.to(ureg.rad).magnitude)
    current_ts = stepper.current_timestep_state()
    current_controller_state = build_controller_state_from_timestep(
        current=current_ts,
        previous=None,
        target_angle_rad=target_angle_rad,
    )
    obs = np.asarray(current_controller_state.obs_vector, dtype=np.float32)
    states: list[np.ndarray] = [obs.copy()]
    current_action_nm = 0.0
    episode_return = 0.0
    steps = 0
    train_mode = mode in {"warmup", "train"}
    warmup_policy = None
    if mode == "warmup" and warmup_controller == "baseline":
        from .controller_baselines import MaxTorqueSweepPolicy

        warmup_policy = MaxTorqueSweepPolicy(env, period_s=float(warmup_baseline_period_s))
        warmup_policy.reset_episode()

    while not stepper.done:
        if stepper.should_update_controller():
            if mode == "warmup":
                if warmup_policy is not None:
                    action_vec = warmup_policy.get_action(obs, train=False)
                    current_action_nm = float(np.asarray(action_vec, dtype=np.float64).reshape(-1)[0])
                else:
                    current_action_nm = float(np.random.uniform(-1.0, 1.0))
            else:
                action_vec = agent.get_action(obs, train=train_mode)
                current_action_nm = float(np.asarray(action_vec, dtype=np.float64).reshape(-1)[0])
        next_ts = stepper.step(wheel_torque_cmd_nm=current_action_nm)
        next_controller_state = build_controller_state_from_timestep(
            current=next_ts,
            previous=current_ts,
            target_angle_rad=target_angle_rad,
        )
        next_obs = np.asarray(next_controller_state.obs_vector, dtype=np.float32)
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

