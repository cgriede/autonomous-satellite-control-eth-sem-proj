"""EpisodeRunner: serial episode execution using the shared stepper factory.



Owns the agent loop (tqdm, warmup/train/mpo dispatch) and returns EpisodeResult.

"""

from __future__ import annotations



import sys
import warnings

from typing import Any



import numpy as np

from tqdm.auto import tqdm



from autonomous_control.action_adapter import (
    POLICY_RAW_DIM,
    policy_output_to_gym_action,
)

from autonomous_control.reward import RewardConfig

from environment_definition.constants.SIMULATION import training_episode_simulation_config

from simulation.setup_types import EnvironmentSetup

from simulation.stepper_factory import build_stepper

from simulation.take_picture import TakePictureBudget, TakePictureConfig



from .feature_selection import ControllerFeatureConfig

from .controller_observation import build_controller_observation_from_timestep

from .training_metrics import collect_episode_learning_stats, snapshot_metrics_start

from .training_progress_display import TrainingProgressDisplay

from .training_runtime import EpisodeResult, _in_notebook





class EpisodeRunner:

    """Serial episode runner backed by the shared stepper factory.



    Usage::



        setup = build_setup(seed=SEED)

        result = EpisodeRunner(setup).run_serial(agent, mode="warmup", warmup_controller="random")

    """



    def __init__(self, setup: EnvironmentSetup) -> None:

        self._setup = setup

        self._resolved = setup.resolve(require_camera=False)



    def run_serial(

        self,

        agent: Any,

        *,

        mode: str,

        train_updates_per_step: int = 1,

        train_every_n_steps: int = 1,

        collect_states: bool = False,

        step_callback: Any | None = None,

        warmup_controller: str = "random",

        warmup_baseline_period_s: float = 60.0,

        feature_config: ControllerFeatureConfig | None = None,

        np_rng: np.random.Generator | None = None,

        verbose_print: int = 0,

        show_simulation_info: bool | None = None,

        show_training_context: bool | None = None,

        show_config_panel: bool = False,

        episode_idx: int = 0,

        progress_display: TrainingProgressDisplay | None = None,

        early_stop_on_budget_exhausted: bool | None = None,

    ) -> EpisodeResult:

        """Run one episode and return EpisodeResult with SimulationStateSeries."""

        if hasattr(agent, "reset_episode"):

            agent.reset_episode()



        torque_policy_label = _infer_torque_policy_label(agent, mode)

        sim_config = training_episode_simulation_config(

            torque_policy_label=torque_policy_label,

        )

        stepper = build_stepper(self._resolved, simulation_config=sim_config)



        episode_rng = np_rng if np_rng is not None else np.random.default_rng()



        tau_max_nm = float(

            self._resolved.satellite.reaction_wheel_max_torque

            .to(self._resolved.ureg.N * self._resolved.ureg.m)

            .magnitude

        )

        tau_limit = self._resolved.satellite.reaction_wheel_max_torque

        warmup_policy: Any | None = None

        if mode == "warmup":

            warmup_policy = _make_warmup_policy(

                warmup_controller=warmup_controller,

                tau_max_nm=tau_max_nm,

                dt=stepper._dt,

                period_s=warmup_baseline_period_s,

                rng=episode_rng,

            )



        reward_config = (

            self._resolved.reward_config

            if self._resolved.reward_config is not None

            else RewardConfig()

        )

        capture_enabled = bool(reward_config.enable_image_quality_capture)

        budget: TakePictureBudget | None = None

        if capture_enabled:

            budget = TakePictureBudget.from_config(TakePictureConfig())



        if early_stop_on_budget_exhausted is None:

            early_stop_on_budget_exhausted = capture_enabled and mode in {"warmup", "train"}



        current_ts = stepper.current_timestep_state()

        obs = build_controller_observation_from_timestep(

            timestep=current_ts,

            feature_config=feature_config,

            secondary_camera_observation_line_n_bins=int(

                self._resolved.secondary_camera_observation_line_n_bins

            ),

        )

        states: list = [obs.copy()] if collect_states else []

        current_action_nm = 0.0

        current_take_picture_signal = -1.0

        take_picture_cmd = False

        stored_action = np.array([0.0, -1.0], dtype=np.float32)

        episode_return = 0.0

        steps = 0
        ended_early_on_budget = False

        train_mode = mode in {"warmup", "train"}

        episode_total_steps = stepper.total_steps

        is_mpo_agent = type(agent).__name__ == "MPOAgent"

        if show_config_panel:
            show_simulation_info = True
            show_training_context = False
        else:
            if show_simulation_info is None:
                show_simulation_info = not (
                    is_mpo_agent and mode in {"warmup", "train", "eval"}
                )
            if show_training_context is None:
                show_training_context = not show_simulation_info and is_mpo_agent
            if progress_display is not None:
                show_simulation_info = False
                show_training_context = False



        metrics_start = snapshot_metrics_start(agent) if mode == "train" else None

        train_stride = max(1, int(train_every_n_steps))



        use_internal_bar = verbose_print == 0 and progress_display is None

        progress_bar = tqdm(

            total=int(episode_total_steps),

            desc=f"{mode} episode",

            unit="step",

            leave=False,

            dynamic_ncols=True,

            file=sys.stdout,

            disable=not use_internal_bar,

        )

        if progress_display is not None:

            progress_display.begin_episode(

                mode=mode,

                episode_idx=episode_idx,

                total_steps=int(episode_total_steps),

                agent=agent,

                metrics_start=metrics_start,

            )

        if verbose_print == 0:

            if show_simulation_info:

                from simulation.simulation_info import print_simulation_info



                print_simulation_info(

                    stepper,

                    simulation_config=sim_config,

                    tau_max_nm=tau_max_nm,

                    agent=agent,

                    episode_mode=mode,

                )

            elif show_training_context:

                from simulation.simulation_info import print_training_context



                print_training_context(

                    stepper,

                    simulation_config=sim_config,

                    tau_max_nm=tau_max_nm,

                    agent=agent,

                    episode_mode=mode,

                )



        try:

            while not stepper.done and steps < int(episode_total_steps):

                take_picture_cmd = False

                if stepper.should_update_controller():

                    if mode == "warmup":

                        if warmup_policy is None:

                            raise RuntimeError("warmup_policy must be configured in warmup mode.")

                        action_vec = warmup_policy.get_action(obs, train=False)

                        current_action_nm = float(

                            np.asarray(action_vec, dtype=np.float64).reshape(-1)[0]

                        )

                        current_take_picture_signal = -1.0

                        take_picture_cmd = False

                        stored_action = np.array(

                            [current_action_nm, current_take_picture_signal],

                            dtype=np.float32,

                        )

                    else:

                        action_vec = np.asarray(

                            agent.get_action(obs, train=train_mode), dtype=np.float64

                        ).reshape(-1)

                        if action_vec.shape[0] == 1:

                            torque_raw = float(action_vec[0])

                            shutter_raw = -1.0

                        elif action_vec.shape[0] >= POLICY_RAW_DIM:

                            torque_raw = float(action_vec[0])

                            shutter_raw = float(action_vec[1])

                        else:

                            raise ValueError(

                                f"Agent action must have shape (1,) or ({POLICY_RAW_DIM},), "

                                f"got {action_vec.shape}."

                            )

                        parsed, stored_action = policy_output_to_gym_action(

                            np.array([torque_raw, shutter_raw], dtype=np.float64),

                            tau_limit=tau_limit,

                        )

                        current_action_nm = float(

                            parsed.wheel_torque_cmd.to(self._resolved.ureg.N * self._resolved.ureg.m).magnitude

                        )

                        current_take_picture_signal = shutter_raw

                        take_picture_cmd = parsed.active_observation



                next_ts = stepper.step(wheel_torque_cmd_nm=current_action_nm)

                cmd_step = stepper.current_index

                if take_picture_cmd and budget is not None:

                    capture = stepper.apply_shutter_capture(cmd_step, budget)

                    next_ts = stepper.current_timestep_state()

                    _ = capture



                reward = float(next_ts.reward)

                done = bool(stepper.done)



                if (

                    early_stop_on_budget_exhausted

                    and budget is not None

                    and budget.remaining == 0

                ):

                    stepper.truncate_to_step_index(cmd_step)

                    done = True
                    ended_early_on_budget = True



                episode_return += reward

                if collect_states:

                    next_obs = build_controller_observation_from_timestep(

                        timestep=next_ts,

                        feature_config=feature_config,

                        secondary_camera_observation_line_n_bins=int(

                            self._resolved.secondary_camera_observation_line_n_bins

                        ),

                    )

                    states.append(next_obs.copy())

                else:

                    next_obs = build_controller_observation_from_timestep(

                        timestep=next_ts,

                        feature_config=feature_config,

                        secondary_camera_observation_line_n_bins=int(

                            self._resolved.secondary_camera_observation_line_n_bins

                        ),

                    )



                if step_callback is not None:

                    step_callback(next_ts)



                if progress_display is not None:

                    progress_display.on_step(

                        next_ts,

                        step=steps + 1,

                        reward=reward,

                        episode_return=episode_return,

                        done=done,

                    )



                if mode in {"warmup", "train"} and hasattr(agent, "store"):

                    agent.store((obs, stored_action.copy(), reward, next_obs, done))

                    if mode == "train" and ((steps + 1) % train_stride) == 0:

                        for _ in range(train_updates_per_step):

                            if hasattr(agent, "train"):

                                agent.train()



                obs = next_obs

                current_ts = next_ts

                steps += 1

                if use_internal_bar:

                    progress_bar.update(1)

                    if (steps % 10) == 0 or done:

                        progress_bar.set_postfix(

                            steps=steps, reward=f"{reward:.5f}", refresh=False

                        )

                if done:

                    break

        finally:

            progress_bar.close()

            if progress_display is not None:

                progress_display.end_episode()



        if ended_early_on_budget:
            early_msg = (
                f"[run_serial] WARNING: episode ended early — capture budget exhausted "
                f"at step {steps}/{episode_total_steps} (mode={mode})"
            )
            warnings.warn(early_msg, UserWarning, stacklevel=2)
            if verbose_print == 0:
                if _in_notebook():
                    print(early_msg)
                elif progress_display is not None:
                    progress_display.write(early_msg)
                else:
                    tqdm.write(early_msg, file=sys.stdout)

        if verbose_print == 0:

            avg_reward = episode_return / max(1, steps)

            end_msg = (

                f"[run_serial] end mode={mode} steps={steps} "

                f"total_reward={episode_return:.6f} avg_reward={avg_reward:.6f}"

            )

            if _in_notebook():

                print(end_msg)

            else:

                if progress_display is not None:
                    progress_display.write(end_msg)
                else:
                    tqdm.write(end_msg, file=sys.stdout)



        context = stepper.build_episode_context()

        learning_stats = collect_episode_learning_stats(

            agent,

            phase=mode,

            episode_idx=episode_idx,

            episode_return=episode_return,

            steps=steps,

            mode=mode,

            metrics_start=metrics_start,

        )

        return EpisodeResult(

            episode_return=episode_return,

            steps=steps,

            states=states,

            simulation_series=context.simulation_series,

            configured_controller_update_interval_s=context.configured_controller_update_interval_s,

            effective_controller_update_interval_s=context.effective_controller_update_interval_s,

            effective_controller_update_interval_steps=context.effective_controller_update_interval_steps,

            learning_stats=learning_stats,

            ended_early_on_budget=ended_early_on_budget,

            configured_episode_steps=int(episode_total_steps),

        )





def _infer_torque_policy_label(agent: Any, mode: str) -> str:

    """Map agent class + episode mode to metadata torque_policy_label (external command source)."""

    class_name = type(agent).__name__.lower()

    if "random" in class_name:

        return "random_torque_agent"

    if "sweep" in class_name or "baseline" in class_name:

        return "max_torque_sweep_agent"

    if "delayed" in class_name and "max" in class_name:

        return "delayed_max_torque"

    if "zero" in class_name:

        return "zero_torque"

    return f"{type(agent).__name__}:{mode}"





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


