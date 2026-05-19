"""EpisodeRunner: serial episode execution using the shared stepper factory.

Owns the agent loop (tqdm, warmup/train/mpo dispatch) and returns EpisodeResult.
Camera wiring (require_camera=True) is reserved for the follow-up SensorKernel slice.
"""
from __future__ import annotations

import sys
from typing import Any

import numpy as np
from tqdm.auto import tqdm

from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig
from simulation.setup_types import SimulationSetupConfig
from simulation.stepper_factory import build_stepper

from .feature_selection import ControllerFeatureConfig
from .training_runtime import (
    EpisodeResult,
    _in_notebook,
    build_state_vector_from_timestep,
)


class EpisodeRunner:
    """Serial episode runner backed by the shared stepper factory.

    Usage::

        setup = build_setup(seed=SEED)
        result = EpisodeRunner(setup).run_serial(agent, mode="warmup", warmup_controller="random")
    """

    def __init__(self, setup: SimulationSetupConfig) -> None:
        self._setup = setup
        # v1: cameras not yet wired into SensorKernel — require_camera stays False.
        self._resolved = setup.resolve(require_camera=False)

    def run_serial(
        self,
        agent: Any,
        *,
        mode: str,
        train_updates_per_step: int = 1,
        step_callback: Any | None = None,
        warmup_controller: str = "random",
        warmup_baseline_period_s: float = 60.0,
        feature_config: ControllerFeatureConfig | None = None,
        np_rng: np.random.Generator | None = None,
        verbose_print: int = 0,
    ) -> EpisodeResult:
        """Run one episode and return EpisodeResult with SimulationStateSeries.

        Args:
            agent: Policy with get_action(obs, train) → np.ndarray.
            mode: "warmup" | "train" | "mpo" | "eval".
            train_updates_per_step: Number of agent.train() calls per step in train mode.
            step_callback: Optional callable(SimulationTimestepState) called after each step.
            warmup_controller: "random" | "baseline" — warmup policy when mode=="warmup".
            warmup_baseline_period_s: Period for MaxTorqueSweepPolicy when baseline warmup.
            feature_config: Override for controller state vector feature selection.
            np_rng: Optional numpy Generator for reproducible warmup randomness.
            verbose_print: 0 = tqdm progress; non-zero = suppress tqdm.

        Returns:
            EpisodeResult with populated simulation_series.
        """
        if hasattr(agent, "reset_episode"):
            agent.reset_episode()

        controller_mode = _infer_controller_mode(agent, mode)
        sim_config = SimulationConfig(
            render_mode=RenderMode.HEADLESS,
            controller_mode=controller_mode,  # type: ignore[arg-type]
        )
        stepper = build_stepper(self._resolved, simulation_config=sim_config)

        episode_rng = np_rng if np_rng is not None else np.random.default_rng()

        # Build a lightweight adapter so baseline controllers can read action bounds / dt.
        tau_max_nm = float(
            self._resolved.satellite.reaction_wheel_max_torque
            .to(self._resolved.ureg.N * self._resolved.ureg.m)
            .magnitude
        )
        warmup_policy: Any | None = None
        if mode == "warmup":
            warmup_policy = _make_warmup_policy(
                warmup_controller=warmup_controller,
                tau_max_nm=tau_max_nm,
                dt=stepper._dt,
                period_s=warmup_baseline_period_s,
                rng=episode_rng,
            )

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
            total=int(episode_total_steps),
            desc=f"{mode} episode",
            unit="step",
            leave=False,
            dynamic_ncols=True,
            file=sys.stdout,
            disable=verbose_print != 0,
        )
        if verbose_print == 0:
            progress_bar.write(
                f"[run_serial] start mode={mode} max_steps={episode_total_steps}"
            )

        try:
            while not stepper.done and steps < int(episode_total_steps):
                if stepper.should_update_controller():
                    if mode == "warmup":
                        if warmup_policy is None:
                            raise RuntimeError("warmup_policy must be configured in warmup mode.")
                        action_vec = warmup_policy.get_action(obs, train=False)
                        current_action_nm = float(
                            np.asarray(action_vec, dtype=np.float64).reshape(-1)[0]
                        )
                    else:
                        action_vec = agent.get_action(obs, train=train_mode)
                        current_action_nm = float(
                            np.asarray(action_vec, dtype=np.float64).reshape(-1)[0]
                        )

                next_ts = stepper.step(wheel_torque_cmd_nm=current_action_nm)
                next_obs = build_state_vector_from_timestep(
                    timestep=next_ts,
                    feature_config=feature_config,
                )
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
                    progress_bar.set_postfix(
                        steps=steps, reward=f"{reward:.5f}", refresh=False
                    )
        finally:
            progress_bar.close()

        if verbose_print == 0:
            avg_reward = episode_return / max(1, steps)
            end_msg = (
                f"[run_serial] end mode={mode} steps={steps} "
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


def _infer_controller_mode(agent: Any, mode: str) -> str:
    """Map agent class name + episode mode to a SimulationConfig controller_mode string."""
    class_name = type(agent).__name__.lower()
    if "random" in class_name:
        return "random"
    if "sweep" in class_name or "baseline" in class_name:
        return "baseline"
    return "mpo"


def _make_warmup_policy(
    *,
    warmup_controller: str,
    tau_max_nm: float,
    dt: Any,
    period_s: float,
    rng: np.random.Generator,
) -> Any:
    """Build a warmup policy from first principles — no env adapter required."""
    from gymnasium import spaces

    from .controller_baselines import MaxTorqueSweepPolicy, RandomTorquePolicy

    action_space = spaces.Box(
        low=np.array([-tau_max_nm], dtype=np.float32),
        high=np.array([tau_max_nm], dtype=np.float32),
        shape=(1,),
        dtype=np.float32,
    )

    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _Adapter:
        action_space: Any
        dt: Any

    adapter = _Adapter(action_space=action_space, dt=dt)

    if warmup_controller == "random":
        policy = RandomTorquePolicy(adapter, rng=rng)
    elif warmup_controller == "baseline":
        policy = MaxTorqueSweepPolicy(adapter, period_s=period_s)
    else:
        raise ValueError(f"Unsupported warmup_controller: {warmup_controller!r}")

    policy.reset_episode()
    return policy
