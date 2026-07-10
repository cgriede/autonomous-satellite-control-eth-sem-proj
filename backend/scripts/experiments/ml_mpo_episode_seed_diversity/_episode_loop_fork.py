"""Custom episode loop for factored MPO + move-gated OBC (replaces EpisodeRunner)."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

import numpy as np

from autonomous_control.training_metrics import snapshot_metrics_start

from autonomous_control.baseline_overflight_step import (
    apply_baseline_shutter_if_requested,
    baseline_overflight_controller_tick,
)
from autonomous_control.controller_observation import (
    ControllerEpisodeContext,
    ControllerObservationLayout,
    build_controller_observation_from_timestep,
    controller_observation_layout,
    resolve_target_anchor_xy_km,
)
from autonomous_control.feature_selection import ControllerFeatureConfig
from autonomous_control.reward import RewardConfig
from environment_definition.constants.SIMULATION import training_episode_simulation_config
from simulation.attitude_controller import target_boresight_angle_rad
from simulation.obc_pointing_request import ObcPointingResolver, theta_target_to_u
from simulation.setup_types import EnvironmentSetup, SimulationOverrides
from simulation.stepper_factory import build_stepper
from simulation.take_picture import TakePictureBudget, TakePictureConfig

from s01_utils.baseline_overflight import build_overflight_policy, warmup_capture_targets

from _action_constants import (
    N_ACTION_DIMS,
    N_TARGETS,
    decode_move,
    decode_shutter,
    decode_target_idx,
    encode_warmup_action,
)
from _mission_score import compute_episode_mission_score
from simulation.simulation_info import print_simulation_info


@dataclass(frozen=True)
class Exp14EpisodeResult:
    episode_return: float
    steps: int
    simulation_series: Any
    cmd_steps: tuple[int, ...]
    mission_score: float
    configured_episode_steps: int = 0
    vector_hold_last_count: int | None = None
    selected_target_indices: tuple[int, ...] = ()
    """Target index chosen by the policy at each controller tick (train/eval only)."""


def _build_warmup_policy(setup: EnvironmentSetup, resolved, *, episode_idx: int, targets_per_episode: int):
    earth_radius_km = float(resolved.earth_radius.to(resolved.ureg.km).magnitude)
    n_targets = len(setup.target_areas or ())
    capture_targets = warmup_capture_targets(
        int(episode_idx),
        n_targets=n_targets,
        targets_per_episode=int(targets_per_episode),
    )
    return build_overflight_policy(
        setup,
        earth_radius_km=earth_radius_km,
        capture_targets=capture_targets,
    )


def run_exp14_episode(
    setup: EnvironmentSetup,
    agent: Any,
    *,
    mode: str,
    feature_config: ControllerFeatureConfig,
    observation_layout: ControllerObservationLayout | None = None,
    episode_idx: int = 0,
    train_updates_per_step: int = 1,
    train_every_n_steps: int = 1,
    warmup_targets_per_episode: int = 10,
    reward_config: RewardConfig | None = None,
    show_progress: bool = False,
    show_config_panel: bool = False,
    progress_display: Any | None = None,
    phase_episode_total: int | None = None,
    experiment_name: str | None = None,
) -> Exp14EpisodeResult:
    if mode not in {"warmup", "train", "eval"}:
        raise ValueError(f"Unsupported mode: {mode!r}")

    if reward_config is not None:
        overrides = setup.simulation_overrides or SimulationOverrides()
        setup = replace(
            setup,
            simulation_overrides=replace(overrides, reward_config=reward_config),
        )

    resolved = setup.resolve(require_camera=False)
    earth_radius_km = float(resolved.earth_radius.to(resolved.ureg.km).magnitude)
    target_anchor_xy_km = resolve_target_anchor_xy_km(
        tuple(resolved.target_areas or ()),
        earth_radius_km=earth_radius_km,
    )
    n_mission_targets = len(target_anchor_xy_km)

    sim_config = training_episode_simulation_config(
        torque_policy_label=(
            "sequential_target_baseline" if mode == "warmup" else "factored_target_select"
        ),
        attitude_request_mode="vector",
    )
    stepper = build_stepper(resolved, simulation_config=sim_config)
    ctrl0 = stepper.current_timestep_state()
    stepper.reset_vector_pointing_episode(theta_orbit_rad=float(ctrl0.theta_orbit_rad))

    tau_max_nm = float(
        resolved.satellite.reaction_wheel_max_torque.to(resolved.ureg.N * resolved.ureg.m).magnitude
    )
    sat_inertia = resolved.satellite.moment_of_inertia_2d
    omega_orbit_rad_s = float(stepper._omega_orbit_rad_s)

    reward_cfg = reward_config if reward_config is not None else RewardConfig()
    budget: TakePictureBudget | None = None
    if bool(reward_cfg.enable_image_quality_capture):
        budget = TakePictureBudget.from_config(TakePictureConfig())

    obs_layout = observation_layout or controller_observation_layout(
        feature_config=feature_config,
        secondary_camera_observation_line_n_bins=int(
            resolved.secondary_camera_observation_line_n_bins
        ),
        n_mission_targets=n_mission_targets,
    )

    def _episode_context() -> ControllerEpisodeContext | None:
        if not feature_config.needs_mission_scalars:
            return None
        remaining = float(budget.remaining) if budget is not None else 0.0
        captured = (
            frozenset(budget.captured_target_indices) if budget is not None else frozenset()
        )
        return ControllerEpisodeContext(
            capture_budget_remaining=remaining,
            target_anchor_xy_km=target_anchor_xy_km,
            captured_target_indices=captured,
        )

    overflight_policy = None
    if mode == "warmup":
        overflight_policy = _build_warmup_policy(
            setup,
            resolved,
            episode_idx=episode_idx,
            targets_per_episode=warmup_targets_per_episode,
        )

    resolver = ObcPointingResolver(tau_max_nm=tau_max_nm, sat_inertia=sat_inertia)
    resolver.reset_episode(theta_orbit_rad=float(ctrl0.theta_orbit_rad))

    current_ts = stepper.current_timestep_state()
    obs = build_controller_observation_from_timestep(
        timestep=current_ts,
        feature_config=feature_config,
        layout=obs_layout,
        episode_context=_episode_context(),
    )

    episode_return = 0.0
    steps = 0
    pilot_store_count = 0
    train_stride = max(1, int(train_every_n_steps))
    cmd_steps: list[int] = []
    selected_target_indices: list[int] = []
    episode_total_steps = int(stepper.total_steps)
    train_mode = mode in {"warmup", "train"}

    if show_config_panel:
        print_simulation_info(
            stepper,
            simulation_config=sim_config,
            tau_max_nm=tau_max_nm,
            agent=agent,
            episode_mode=mode,
            experiment_name=experiment_name or "ml_mpo_multienv_target_select",
            phase_episode_total=phase_episode_total,
        )

    metrics_start = snapshot_metrics_start(agent) if mode == "train" else None
    if progress_display is not None:
        progress_display.begin_episode(
            mode=mode,
            episode_idx=int(episode_idx),
            total_steps=episode_total_steps,
            agent=agent,
            metrics_start=metrics_start,
        )

    try:
        while not stepper.done and steps < episode_total_steps:
            take_picture_cmd = False
            stored_action = np.zeros(N_ACTION_DIMS, dtype=np.float32)
            wheel_nm = 0.0
            pointing_u = None

            if stepper.should_update_controller():
                state = stepper.current_timestep_state()
                sat_xy = np.asarray(state.sat_pos_xy_km, dtype=float)

                if mode == "warmup":
                    assert overflight_policy is not None
                    policy_action, _gym2, take_picture_cmd = baseline_overflight_controller_tick(
                        policy=overflight_policy,
                        stepper=stepper,
                        state=state,
                        sat_pos_xy_km=sat_xy,
                        omega_orbit_rad_s=omega_orbit_rad_s,
                        sat_inertia=sat_inertia,
                        tau_max_nm=tau_max_nm,
                        budget=budget,
                    )
                    active_idx = int(overflight_policy.active_target_index)
                    target_idx = min(max(active_idx, 0), N_TARGETS - 1)
                    stored_action = encode_warmup_action(
                        target_idx=target_idx,
                        move=str(overflight_policy.pointing_phase) == "engage",
                        shutter=bool(take_picture_cmd),
                    )
                    wheel_nm = float(policy_action.torque_request_nm)
                else:
                    stored_action = np.asarray(
                        agent.get_action(obs, train=train_mode),
                        dtype=np.float32,
                    ).reshape(-1)
                    target_idx = decode_target_idx(stored_action)
                    move = decode_move(stored_action)
                    take_picture_cmd = decode_shutter(stored_action)
                    selected_target_indices.append(target_idx)
                    anchor = target_anchor_xy_km[target_idx]
                    if move:
                        theta_target = float(
                            target_boresight_angle_rad(sat_xy, np.asarray(anchor, dtype=float))
                        )
                        pointing_u = float(
                            theta_target_to_u(
                                theta_target_rad=theta_target,
                                theta_orbit_rad=float(state.theta_orbit_rad),
                            )
                        )
                        wheel_nm = resolver.resolve_u_to_torque_nm(
                            u=pointing_u,
                            theta_orbit_rad=float(state.theta_orbit_rad),
                            sat_pos_xy_km=sat_xy,
                            body_z_rad=float(state.body_z_angle_rad),
                            omega_sat_rad_s=float(state.omega_sat_rad_s),
                            omega_orbit_rad_s=omega_orbit_rad_s,
                        )
                    else:
                        wheel_nm = 0.0
                        pointing_u = None

            next_ts = stepper.step(
                wheel_torque_cmd_nm=float(wheel_nm),
                agent_pointing_cmd_u=pointing_u,
            )
            cmd_step = int(stepper.current_index)
            if take_picture_cmd and budget is not None:
                stepper.apply_shutter_capture(cmd_step, budget)
                next_ts = stepper.current_timestep_state()
                cmd_steps.append(cmd_step)

            reward = float(next_ts.reward)
            done = bool(stepper.done)
            episode_return += reward

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

            next_obs = build_controller_observation_from_timestep(
                timestep=next_ts,
                feature_config=feature_config,
                layout=obs_layout,
                episode_context=_episode_context(),
            )

            if mode in {"warmup", "train"} and hasattr(agent, "store"):
                agent.store((obs, stored_action.copy(), reward, next_obs, done))
                pilot_store_count += 1
                if mode == "train" and (pilot_store_count % train_stride) == 0:
                    for _ in range(int(train_updates_per_step)):
                        if hasattr(agent, "train"):
                            agent.train()

            obs = next_obs
            steps += 1
            if done:
                break
    finally:
        if progress_display is not None:
            progress_display.end_episode()

    series = stepper.finalize_series()
    if mode == "warmup" and overflight_policy is not None and overflight_policy.cmd_steps:
        cmd_steps = list(overflight_policy.cmd_steps)
    mission_score = compute_episode_mission_score(series, tuple(cmd_steps))
    hold_last = int(resolver.diagnostics.hold_last_count)

    return Exp14EpisodeResult(
        episode_return=float(episode_return),
        steps=int(steps),
        simulation_series=series,
        cmd_steps=tuple(cmd_steps),
        mission_score=float(mission_score),
        configured_episode_steps=int(episode_total_steps),
        vector_hold_last_count=hold_last,
        selected_target_indices=tuple(selected_target_indices),
    )


__all__ = ["Exp14EpisodeResult", "run_exp14_episode"]
