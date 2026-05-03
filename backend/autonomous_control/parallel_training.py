from __future__ import annotations

import io
import multiprocessing as mp
import queue
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch

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
from utils.flight_geometry.line_of_sight import minimum_contact_angle
from utils.ml_training.ml_training_utils import RunTelemetryWriter

from .config.randomness import apply_global_seed, derive_seed
from .controller_actor import Actor
from .mpo_config import MPOConfig
from .reward import RewardConfig
from .training_runtime import build_state_vector_from_timestep


@dataclass(frozen=True)
class WorkerTask:
    episode_idx: int
    mode: str
    policy_state_bytes: bytes


@dataclass(frozen=True)
class WorkerResult:
    worker_id: int
    episode_idx: int
    episode_return: float
    steps: int
    obs: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    next_obs: np.ndarray
    done: np.ndarray


def _build_stepper(*, satellite_altitude: Any) -> SimulationStepper:
    theta_center = SIMULATION.theta_center.to(ureg.rad).magnitude
    alpha = minimum_contact_angle(observer_height=0.0 * ureg.km, orbit_height=satellite_altitude)
    contact_half_angle_deg = alpha.to(ureg.deg).magnitude
    margin_deg = SIMULATION.contact_margin_angle.to(ureg.deg).magnitude
    start_angle_deg = -(contact_half_angle_deg + margin_deg)
    end_angle_deg = contact_half_angle_deg + margin_deg
    return SimulationStepper(
        simulation_config=SimulationConfig(
            render_mode=RenderMode.HEADLESS,
            controller_mode="random",
        ),
        earth_radius=EARTH_RADIUS,
        earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
        satellite=SATELLITE,
        satellite_altitude=satellite_altitude,
        theta_center_rad=float(theta_center),
        start_angle_deg=float(start_angle_deg),
        end_angle_deg=float(end_angle_deg),
        sat_motion_span_scale=float(SIMULATION.sat_motion_span_scale),
        sat_z_offset_deg=float(SIMULATION.sat_z_offset.to(ureg.deg).magnitude),
        ureg=ureg,
        camera_pixel_ray_samples=SIMULATION.camera_pixel_ray_samples,
        reward_config=RewardConfig(),
    )


def _load_actor_from_bytes(
    *,
    payload: bytes,
    obs_size: int,
    action_size: int,
    action_low: np.ndarray,
    action_high: np.ndarray,
    config: MPOConfig,
    device: torch.device,
) -> Actor:
    action_low_t = torch.as_tensor(action_low, dtype=torch.float32, device=device)
    action_high_t = torch.as_tensor(action_high, dtype=torch.float32, device=device)
    actor = Actor(
        action_low_t,
        action_high_t,
        obs_size,
        action_size,
        config.num_layers_actor,
        config.num_units_actor,
        config.activation_actor,
        config.actor_dropout,
    ).to(device)
    state_dict = torch.load(io.BytesIO(payload), map_location=device)
    actor.load_state_dict(state_dict)
    actor.eval()
    return actor


def _serialize_policy_state_dict(state_dict: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    torch.save(state_dict, buffer)
    return buffer.getvalue()


def serialize_policy_for_workers(agent: Any) -> bytes:
    return _serialize_policy_state_dict(agent.pi.state_dict())


def _worker_loop(
    worker_id: int,
    task_queue: mp.Queue,
    result_queue: mp.Queue,
    obs_size: int,
    action_size: int,
    action_low: np.ndarray,
    action_high: np.ndarray,
    config: MPOConfig,
    base_seed: int,
    satellite_altitude: Any,
) -> None:
    device = torch.device("cpu")
    worker_seed = derive_seed(base_seed, "parallel_worker", worker_id)
    apply_global_seed(worker_seed)
    worker_rng = np.random.default_rng(worker_seed)
    while True:
        task = task_queue.get()
        if task is None:
            return
        assert isinstance(task, WorkerTask)
        actor = _load_actor_from_bytes(
            payload=task.policy_state_bytes,
            obs_size=obs_size,
            action_size=action_size,
            action_low=action_low,
            action_high=action_high,
            config=config,
            device=device,
        )
        stepper = _build_stepper(satellite_altitude=satellite_altitude)
        current_ts = stepper.current_timestep_state()
        obs = build_state_vector_from_timestep(
            timestep=current_ts,
        )
        current_action_nm = 0.0
        episode_return = 0.0
        steps = 0
        obs_batch: list[np.ndarray] = []
        actions_batch: list[np.ndarray] = []
        rewards_batch: list[float] = []
        next_obs_batch: list[np.ndarray] = []
        done_batch: list[float] = []
        train_mode = task.mode in {"warmup", "train"}
        action_low_t = torch.as_tensor(action_low, dtype=torch.float32, device=device)
        action_high_t = torch.as_tensor(action_high, dtype=torch.float32, device=device)
        action_scale = (action_high_t - action_low_t) / 2.0
        action_bias = (action_high_t + action_low_t) / 2.0
        while not stepper.done:
            if stepper.should_update_controller():
                if task.mode == "warmup":
                    current_action_nm = float(worker_rng.uniform(-1.0, 1.0))
                else:
                    obs_tensor = torch.as_tensor(obs, dtype=torch.float32, device=device)
                    with torch.no_grad():
                        dist = actor(obs_tensor)
                        action_gaussian = dist.rsample() if train_mode else dist.mean
                        action_scaled = torch.tanh(action_gaussian) * action_scale + action_bias
                    current_action_nm = float(action_scaled.detach().cpu().numpy().reshape(-1)[0])
            next_ts = stepper.step(wheel_torque_cmd_nm=current_action_nm)
            next_obs = build_state_vector_from_timestep(
                timestep=next_ts,
            )
            reward = float(next_ts.reward)
            done = bool(stepper.done)
            obs_batch.append(obs.copy())
            actions_batch.append(np.array([current_action_nm], dtype=np.float32))
            rewards_batch.append(reward)
            next_obs_batch.append(next_obs.copy())
            done_batch.append(1.0 if done else 0.0)
            episode_return += reward
            obs = next_obs
            current_ts = next_ts
            steps += 1
        result_queue.put(
            WorkerResult(
                worker_id=int(worker_id),
                episode_idx=int(task.episode_idx),
                episode_return=float(episode_return),
                steps=int(steps),
                obs=np.asarray(obs_batch, dtype=np.float32),
                actions=np.asarray(actions_batch, dtype=np.float32),
                rewards=np.asarray(rewards_batch, dtype=np.float32),
                next_obs=np.asarray(next_obs_batch, dtype=np.float32),
                done=np.asarray(done_batch, dtype=np.float32),
            )
        )


class ParallelMPOTrainer:
    """Shared learner, parallel rollout workers.

    Contract:
    - worker -> learner: batched transitions `(obs, action, reward, next_obs, done)` + episode summary.
    - learner -> worker: serialized policy state bytes refreshed each dispatched episode.
    """

    def __init__(
        self,
        *,
        agent: Any,
        env: Any,
        num_workers: int,
        telemetry_writer: RunTelemetryWriter | None = None,
        seed: int = 0,
        satellite_altitude: Any | None = None,
    ) -> None:
        if num_workers < 2:
            raise ValueError("num_workers must be >= 2 for parallel training.")
        self.agent = agent
        self.env = env
        self.num_workers = int(num_workers)
        self.telemetry_writer = telemetry_writer
        self.seed = int(seed)
        self.satellite_altitude = satellite_altitude if satellite_altitude is not None else SATELLITE_ALTITUDE
        self._ctx = mp.get_context("spawn")
        self._task_queue: mp.Queue = self._ctx.Queue(maxsize=max(4, self.num_workers * 2))
        self._result_queue: mp.Queue = self._ctx.Queue(maxsize=max(4, self.num_workers * 2))
        self._workers: list[mp.Process] = []

    def __enter__(self) -> "ParallelMPOTrainer":
        obs_size = int(np.prod(self.env.observation_space.shape))
        action_size = int(np.prod(self.env.action_space.shape))
        action_low = np.asarray(self.env.action_space.low, dtype=np.float32)
        action_high = np.asarray(self.env.action_space.high, dtype=np.float32)
        config = self.agent.config
        for worker_id in range(self.num_workers):
            proc = self._ctx.Process(
                target=_worker_loop,
                args=(
                    worker_id,
                    self._task_queue,
                    self._result_queue,
                    obs_size,
                    action_size,
                    action_low,
                    action_high,
                    config,
                    self.seed,
                    self.satellite_altitude,
                ),
                daemon=True,
            )
            proc.start()
            self._workers.append(proc)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        for _ in self._workers:
            self._task_queue.put(None)
        for proc in self._workers:
            proc.join(timeout=5.0)

    def run_phase(
        self,
        *,
        phase: str,
        episode_count: int,
        train_updates_per_step: int,
    ) -> list[dict[str, float]]:
        if episode_count <= 0:
            return []
        policy_bytes = serialize_policy_for_workers(self.agent)
        next_to_submit = 0
        next_to_collect = 0
        in_flight = 0
        started_at = time.perf_counter()
        returns_window: list[float] = []
        completed: list[dict[str, float]] = []

        while next_to_collect < episode_count:
            while in_flight < self.num_workers and next_to_submit < episode_count:
                ep_idx = next_to_submit
                self._task_queue.put(
                    WorkerTask(
                        episode_idx=ep_idx,
                        mode=phase,
                        policy_state_bytes=policy_bytes,
                    )
                )
                if self.telemetry_writer is not None:
                    self.telemetry_writer.on_worker_status(
                        worker_id=ep_idx % self.num_workers,
                        status="running",
                        episode_idx=ep_idx,
                    )
                next_to_submit += 1
                in_flight += 1
            try:
                result = self._result_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            assert isinstance(result, WorkerResult)
            in_flight -= 1
            next_to_collect += 1

            for i in range(result.obs.shape[0]):
                transition = (
                    result.obs[i],
                    result.actions[i],
                    float(result.rewards[i]),
                    result.next_obs[i],
                    bool(result.done[i] > 0.5),
                )
                self.agent.store(transition)
                if phase == "train":
                    for _ in range(train_updates_per_step):
                        self.agent.train()

            elapsed = max(1e-9, time.perf_counter() - started_at)
            eps = float(next_to_collect / elapsed)
            returns_window.append(float(result.episode_return))
            if len(returns_window) > 25:
                returns_window.pop(0)
            rolling = float(np.mean(np.asarray(returns_window, dtype=np.float64)))
            completed.append(
                {
                    "episode_idx": float(result.episode_idx),
                    "episode_return": float(result.episode_return),
                    "steps": float(result.steps),
                    "episodes_per_second": eps,
                    "rolling_return_mean": rolling,
                }
            )
            if self.telemetry_writer is not None:
                self.telemetry_writer.on_worker_status(
                    worker_id=result.worker_id,
                    status="idle",
                    episode_idx=result.episode_idx,
                )
                self.telemetry_writer.on_episode_finished(
                    phase=phase,
                    episode_idx=result.episode_idx,
                    episode_return=result.episode_return,
                    steps=result.steps,
                    episodes_per_second=eps,
                    rolling_return_mean=rolling,
                )

            if phase == "train":
                policy_bytes = serialize_policy_for_workers(self.agent)
        return completed
