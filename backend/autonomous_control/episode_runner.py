"""EpisodeRunner: serial episode execution using the shared stepper factory.



Owns the agent loop (tqdm, warmup/train/mpo dispatch) and returns EpisodeResult.

"""

from __future__ import annotations



import sys
import warnings
from pathlib import Path

from typing import Any



import numpy as np

from tqdm.auto import tqdm



from autonomous_control.action_adapter import (
    POLICY_RAW_DIM,
    policy_output_to_gym_action,
)

from autonomous_control.baseline_overflight_step import baseline_overflight_controller_tick

from autonomous_control.reward import RewardConfig

from environment_definition.constants.SIMULATION import training_episode_simulation_config

from simulation.setup_types import EnvironmentSetup

from simulation.stepper_factory import build_stepper

from simulation.take_picture import TakePictureBudget, TakePictureConfig



from .feature_selection import ControllerFeatureConfig

from .controller_observation import (
    ControllerEpisodeContext,
    ControllerObservationLayout,
    build_controller_observation_from_timestep,
    controller_observation_layout,
    resolve_target_anchor_xy_km,
)

from .training_metrics import collect_episode_learning_stats, snapshot_metrics_start


from .training_progress_display import TrainingProgressDisplay

from .training_runtime import EpisodeResult, _in_notebook





class EpisodeRunner:

    """Serial episode runner backed by the shared stepper factory.



    Usage::



        setup = build_setup(seed=SEED)

        result = EpisodeRunner(setup).run_serial(agent, mode="warmup")

    """



    def __init__(self, setup: EnvironmentSetup) -> None:

        self._setup = setup

        self._resolved = setup.resolve(require_camera=False)

        earth_radius_km = float(self._resolved.earth_radius.to(self._resolved.ureg.km).magnitude)

        self._target_anchor_xy_km = resolve_target_anchor_xy_km(

            tuple(self._resolved.target_areas or ()),

            earth_radius_km=earth_radius_km,

        )



    def run_serial(

        self,

        agent: Any,

        *,

        mode: str,

        train_updates_per_step: int = 1,

        train_every_n_steps: int = 1,

        collect_states: bool = False,

        step_callback: Any | None = None,

        warmup_controller: str = "baseline",

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

        observation_layout: ControllerObservationLayout | None = None,

        warmup_capture_targets: tuple[int, ...] | None = None,

    ) -> EpisodeResult:

        """Run one episode and return EpisodeResult with SimulationStateSeries."""

        if hasattr(agent, "reset_episode"):

            agent.reset_episode()



        if mode == "warmup" and warmup_controller not in _WARMUP_OVERFLIGHT_CONTROLLERS:
            raise ValueError(
                f"mode='warmup' only supports sequential baseline overflight; "
                f"got warmup_controller={warmup_controller!r}. "
                "Torque-only random/sweep warmups were removed."
            )

        if mode == "warmup":
            torque_policy_label = "sequential_target_baseline"
        else:
            torque_policy_label = _infer_torque_policy_label(agent, mode)

        sim_config = training_episode_simulation_config(

            torque_policy_label=torque_policy_label,

        )

        stepper = build_stepper(self._resolved, simulation_config=sim_config)



        tau_max_nm = float(

            self._resolved.satellite.reaction_wheel_max_torque

            .to(self._resolved.ureg.N * self._resolved.ureg.m)

            .magnitude

        )

        tau_limit = self._resolved.satellite.reaction_wheel_max_torque

        overflight_policy: Any | None = None

        if mode == "warmup":
            capture_targets: tuple[int, ...] | None = warmup_capture_targets
            if capture_targets is None:
                capture_targets = tuple(range(len(self._target_anchor_xy_km)))
            overflight_policy = _build_warmup_overflight_policy(
                self._setup,
                self._resolved,
                capture_targets=capture_targets,
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

            early_stop_on_budget_exhausted = False



        feat_cfg = feature_config if feature_config is not None else ControllerFeatureConfig()

        n_mission_targets = len(self._target_anchor_xy_km)

        obs_layout = observation_layout

        if obs_layout is None:

            obs_layout = controller_observation_layout(

                feature_config=feat_cfg,

                secondary_camera_observation_line_n_bins=int(

                    self._resolved.secondary_camera_observation_line_n_bins

                ),

                n_mission_targets=n_mission_targets,

            )



        def _episode_context() -> ControllerEpisodeContext | None:

            if not feat_cfg.needs_mission_scalars:

                return None

            remaining = float(budget.remaining) if budget is not None else 0.0
            captured = (
                frozenset(budget.captured_target_indices)
                if budget is not None
                else frozenset()
            )

            return ControllerEpisodeContext(

                capture_budget_remaining=remaining,

                target_anchor_xy_km=self._target_anchor_xy_km,

                captured_target_indices=captured,

            )



        current_ts = stepper.current_timestep_state()

        obs = build_controller_observation_from_timestep(

            timestep=current_ts,

            feature_config=feat_cfg,

            layout=obs_layout,

            episode_context=_episode_context(),

        )

        states: list = [obs.copy()] if collect_states else []

        current_action_nm = 0.0

        current_take_picture_signal = -1.0

        take_picture_cmd = False

        stored_action = np.array([0.0, -1.0], dtype=np.float32)

        episode_return = 0.0

        steps = 0
        pilot_store_count = 0
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

                pilot_command_issued = False

                if stepper.should_update_controller():

                    pilot_command_issued = True

                    if mode == "warmup":

                        if overflight_policy is None:

                            raise RuntimeError("overflight_policy must be configured in warmup mode.")

                        ctrl_state = stepper.current_timestep_state()

                        sat_xy = np.asarray(ctrl_state.sat_pos_xy_km, dtype=float)

                        _action, stored_action, take_picture_cmd = baseline_overflight_controller_tick(

                            policy=overflight_policy,

                            stepper=stepper,

                            state=ctrl_state,

                            sat_pos_xy_km=sat_xy,

                            omega_orbit_rad_s=float(stepper._omega_orbit_rad_s),

                            sat_inertia=self._resolved.satellite.moment_of_inertia_2d,

                            tau_max_nm=tau_max_nm,

                            budget=budget,

                        )

                        current_action_nm = float(_action.torque_request_nm)

                        current_take_picture_signal = float(stored_action[1])

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

                        feature_config=feat_cfg,

                        layout=obs_layout,

                        episode_context=_episode_context(),

                    )

                    states.append(next_obs.copy())

                else:

                    next_obs = build_controller_observation_from_timestep(

                        timestep=next_ts,

                        feature_config=feat_cfg,

                        layout=obs_layout,

                        episode_context=_episode_context(),

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

                        capture_budget_remaining=(
                            int(budget.remaining) if budget is not None else None
                        ),
                        safe_mode_activations=int(stepper.safe_mode_takeover_count),
                    )



                if (
                    pilot_command_issued
                    and mode in {"warmup", "train"}
                    and hasattr(agent, "store")
                ):

                    agent.store((obs, stored_action.copy(), reward, next_obs, done))

                    if mode == "train":

                        pilot_store_count += 1

                        if (pilot_store_count % train_stride) == 0:

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





_WARMUP_OVERFLIGHT_CONTROLLERS = frozenset({"baseline", "overflight"})


def _build_warmup_overflight_policy(
    setup: EnvironmentSetup,
    resolved: Any,
    *,
    capture_targets: tuple[int, ...] | None = None,
) -> Any:
    """Build notebook-07 sequential baseline policy for warmup episodes."""
    import sys
    from pathlib import Path

    s01 = Path(__file__).resolve().parents[1] / "notebooks" / "s01"
    if str(s01) not in sys.path:
        sys.path.insert(0, str(s01))
    from s01_utils.baseline_overflight import build_overflight_policy

    earth_radius_km = float(resolved.earth_radius.to(resolved.ureg.km).magnitude)
    return build_overflight_policy(
        setup,
        earth_radius_km=earth_radius_km,
        capture_targets=capture_targets,
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

