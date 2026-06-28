"""S01 MPO training workflow: preflight gate, warmup, train, eval on s01 mission."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from tqdm.auto import tqdm

from autonomous_control.config.randomness import RandomnessConfig, apply_global_seed, derive_seed
from autonomous_control.controller_agent import MPOAgent
from autonomous_control.controller_observation import (
    ControllerEpisodeContext,
    ControllerObservationLayout,
    build_controller_observation_from_timestep,
    controller_observation_layout,
    mission_scalar_values_from_context,
    resolve_target_anchor_xy_km,
)
from autonomous_control.feature_selection import (
    ControllerFeatureConfig,
    mission_scalar_key_names,
    select_controller_inputs_from_timestep,
)
from autonomous_control.episode_runner import EpisodeRunner
from autonomous_control.CNN_1d import cnn_vision_conv_stack
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.reward import RewardConfig
from autonomous_control.training_metrics import learning_stats_to_row
from autonomous_control.training_preflight import run_training_gate
from autonomous_control.training_progress_display import (
    TrainingProgressConfig,
    TrainingProgressDisplay,
)
from autonomous_control.notebook_warmup_bundle_cache import (
    bundle_dir_for_digest,
    digest_for_warmup_fingerprint,
    preload_warmup_buffer_from_episodes,
    reset_agent_replay_counters,
    save_warmup_episode_bundle,
    try_load_warmup_episode_bundle,
    warmup_fingerprint_payload,
)
from autonomous_control.training_runtime import EpisodeResult, make_attitude_control_env
from environment_definition.constants import RenderMode, SIMULATION
from environment_definition.constants.SATELLITE import REACTION_WHEEL_MAX_TORQUE
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.setup_types import EnvironmentSetup, ResolvedSimulationSetup, SimulationOverrides
from simulation.simulation_info import _reward_program_rows
from simulation.take_picture import TakePictureBudget, TakePictureConfig
from s01_utils.baseline_overflight import (
    BASELINE_N_TARGETS,
    build_baseline_overflight_setup,
    warmup_capture_targets,
)
from simulation.state_types import SimulationTimestepState
from utils.ml_training.ml_training_utils import (
    RunTelemetryWriter,
    append_run_markdown_event,
    checkpoint_path,
    create_run_dir,
    init_run_markdown,
)
from utils.ml_training.training_artifact_worker import (
    BackgroundArtifactWorker,
    run_artifacts_sync,
)
from utils.ml_training.training_run_artifacts import (
    artifact_paths_map,
    ensure_run_layout,
    episode_row_from_result,
    finalize_episodes_csv,
    write_config_snapshot,
    write_summary_metrics_json,
)


# Default controller observation features for notebook 08.
# Timestep keys (attitude/orbit/vision) plus mission scalars (budget + per-target bearing [rad]).
# Notebook 08 should use this constant (or dataclasses.replace on it) — do not duplicate a partial config.
S01_TRAINING_FEATURE_CONFIG = ControllerFeatureConfig(
    attitude_keys=(
        "body_z_angle_rad",
        "omega_sat_rad_s",
    ),
    orbit_keys=(
        "theta_orbit_rad",
        "primary_camera_image_quality",
    ),
    vision_keys=(
        "camera_observation_line_codes",
        "secondary_camera_observation_line_codes",
    ),
    include_capture_budget=True,
    include_captured_target_mask=True,
    include_target_bearing_errors=True,
)

_FEATURE_UNITS: dict[str, str] = {
    "body_z_angle_rad": "rad",
    "omega_sat_rad_s": "rad/s",
    "theta_orbit_rad": "rad",
    "primary_camera_image_quality": "1",
    "camera_observation_line_codes": "obs code / bin",
    "secondary_camera_observation_line_codes": "obs code / bin",
    "capture_budget_remaining": "count",
    "target_already_imaged": "1",
    "target_bearing_error_rad": "rad",
}

_OBS_CODE_LABELS: dict[int, str] = {
    -99: "not_computed",
    0: "space",
    1: "earth",
    2: "cloud",
    3: "target",
}


@dataclass(frozen=True)
class TrainingWorkflowConfig:
    """Notebook-08 training knobs.

    Warmup baseline uses strided target lists per episode (see ``warmup_capture_targets``).

    MPO update cadence (``EpisodeRunner.run_serial``, train mode only): replay ``store()``
    runs every controller tick; ``train_every_n_steps`` throttles ``agent.train()`` to every
    N-th controller store (not every simulation integration step). See
    ``docs/presentation/machine-learning.md``.
    """

    seed: int = 7
    warmup_episodes: int = 10
    train_episodes: int = 10
    eval_episodes: int = 2
    updates_per_step: int = 1  # MPO train() calls each time the learn gate opens
    train_every_n_steps: int = 1  # open learn gate every N controller stores (not sim steps)
    collect_states: bool = False
    run_id: str | None = None
    feature_config: ControllerFeatureConfig = S01_TRAINING_FEATURE_CONFIG
    background_artifacts: bool = True
    live_feed_interval_steps: int = 400
    warmup_live_feed_interval_steps: int = 1600
    early_stop_on_budget_exhausted: bool = False
    use_warmup_bundle_cache: bool = True
    rebuild_warmup_bundle_cache: bool = False
    warmup_targets_per_episode: int = 10


@dataclass
class TrainingWorkflowSetup:
    config: TrainingWorkflowConfig
    run_dir: Path
    mission_setup: EnvironmentSetup
    runner: EpisodeRunner
    agent: MPOAgent
    altitude_km: float
    feature_config: ControllerFeatureConfig
    secondary_camera_bins: int
    observation_layout: ControllerObservationLayout
    encoder_output_dim: int
    mpo_config: MPOConfig


@dataclass(frozen=True)
class PhaseKPIs:
    phase: str
    episodes: int
    return_mean: float
    return_std: float
    return_best: float
    best_episode_idx: int


@dataclass
class TrainingWorkflowResult:
    warmup_results: list[EpisodeResult]
    train_results: list[EpisodeResult]
    eval_results: list[EpisodeResult]
    checkpoint_path: Path
    train_kpis: PhaseKPIs
    eval_kpis: PhaseKPIs
    artifact_paths: dict[str, Path]
    artifact_errors: list[str]
    _artifact_worker: Any | None = None

    def wait_for_artifacts(self, timeout: float | None = None) -> list[str]:
        if self._artifact_worker is not None:
            errors = self._artifact_worker.shutdown(wait=True)
            self.artifact_errors.extend(errors)
            self._artifact_worker = None
            return list(self.artifact_errors)
        _ = timeout
        return list(self.artifact_errors)


@dataclass
class TrainingWorkflowContext:
    """Mutable cross-phase state for notebook-08 warmup → train → eval."""

    setup: TrainingWorkflowSetup
    show_progress: bool = True
    warmup_results: list[EpisodeResult] = field(default_factory=list)
    train_results: list[EpisodeResult] = field(default_factory=list)
    eval_results: list[EpisodeResult] = field(default_factory=list)
    episode_rows: list[dict[str, Any]] = field(default_factory=list)
    global_idx: int = 0
    artifact_errors: list[str] = field(default_factory=list)
    worker: BackgroundArtifactWorker | None = None
    progress_display: TrainingProgressDisplay | None = None
    telemetry_writer: RunTelemetryWriter | None = None
    paths: dict[str, Path] = field(default_factory=dict)
    checkpoint_path: Path | None = None
    _closed: bool = False

    @property
    def config(self) -> TrainingWorkflowConfig:
        return self.setup.config

    def close(self) -> None:
        if self._closed:
            return
        if self.worker is not None and self.config.background_artifacts:
            self.artifact_errors.extend(self.worker.shutdown(wait=False))
            self.worker = None
        if self.progress_display is not None:
            self.progress_display.close()
            self.progress_display = None
        self._closed = True


def _mpo_config_snapshot(mpo_config: MPOConfig) -> dict[str, object]:
    reward = mpo_config.reward
    return {
        "buffer_size": mpo_config.buffer_size,
        "batch_size": mpo_config.batch_size,
        "gamma": mpo_config.gamma,
        "tau": mpo_config.tau,
        "learning_rate_q": mpo_config.learning_rate_q,
        "learning_rate_pi": mpo_config.learning_rate_pi,
        "learning_rate_eta": mpo_config.learning_rate_eta,
        "target_kl_mu": mpo_config.target_kl_mu,
        "target_kl_sigma": mpo_config.target_kl_sigma,
        "num_samples_q": mpo_config.num_samples_q,
        "num_samples_pi": mpo_config.num_samples_pi,
        "warmup_episodes": mpo_config.warmup_episodes,
        "num_units_actor": mpo_config.num_units_actor,
        "num_units_critic": mpo_config.num_units_critic,
        "code_embed_dim": mpo_config.code_embed_dim,
        "cnn_embedding_dim": mpo_config.cnn_embedding_dim,
        "num_cnn_layers": mpo_config.num_cnn_layers,
        "reward": {
            "enable_distance_reward": reward.enable_distance_reward,
            "enable_image_quality_capture": reward.enable_image_quality_capture,
            "enable_shutter_waste_penalty": reward.enable_shutter_waste_penalty,
            "enable_torque_effort": reward.enable_torque_effort,
            "k_shutter_waste": reward.k_shutter_waste,
            "k_torque_effort": reward.k_torque_effort,
            "shutter_waste_reward_epsilon": reward.shutter_waste_reward_epsilon,
            "enable_outer_gate": reward.enable_outer_gate,
            "enable_energy": reward.enable_energy,
            "enable_cloud_penalty": reward.enable_cloud_penalty,
        },
    }


def _reward_config_flags(reward: RewardConfig) -> str:
    rows = _reward_program_rows(reward)
    return "; ".join(f"{label} ({value})" if value else label for label, value in rows)


def _episode_markdown_payload(result: EpisodeResult) -> dict[str, object]:
    payload: dict[str, object] = {
        "episode_return": f"{result.episode_return:.6f}",
        "steps": result.steps,
    }
    if result.ended_early_on_budget:
        payload["ended_early_on_budget"] = True
        payload["configured_episode_steps"] = result.configured_episode_steps
    if result.learning_stats is not None:
        stats = result.learning_stats
        payload.update(
            {
                "n_train_updates": stats.n_train_updates,
                "q_loss_mean": f"{stats.q_loss_mean:.6f}",
                "pi_loss_mean": f"{stats.pi_loss_mean:.6f}",
                "kl_mean": f"{stats.kl_mean:.6f}",
                "eta_mean": f"{stats.eta_mean:.6f}",
            }
        )
    return payload


def _train_postfix(result: EpisodeResult) -> dict[str, str]:
    postfix: dict[str, str] = {"reward": f"{result.episode_return:.1f}"}
    if result.learning_stats is not None and not np.isnan(result.learning_stats.kl_mean):
        postfix["kl"] = f"{result.learning_stats.kl_mean:.4f}"
    elif result.learning_stats is not None and not np.isnan(result.learning_stats.q_loss_mean):
        postfix["q_loss"] = f"{result.learning_stats.q_loss_mean:.2f}"
    return postfix


def run_s01_training_preflight_gate(
    *,
    feature_config: ControllerFeatureConfig | None = None,
    force: bool = False,
    use_cache: bool = True,
    integration_pytest: bool = False,
) -> bool:
    """Inline feature checks plus fast ML pytest subset (integration tests optional).

    Default notebook path: inline checks + fast pytest (~3s on cache miss). Set
    ``integration_pytest=True`` for full serial episode-runner tests (~80s), or
    ``force=True`` to ignore session/disk cache.

    Returns True when checks ran; False when a valid cache entry was reused.
    """
    return run_training_gate(
        feature_config=feature_config or S01_TRAINING_FEATURE_CONFIG,
        force=force,
        use_cache=use_cache,
        integration_pytest=integration_pytest,
    )


def _default_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    return f"nb-s01-08-{ts}"


def build_s01_training_mission_setup(*, seed: int) -> EnvironmentSetup:
    """Mission profile aligned with notebook 07 baseline overflight."""
    return build_baseline_overflight_setup(
        seed=derive_seed(seed, "mission_altitude"),
        cloud_seed=derive_seed(seed, "mission_clouds"),
        n_targets=BASELINE_N_TARGETS,
    )


def _estimate_episode_steps(resolved: ResolvedSimulationSetup) -> int:
    """Match SimulationStepper horizon from resolved orbit window."""
    r_earth_km = float(resolved.earth_radius.to(ureg.km).magnitude)
    alt_km = float(resolved.altitude.to(ureg.km).magnitude)
    mu_km3_s2 = float(
        resolved.earth_gravitational_parameter.to((ureg.km**3) / (ureg.s**2)).magnitude
    )
    r_orbit_km = r_earth_km + alt_km
    omega_rad_s = float(np.sqrt(mu_km3_s2 / (r_orbit_km**3)))
    render_span_rad = float(
        np.deg2rad(resolved.end_angle_deg - resolved.start_angle_deg)
    )
    sat_span_rad = render_span_rad * float(resolved.sat_motion_span_scale)
    sim_total_s = sat_span_rad / omega_rad_s
    dt_s = float(SIMULATION.simulation_timestep.to(ureg.s).magnitude)
    return max(2, int(np.ceil(sim_total_s / dt_s)) + 1)


def _feature_key_dims(
    key: str,
    *,
    secondary_camera_bins: int,
) -> int:
    if key == "camera_observation_line_codes":
        return int(SIMULATION.camera_observation_line_n_bins)
    if key == "secondary_camera_observation_line_codes":
        return int(secondary_camera_bins)
    return 1


def feature_config_registry_table(
    feature_config: ControllerFeatureConfig,
    *,
    secondary_camera_bins: int,
    n_mission_targets: int = 0,
) -> list[dict[str, object]]:
    """Rows describing each selected SimulationTimestepState key (edit point for features)."""
    rows: list[dict[str, object]] = []
    for group, keys in (
        ("attitude", feature_config.attitude_keys),
        ("orbit", feature_config.orbit_keys),
        ("vision", feature_config.vision_keys),
    ):
        for key in keys:
            width = _feature_key_dims(key, secondary_camera_bins=secondary_camera_bins)
            rows.append(
                {
                    "group": group,
                    "timestep_key": key,
                    "state_dims": width,
                    "unit": _FEATURE_UNITS.get(key, "—"),
                    "encoder_path": (
                        "scalar → MLP branch"
                        if width == 1
                        else "int8 codes → embed → 1D-CNN"
                    ),
                    "source_module": "autonomous_control/feature_selection.py",
                }
            )
    mission_keys = mission_scalar_key_names(
        n_targets=int(n_mission_targets),
        include_budget=feature_config.include_capture_budget,
        include_captured_mask=feature_config.include_captured_target_mask,
        include_bearings=feature_config.include_target_bearing_errors,
    )
    for key in mission_keys:
        unit = _FEATURE_UNITS.get(key, _FEATURE_UNITS.get("target_bearing_error_rad", "—"))
        if key.startswith("target_bearing_error_rad_"):
            unit = _FEATURE_UNITS["target_bearing_error_rad"]
        elif key.startswith("target_already_imaged_"):
            unit = _FEATURE_UNITS["target_already_imaged"]
        rows.append(
            {
                "group": "mission",
                "timestep_key": key,
                "state_dims": 1,
                "unit": unit,
                "encoder_path": "scalar → MLP branch",
                "source_module": "autonomous_control/controller_observation.py",
            }
        )
    return rows


def controller_encoder_routing_table(
    feature_config: ControllerFeatureConfig,
    *,
    secondary_camera_bins: int,
    mpo_config: MPOConfig | None = None,
    n_mission_targets: int = 0,
) -> list[dict[str, object]]:
    """Rows describing how each feature group reaches the actor/critic trunk."""
    cfg = mpo_config if mpo_config is not None else MPOConfig()
    scalar_width = int(cfg.num_units_actor)
    cnn_out = int(cfg.cnn_embedding_dim)
    rows: list[dict[str, object]] = []

    mission_keys = mission_scalar_key_names(
        n_targets=int(n_mission_targets),
        include_budget=feature_config.include_capture_budget,
        include_captured_mask=feature_config.include_captured_target_mask,
        include_bearings=feature_config.include_target_bearing_errors,
    )
    scalar_keys = feature_config.attitude_keys + feature_config.orbit_keys + mission_keys
    if scalar_keys:
        rows.append(
            {
                "stage": "scalar branch",
                "inputs": ", ".join(scalar_keys),
                "input_shape": f"({len(scalar_keys)},) float32",
                "module": f"MLP → {scalar_width}-D",
            }
        )

    vision_labels = {
        "camera_observation_line_codes": "primary (nadir)",
        "secondary_camera_observation_line_codes": "secondary (forward)",
    }
    _, kernel_sizes, _ = cnn_vision_conv_stack(int(cfg.num_cnn_layers))
    cnn_kernel = int(kernel_sizes[0])
    cnn_outputs: list[str] = []
    for key in feature_config.vision_keys:
        seq_len = _feature_key_dims(key, secondary_camera_bins=secondary_camera_bins)
        label = vision_labels.get(key, key)
        cnn_outputs.append(str(cnn_out))
        rows.append(
            {
                "stage": f"vision branch ({label})",
                "inputs": key,
                "input_shape": f"({seq_len},) int8",
                "module": (
                    f"ObservationLineCNNEncoder "
                    f"({cfg.num_cnn_layers}×Conv1d, k={cnn_kernel}) → {cnn_out}-D"
                ),
            }
        )

    if feature_config.vision_keys:
        vision_fusion_in = cnn_out * len(feature_config.vision_keys)
        rows.append(
            {
                "stage": "vision fusion",
                "inputs": "concat CNN embeddings",
                "input_shape": f"({vision_fusion_in},)",
                "module": f"MLP → {scalar_width}-D",
            }
        )

    trunk_dim = scalar_width + (scalar_width if feature_config.vision_keys else 0)
    rows.append(
        {
            "stage": "policy / Q trunk",
            "inputs": "concat(scalar, vision)",
            "input_shape": f"({trunk_dim},)",
            "module": "Actor head / Critic head",
        }
    )
    return rows


def observation_code_legend_table() -> list[dict[str, object]]:
    return [
        {"code": code, "label": label}
        for code, label in sorted(_OBS_CODE_LABELS.items())
    ]


def _episode_context_for_setup(
    setup: TrainingWorkflowSetup,
    *,
    budget_remaining: float | None = None,
) -> ControllerEpisodeContext | None:
    if not setup.feature_config.needs_mission_scalars:
        return None
    resolved = setup.mission_setup.resolve(require_camera=False)
    earth_radius_km = float(resolved.earth_radius.to(ureg.km).magnitude)
    anchors = resolve_target_anchor_xy_km(
        tuple(resolved.target_areas or ()),
        earth_radius_km=earth_radius_km,
    )
    if budget_remaining is None:
        budget_remaining = float(
            TakePictureBudget.from_config(TakePictureConfig()).remaining
        )
    return ControllerEpisodeContext(
        capture_budget_remaining=float(budget_remaining),
        target_anchor_xy_km=anchors,
    )


def _initial_timestep_for_setup(setup: TrainingWorkflowSetup) -> SimulationTimestepState:
    from environment_definition.constants.SIMULATION import training_episode_simulation_config
    from simulation.stepper_factory import build_stepper

    resolved = setup.mission_setup.resolve(require_camera=False)
    sim_config = training_episode_simulation_config()
    stepper = build_stepper(resolved, simulation_config=sim_config)
    return stepper.current_timestep_state()


def feature_scalar_snapshot_table(
    setup: TrainingWorkflowSetup,
    *,
    timestep: SimulationTimestepState | None = None,
) -> list[dict[str, object]]:
    """Scalar feature values at episode start (one row per scalar MLP input)."""
    ts = timestep if timestep is not None else _initial_timestep_for_setup(setup)
    selected = select_controller_inputs_from_timestep(
        timestep=ts,
        feature_config=setup.feature_config,
    )
    episode_context = _episode_context_for_setup(setup)
    mission_values: dict[str, float] = {}
    if episode_context is not None:
        mission_values = mission_scalar_values_from_context(
            timestep=ts,
            episode_context=episode_context,
            feature_config=setup.feature_config,
        )
    rows: list[dict[str, object]] = []
    scalar_index = 0
    for group, keys in (
        ("attitude", setup.feature_config.attitude_keys),
        ("orbit", setup.feature_config.orbit_keys),
    ):
        for key in keys:
            value = selected[key]
            rows.append(
                {
                    "scalar_index": scalar_index,
                    "group": group,
                    "timestep_key": key,
                    "value": float(value),
                    "unit": _FEATURE_UNITS.get(key, "—"),
                }
            )
            scalar_index += 1
    n_targets = len(setup.mission_setup.resolve(require_camera=False).target_areas or ())
    mission_keys = mission_scalar_key_names(
        n_targets=n_targets,
        include_budget=setup.feature_config.include_capture_budget,
        include_captured_mask=setup.feature_config.include_captured_target_mask,
        include_bearings=setup.feature_config.include_target_bearing_errors,
    )
    for key in mission_keys:
        unit = _FEATURE_UNITS["target_bearing_error_rad"]
        if key == "capture_budget_remaining":
            unit = _FEATURE_UNITS["capture_budget_remaining"]
        elif key.startswith("target_already_imaged_"):
            unit = _FEATURE_UNITS["target_already_imaged"]
        rows.append(
            {
                "scalar_index": scalar_index,
                "group": "mission",
                "timestep_key": key,
                "value": float(mission_values[key]),
                "unit": unit,
            }
        )
        scalar_index += 1
    return rows


def feature_vision_line_summary_table(
    setup: TrainingWorkflowSetup,
    *,
    timestep: SimulationTimestepState | None = None,
    preview_bins: int = 8,
) -> list[dict[str, object]]:
    """Per-camera line-code histogram plus first bins for vision features."""
    ts = timestep if timestep is not None else _initial_timestep_for_setup(setup)
    selected = select_controller_inputs_from_timestep(
        timestep=ts,
        feature_config=setup.feature_config,
    )
    rows: list[dict[str, object]] = []
    for camera_label, key in (
        ("primary (nadir)", "camera_observation_line_codes"),
        ("secondary (forward)", "secondary_camera_observation_line_codes"),
    ):
        if key not in selected:
            continue
        codes = np.asarray(selected[key], dtype=np.int8).reshape(-1)
        if codes.size == 0:
            rows.append(
                {
                    "camera": camera_label,
                    "timestep_key": key,
                    "n_bins": 0,
                    "preview": "—",
                    "dominant_code": "—",
                    "target_bins": 0,
                }
            )
            continue
        counts: dict[int, int] = {}
        for code in codes:
            counts[int(code)] = counts.get(int(code), 0) + 1
        dominant = max(counts, key=counts.get)
        preview_vals = ", ".join(str(int(v)) for v in codes[:preview_bins])
        rows.append(
            {
                "camera": camera_label,
                "timestep_key": key,
                "n_bins": int(codes.size),
                "preview": f"[{preview_vals}, …]",
                "dominant_code": f"{dominant} ({_OBS_CODE_LABELS.get(dominant, '?')})",
                "target_bins": int(np.sum(codes == 3)),
            }
        )
    return rows


def display_feature_tables(
    feature_config: ControllerFeatureConfig,
    *,
    secondary_camera_bins: int,
    mpo_config: MPOConfig | None = None,
    n_mission_targets: int = 0,
) -> None:
    """Notebook helper: feature selection and multimodal encoder routing."""
    import pandas as pd
    from IPython.display import Markdown, display

    from utils.notebook.display import display_notebook_dataframe

    layout = controller_observation_layout(
        feature_config=feature_config,
        secondary_camera_observation_line_n_bins=secondary_camera_bins,
        n_mission_targets=int(n_mission_targets),
    )
    cfg = mpo_config if mpo_config is not None else MPOConfig()
    display(Markdown("### Controller feature selection (`ControllerFeatureConfig`)"))
    display(
        Markdown(
            "Edit `S01_TRAINING_FEATURE_CONFIG` in `s01_utils/training_workflow.py` "
            "(timestep key tuples **and** `include_capture_budget` / "
            "`include_captured_target_mask` / "
            "`include_target_bearing_errors`). Notebook 08 should assign "
            "`FEATURE_CONFIG = tw.S01_TRAINING_FEATURE_CONFIG` rather than duplicating keys."
        )
    )
    display_notebook_dataframe(
        pd.DataFrame(
            feature_config_registry_table(
                feature_config,
                secondary_camera_bins=secondary_camera_bins,
                n_mission_targets=n_mission_targets,
            )
        )
    )
    display(
        Markdown(
            "### Controller encoder routing "
            f"(scalar **{layout.scalar_dim}**, "
            f"vision streams **{layout.num_vision_streams}**)"
        )
    )
    display_notebook_dataframe(
        pd.DataFrame(
            controller_encoder_routing_table(
                feature_config,
                secondary_camera_bins=secondary_camera_bins,
                mpo_config=cfg,
                n_mission_targets=n_mission_targets,
            )
        )
    )
    display(Markdown("### Observation code legend (vision line bins)"))
    display_notebook_dataframe(pd.DataFrame(observation_code_legend_table()))


def display_feature_snapshot_tables(setup: TrainingWorkflowSetup) -> None:
    """Notebook helper: scalar values + vision summaries at episode start."""
    import pandas as pd
    from IPython.display import Markdown, display

    from utils.notebook.display import display_notebook_dataframe

    ts = _initial_timestep_for_setup(setup)
    obs = build_controller_observation_from_timestep(
        timestep=ts,
        feature_config=setup.feature_config,
        layout=setup.observation_layout,
        episode_context=_episode_context_for_setup(setup),
    )
    vision_shapes = ", ".join(
        f"{key} {line.shape[0]} bins"
        for key, line in zip(setup.observation_layout.vision_keys, obs.vision)
    )
    display(Markdown("### Scalar features at episode start (MLP branch)"))
    display_notebook_dataframe(pd.DataFrame(feature_scalar_snapshot_table(setup, timestep=ts)))
    display(Markdown("### Vision line features at episode start (CNN branches)"))
    display_notebook_dataframe(pd.DataFrame(feature_vision_line_summary_table(setup, timestep=ts)))
    display(
        Markdown(
            f"Structured `ControllerObservation`: "
            f"scalars **{obs.scalars.shape[0]}**, "
            f"vision **{vision_shapes}** → encoder trunk **{setup.encoder_output_dim}**-D."
        )
    )


def build_training_workflow_setup(
    config: TrainingWorkflowConfig | None = None,
) -> TrainingWorkflowSetup:
    cfg = config if config is not None else TrainingWorkflowConfig()
    apply_global_seed(RandomnessConfig(seed=cfg.seed))
    capture_reward = RewardConfig(
        enable_distance_reward=False,
        enable_image_quality_capture=True,
        enable_shutter_waste_penalty=True,
        enable_torque_effort=True,
    )
    mission_setup = replace(
        build_s01_training_mission_setup(seed=cfg.seed),
        simulation_overrides=SimulationOverrides(reward_config=capture_reward),
    )
    resolved = mission_setup.resolve(require_camera=True)
    n_targets = len(resolved.target_areas or ())
    secondary_bins = int(resolved.secondary_camera_observation_line_n_bins)
    obs_layout = controller_observation_layout(
        feature_config=cfg.feature_config,
        secondary_camera_observation_line_n_bins=secondary_bins,
        n_mission_targets=n_targets,
    )
    max_episode_steps = _estimate_episode_steps(resolved)
    mpo_config = MPOConfig(
        warmup_episodes=cfg.warmup_episodes,
        max_target_index=n_targets - 1,
        max_steps_per_episode=max_episode_steps,
        reward=capture_reward,
    )
    env = make_attitude_control_env(
        secondary_camera_observation_line_n_bins=secondary_bins,
        reward_config=mpo_config.reward,
        feature_config=cfg.feature_config,
        n_mission_targets=n_targets,
        observation_layout=obs_layout,
    )
    agent = MPOAgent(env, config=mpo_config)
    encoder_output_dim = int(agent.pi.encoder.output_dim)
    run_id = cfg.run_id if cfg.run_id is not None else _default_run_id()
    run_dir = create_run_dir(run_id=run_id)
    ensure_run_layout(run_dir)
    paths = artifact_paths_map(run_dir)
    init_run_markdown(
        run_dir,
        title="S01 notebook 08 — MPO training",
        metadata={
            "seed": cfg.seed,
            "warmup_episodes": cfg.warmup_episodes,
            "train_episodes": cfg.train_episodes,
            "eval_episodes": cfg.eval_episodes,
            "scalar_dim": obs_layout.scalar_dim,
            "vision_keys": list(obs_layout.vision_keys),
            "vision_seq_lens": list(obs_layout.vision_seq_lens),
            "encoder_output_dim": encoder_output_dim,
            "code_embed_dim": mpo_config.code_embed_dim,
            "cnn_embedding_dim": mpo_config.cnn_embedding_dim,
            "num_cnn_layers": mpo_config.num_cnn_layers,
            "feature_attitude_keys": list(cfg.feature_config.attitude_keys),
            "feature_orbit_keys": list(cfg.feature_config.orbit_keys),
            "feature_vision_keys": list(cfg.feature_config.vision_keys),
            "sampled_altitude_km": float(resolved.altitude.to(ureg.km).magnitude),
            "created_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    write_config_snapshot(
        run_dir,
        {
            "workflow": {
                "seed": cfg.seed,
                "warmup_episodes": cfg.warmup_episodes,
                "train_episodes": cfg.train_episodes,
                "eval_episodes": cfg.eval_episodes,
                "updates_per_step": cfg.updates_per_step,
                "train_every_n_steps": cfg.train_every_n_steps,
                "collect_states": cfg.collect_states,
                "background_artifacts": cfg.background_artifacts,
                "early_stop_on_budget_exhausted": cfg.early_stop_on_budget_exhausted,
                "use_warmup_bundle_cache": cfg.use_warmup_bundle_cache,
                "rebuild_warmup_bundle_cache": cfg.rebuild_warmup_bundle_cache,
                "warmup_targets_per_episode": cfg.warmup_targets_per_episode,
            },
            "mpo": _mpo_config_snapshot(mpo_config),
            "features": {
                "attitude_keys": list(cfg.feature_config.attitude_keys),
                "orbit_keys": list(cfg.feature_config.orbit_keys),
                "vision_keys": list(cfg.feature_config.vision_keys),
                "include_capture_budget": cfg.feature_config.include_capture_budget,
                "include_captured_target_mask": cfg.feature_config.include_captured_target_mask,
                "include_target_bearing_errors": cfg.feature_config.include_target_bearing_errors,
            },
            "observation": {
                "scalar_dim": obs_layout.scalar_dim,
                "vision_keys": list(obs_layout.vision_keys),
                "vision_seq_lens": list(obs_layout.vision_seq_lens),
                "encoder_output_dim": encoder_output_dim,
            },
            "mission": {
                "sampled_altitude_km": float(resolved.altitude.to(ureg.km).magnitude),
                "cloud_count": len(resolved.clouds),
                "target_count": len(resolved.target_areas),
                "orbit_start_deg": float(resolved.start_angle_deg),
                "orbit_end_deg": float(resolved.end_angle_deg),
                "max_episode_steps": max_episode_steps,
                "profile": "baseline_overflight",
            },
            "artifact_paths": {k: str(v) for k, v in paths.items()},
        },
    )
    return TrainingWorkflowSetup(
        config=cfg,
        run_dir=run_dir,
        mission_setup=mission_setup,
        runner=EpisodeRunner(mission_setup),
        agent=agent,
        altitude_km=float(resolved.altitude.to(ureg.km).magnitude),
        feature_config=cfg.feature_config,
        secondary_camera_bins=secondary_bins,
        observation_layout=obs_layout,
        encoder_output_dim=encoder_output_dim,
        mpo_config=mpo_config,
    )


def print_training_setup_summary(setup: TrainingWorkflowSetup) -> None:
    cfg = setup.config
    resolved = setup.mission_setup.resolve(require_camera=True)
    print("S01 MPO training setup (notebook 07 baseline overflight profile)")
    print(f"  run_dir:           {setup.run_dir}")
    print(f"  seed:              {cfg.seed}")
    print(f"  altitude:          {setup.altitude_km:.1f} km")
    print(f"  targets:           {len(resolved.target_areas)}")
    print(f"  clouds:            {len(resolved.clouds)} (seeded over target corridor)")
    print(
        f"  orbit window:      {resolved.start_angle_deg:.1f}° .. "
        f"{resolved.end_angle_deg:.1f}°"
    )
    print(f"  episode steps:     {setup.mpo_config.max_steps_per_episode}")
    print(f"  attitude safety:   on (training_episode_simulation_config)")
    print(f"  scalar dim:        {setup.observation_layout.scalar_dim}")
    print(f"  vision streams:    {list(zip(setup.observation_layout.vision_keys, setup.observation_layout.vision_seq_lens))}")
    print(f"  encoder trunk:     {setup.encoder_output_dim}-D")
    print(f"  secondary bins:    {setup.secondary_camera_bins}")
    print(f"  feature keys:      {list(setup.feature_config.selected_keys)}")
    print(f"  warmup episodes:   {cfg.warmup_episodes}")
    print(f"  train episodes:    {cfg.train_episodes}")
    print(f"  eval episodes:     {cfg.eval_episodes}")
    mpo = setup.mpo_config
    print(f"  MPO batch_size:    {mpo.batch_size}")
    print(f"  MPO gamma:         {mpo.gamma}")
    print(f"  MPO LRs q/pi/eta:  {mpo.learning_rate_q}/{mpo.learning_rate_pi}/{mpo.learning_rate_eta}")
    print(f"  target_kl mu/sigma: {mpo.target_kl_mu}/{mpo.target_kl_sigma}")
    print(f"  reward program:    {_reward_config_flags(mpo.reward)}")
    print(f"  early stop:        {cfg.early_stop_on_budget_exhausted} (warmup/train; eval always full horizon)")
    print(f"  warmup cache:      {cfg.use_warmup_bundle_cache} (rebuild={cfg.rebuild_warmup_bundle_cache})")
    n_targets = len(setup.mission_setup.resolve(require_camera=True).target_areas or ())
    per = min(cfg.warmup_targets_per_episode, n_targets)
    stride = max(1, (n_targets + per - 1) // per)
    sample = warmup_capture_targets(0, n_targets=n_targets, targets_per_episode=cfg.warmup_targets_per_episode)
    print(
        f"  warmup targets/ep: {per} on {n_targets} "
        f"(ep0 start 0 then +{stride} each → {list(sample)})"
    )


def _episode_return(result: EpisodeResult) -> float:
    return float(result.episode_return)


def _summarize_phase(phase: str, results: list[EpisodeResult]) -> PhaseKPIs:
    totals = np.asarray([_episode_return(r) for r in results], dtype=np.float64)
    best_idx = int(np.argmax(totals)) if len(totals) else 0
    return PhaseKPIs(
        phase=phase,
        episodes=len(results),
        return_mean=float(np.mean(totals)) if len(totals) else 0.0,
        return_std=float(np.std(totals)) if len(totals) else 0.0,
        return_best=float(np.max(totals)) if len(totals) else 0.0,
        best_episode_idx=best_idx,
    )


def compute_action_diagnostics_from_episodes(
    episodes: list[EpisodeResult],
    *,
    phase: str,
    tau_max_nm: float | None = None,
    shutter_applied_epsilon: float = 1.0,
) -> dict[str, Any]:
    """Post-run action/reward diagnostics (required after first training run)."""
    if tau_max_nm is None:
        tau_max_nm = float(REACTION_WHEEL_MAX_TORQUE.to(ureg.N * ureg.m).magnitude)
    if not episodes:
        return {"phase": phase, "episodes": 0}

    torque_norms: list[float] = []
    shutter_rewards: list[float] = []
    shutter_omega_abs: list[float] = []
    n_shutter_cmds = 0
    n_shutter_meaningful = 0

    for ep in episodes:
        series = ep.simulation_series
        interval = max(1, int(ep.effective_controller_update_interval_steps))
        agent_cmds = np.asarray(
            series.wheel_torque_agent_cmd_nm
            if series.wheel_torque_agent_cmd_nm is not None
            else series.wheel_torque_cmd_nm,
            dtype=float,
        )
        dt_s = float(series.metadata.sim_dt_s)
        body_z = np.asarray(series.body_z_angle_rad, dtype=float)
        omega_est = np.diff(body_z) / dt_s if body_z.size > 1 and dt_s > 0.0 else np.zeros(0)

        for i in range(ep.steps):
            if i % interval != 0:
                continue
            step_k = i + 1
            if step_k >= agent_cmds.shape[0]:
                continue
            torque_norms.append(float(np.clip(agent_cmds[step_k] / tau_max_nm, -1.0, 1.0)))

        cmd_steps = tuple(series.metadata.take_picture_cmd_steps or ())
        for step_k in cmd_steps:
            if step_k < 0 or step_k >= series.simulation_reward.shape[0]:
                continue
            n_shutter_cmds += 1
            reward_k = float(series.simulation_reward[step_k])
            shutter_rewards.append(reward_k)
            if reward_k > float(shutter_applied_epsilon):
                n_shutter_meaningful += 1
            if omega_est.size > 0:
                idx = min(max(step_k - 1, 0), omega_est.size - 1)
                shutter_omega_abs.append(abs(float(omega_est[idx])))

    torque_arr = np.asarray(torque_norms, dtype=np.float64)
    return {
        "phase": phase,
        "episodes": len(episodes),
        "torque_norm_mean": float(np.mean(np.abs(torque_arr))) if torque_arr.size else 0.0,
        "torque_norm_std": float(np.std(torque_arr)) if torque_arr.size else 0.0,
        "torque_saturated_fraction": float(np.mean(np.abs(torque_arr) > 0.9))
        if torque_arr.size
        else 0.0,
        "shutter_cmd_count": int(n_shutter_cmds),
        "shutter_meaningful_fraction": (
            float(n_shutter_meaningful) / float(n_shutter_cmds) if n_shutter_cmds else 0.0
        ),
        "shutter_applied_epsilon": float(shutter_applied_epsilon),
        "mean_abs_omega_rad_s_at_shutter": float(np.mean(shutter_omega_abs))
        if shutter_omega_abs
        else 0.0,
    }


S01_WARMUP_SEED_TAG = "warmup_episode"
S01_WARMUP_MISSION_PROFILE = "s01_training"


def _warmup_capture_targets(
    setup: TrainingWorkflowSetup,
    warmup_episode_idx: int,
) -> tuple[int, ...]:
    n_targets = len(setup.mission_setup.resolve(require_camera=True).target_areas or ())
    return warmup_capture_targets(
        warmup_episode_idx,
        n_targets=n_targets,
        targets_per_episode=setup.config.warmup_targets_per_episode,
    )


def s01_training_warmup_fingerprint(
    setup: TrainingWorkflowSetup,
    *,
    episode_count: int,
) -> dict[str, Any]:
    """Fingerprint for S01 notebook-08 warmup bundles (mission + feature parity)."""
    layout = setup.observation_layout
    obs_dim = layout.scalar_dim + sum(layout.vision_seq_lens)
    resolved = setup.mission_setup.resolve(require_camera=True)
    alt_m = float(resolved.altitude.to(ureg.m).magnitude)
    n_targets = len(resolved.target_areas or ())
    return warmup_fingerprint_payload(
        obs_dim=obs_dim,
        action_dim=2,
        max_episode_steps=int(setup.mpo_config.max_steps_per_episode),
        camera_observation_line_n_bins=int(SIMULATION.camera_observation_line_n_bins),
        satellite_altitude_m=alt_m,
        base_seed=int(setup.config.seed),
        episode_count=int(episode_count),
        warmup_controller="baseline",
        feature_config=setup.feature_config,
        reward_config=setup.mpo_config.reward,
        early_stop_on_budget_exhausted=bool(setup.config.early_stop_on_budget_exhausted),
        n_mission_targets=n_targets,
        warmup_seed_tag=S01_WARMUP_SEED_TAG,
        secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
        mission_profile=S01_WARMUP_MISSION_PROFILE,
        warmup_targets_per_episode=int(setup.config.warmup_targets_per_episode),
    )


def _warmup_cache_env_adapter(setup: TrainingWorkflowSetup) -> Any:
    n_targets = len(setup.mission_setup.resolve(require_camera=True).target_areas or ())
    return make_attitude_control_env(
        feature_config=setup.feature_config,
        secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
        n_mission_targets=n_targets,
        observation_layout=setup.observation_layout,
    )


def load_or_build_s01_training_warmup_episodes(
    setup: TrainingWorkflowSetup,
    *,
    progress_display: TrainingProgressDisplay | None = None,
    show_progress: bool = True,
    episode_bar: Any | None = None,
) -> tuple[list[EpisodeResult], bool]:
    """Load cached S01 warmup episodes or build them with ``EpisodeRunner`` (collect_states=True).

    Returns ``(episodes, from_cache)``. When building, updates ``episode_bar`` per episode if given.
    """
    cfg = setup.config
    episode_count = int(cfg.warmup_episodes)
    if episode_count <= 0:
        return [], False

    fingerprint = s01_training_warmup_fingerprint(setup, episode_count=episode_count)
    digest = digest_for_warmup_fingerprint(fingerprint)
    bundle_dir = bundle_dir_for_digest(digest)
    env = _warmup_cache_env_adapter(setup)

    if cfg.rebuild_warmup_bundle_cache and bundle_dir.exists():
        shutil.rmtree(bundle_dir)

    if not cfg.rebuild_warmup_bundle_cache:
        loaded = try_load_warmup_episode_bundle(
            bundle_dir,
            expected_fingerprint=fingerprint,
            expected_digest_hex=digest,
            env=env,
        )
        if loaded is not None:
            reset_agent_replay_counters(setup.agent)
            n_trans = preload_warmup_buffer_from_episodes(setup.agent, loaded)
            if show_progress:
                tqdm.write(
                    f"Warmup cache hit: {len(loaded)} episodes, "
                    f"{n_trans} transitions ({bundle_dir.name[:12]}…)"
                )
            return loaded, True

    episodes_built: list[EpisodeResult] = []
    for warmup_idx in range(episode_count):
        capture_targets = _warmup_capture_targets(setup, warmup_idx)
        result = setup.runner.run_serial(
            setup.agent,
            feature_config=setup.feature_config,
            observation_layout=setup.observation_layout,
            mode="warmup",
            episode_idx=warmup_idx,
            show_config_panel=warmup_idx == 0,
            early_stop_on_budget_exhausted=cfg.early_stop_on_budget_exhausted,
            collect_states=True,
            progress_display=progress_display,
            train_every_n_steps=cfg.train_every_n_steps,
            warmup_capture_targets=capture_targets,
            np_rng=np.random.default_rng(
                derive_seed(cfg.seed, S01_WARMUP_SEED_TAG, warmup_idx)
            ),
        )
        episodes_built.append(result)
        if episode_bar is not None:
            episode_bar.update(1)

    save_warmup_episode_bundle(
        bundle_dir,
        digest_hex=digest,
        fingerprint=fingerprint,
        episodes=episodes_built,
    )
    if show_progress:
        tqdm.write(f"Warmup cache saved: {bundle_dir}")
    return episodes_built, False


def _save_checkpoint(agent: MPOAgent, path: Path) -> Path:
    payload = {
        "pi": agent.pi.state_dict(),
        "pi_target": agent.pi_target.state_dict(),
        "q1": agent.q1.state_dict(),
        "q2": agent.q2.state_dict(),
        "q1_target": agent.q1_target.state_dict(),
        "q2_target": agent.q2_target.state_dict(),
        "q_optimizer": agent.q_optimizer.state_dict(),
        "pi_optimizer": agent.pi_optimizer.state_dict(),
        "eta_optimizer": agent.eta_optimizer.state_dict(),
        "log_eta": float(agent.log_eta.detach().cpu().item()),
        "step_counter": agent.step_counter,
        "episode_returns": agent.episode_returns,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)
    return path


def open_training_workflow(
    setup: TrainingWorkflowSetup,
    *,
    show_progress: bool = True,
) -> TrainingWorkflowContext:
    """Start a training run session (telemetry, progress display, artifact worker)."""
    ctx = TrainingWorkflowContext(setup=setup, show_progress=show_progress)
    ctx.paths = artifact_paths_map(setup.run_dir)
    if setup.config.background_artifacts:
        ctx.worker = BackgroundArtifactWorker(setup.run_dir)
    ctx.telemetry_writer = RunTelemetryWriter(setup.run_dir)
    ctx.telemetry_writer.on_run_started(metadata={"workflow": "s01_notebook_08"})
    if show_progress:
        ctx.progress_display = TrainingProgressDisplay(
            config=TrainingProgressConfig(
                live_feed_interval_steps=setup.config.live_feed_interval_steps,
                telemetry_writer=ctx.telemetry_writer,
            ),
            agent=setup.agent,
        )
    return ctx


def _ctx_run_episode(ctx: TrainingWorkflowContext, **kwargs: Any) -> EpisodeResult:
    setup = ctx.setup
    cfg = ctx.config
    warmup_idx = kwargs.get("episode_idx", 0)
    if kwargs.get("mode") == "warmup" and "warmup_capture_targets" not in kwargs:
        kwargs = {
            **kwargs,
            "warmup_capture_targets": _warmup_capture_targets(setup, int(warmup_idx)),
        }
    return setup.runner.run_serial(
        setup.agent,
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        progress_display=ctx.progress_display,
        train_every_n_steps=cfg.train_every_n_steps,
        collect_states=cfg.collect_states,
        **kwargs,
    )


def _ctx_record_episode(
    ctx: TrainingWorkflowContext,
    *,
    phase: str,
    episode_idx: int,
    result: EpisodeResult,
    heading: str,
) -> None:
    learning_row = learning_stats_to_row(result.learning_stats)
    ctx.episode_rows.append(
        episode_row_from_result(
            global_idx=ctx.global_idx,
            phase=phase,
            episode_idx=episode_idx,
            episode_return=result.episode_return,
            steps=result.steps,
            learning_row=learning_row,
        )
    )
    append_run_markdown_event(
        ctx.setup.run_dir,
        heading=heading,
        payload=_episode_markdown_payload(result),
    )
    ctx.global_idx += 1


def run_warmup(ctx: TrainingWorkflowContext) -> list[EpisodeResult]:
    """Baseline overflight warmup episodes (fills replay buffer)."""
    setup = ctx.setup
    cfg = ctx.config
    if cfg.warmup_episodes <= 0:
        return ctx.warmup_results

    warmup_bar = tqdm(
        total=cfg.warmup_episodes,
        desc="Warmup",
        unit="ep",
        disable=not ctx.show_progress,
        position=0,
    )
    if ctx.progress_display is not None:
        ctx.progress_display.set_phase_bar(warmup_bar)
        ctx.progress_display.set_phase_episode_total(cfg.warmup_episodes)
        ctx.progress_display.set_live_feed_interval_steps(cfg.warmup_live_feed_interval_steps)
    try:
        if cfg.use_warmup_bundle_cache:
            cached_warmups, warmup_from_cache = load_or_build_s01_training_warmup_episodes(
                setup,
                progress_display=ctx.progress_display,
                show_progress=ctx.show_progress,
                episode_bar=warmup_bar,
            )
            for warmup_idx, result in enumerate(cached_warmups):
                ctx.warmup_results.append(result)
                _ctx_record_episode(
                    ctx,
                    phase="warmup",
                    episode_idx=warmup_idx,
                    result=result,
                    heading=f"Warmup episode {warmup_idx + 1} (baseline overflight)",
                )
                if warmup_from_cache:
                    warmup_bar.update(1)
        else:
            for warmup_idx in range(cfg.warmup_episodes):
                result = _ctx_run_episode(
                    ctx,
                    mode="warmup",
                    episode_idx=warmup_idx,
                    show_config_panel=warmup_idx == 0,
                    early_stop_on_budget_exhausted=cfg.early_stop_on_budget_exhausted,
                    np_rng=np.random.default_rng(
                        derive_seed(cfg.seed, S01_WARMUP_SEED_TAG, warmup_idx)
                    ),
                )
                ctx.warmup_results.append(result)
                _ctx_record_episode(
                    ctx,
                    phase="warmup",
                    episode_idx=warmup_idx,
                    result=result,
                    heading=f"Warmup episode {warmup_idx + 1} (baseline overflight)",
                )
                warmup_bar.update(1)
    finally:
        warmup_bar.close()
    if ctx.progress_display is not None and ctx.warmup_results:
        ctx.progress_display.show_warmup_summary(ctx.warmup_results)
    return ctx.warmup_results


def run_training(ctx: TrainingWorkflowContext) -> list[EpisodeResult]:
    """Policy training episodes + checkpoint save."""
    cfg = ctx.config
    train_bar = tqdm(
        total=cfg.train_episodes,
        desc="Train",
        unit="ep",
        disable=not ctx.show_progress,
        position=0,
    )
    if ctx.progress_display is not None:
        ctx.progress_display.set_phase_bar(train_bar)
        ctx.progress_display.set_phase_episode_total(cfg.train_episodes)
        ctx.progress_display.set_live_feed_interval_steps(cfg.live_feed_interval_steps)
    try:
        for ep in range(cfg.train_episodes):
            result = _ctx_run_episode(
                ctx,
                mode="train",
                train_updates_per_step=cfg.updates_per_step,
                episode_idx=ep,
                show_config_panel=ep == 0,
                early_stop_on_budget_exhausted=cfg.early_stop_on_budget_exhausted,
                np_rng=np.random.default_rng(derive_seed(cfg.seed, "train_episode", ep)),
            )
            ctx.train_results.append(result)
            _ctx_record_episode(
                ctx,
                phase="train",
                episode_idx=ep,
                result=result,
                heading=f"Train episode {ep + 1}",
            )
            train_bar.set_postfix(**_train_postfix(result))
            train_bar.update(1)
    finally:
        train_bar.close()

    ctx.checkpoint_path = _save_checkpoint(ctx.setup.agent, checkpoint_path(ctx.setup.run_dir))
    return ctx.train_results


def run_eval(ctx: TrainingWorkflowContext) -> TrainingWorkflowResult:
    """Eval episodes, finalize CSV/metrics, export plots/video."""
    cfg = ctx.config
    eval_bar = tqdm(
        total=cfg.eval_episodes,
        desc="Eval",
        unit="ep",
        disable=not ctx.show_progress,
        position=0,
    )
    if ctx.progress_display is not None:
        ctx.progress_display.set_phase_bar(eval_bar)
        ctx.progress_display.set_phase_episode_total(cfg.eval_episodes)
        ctx.progress_display.set_live_feed_interval_steps(cfg.live_feed_interval_steps)
    try:
        for ep in range(cfg.eval_episodes):
            result = _ctx_run_episode(
                ctx,
                mode="eval",
                train_updates_per_step=0,
                episode_idx=ep,
                show_config_panel=ep == 0,
                early_stop_on_budget_exhausted=False,
                np_rng=np.random.default_rng(derive_seed(cfg.seed, "eval_episode", ep)),
            )
            ctx.eval_results.append(result)
            _ctx_record_episode(
                ctx,
                phase="eval",
                episode_idx=ep,
                result=result,
                heading=f"Eval episode {ep + 1}",
            )
            eval_bar.set_postfix(reward=f"{result.episode_return:.1f}")
            eval_bar.update(1)
    finally:
        eval_bar.close()

    finalize_episodes_csv(ctx.setup.run_dir, ctx.episode_rows)
    action_diagnostics = {
        "train": compute_action_diagnostics_from_episodes(ctx.train_results, phase="train"),
        "eval": compute_action_diagnostics_from_episodes(ctx.eval_results, phase="eval"),
    }
    write_summary_metrics_json(
        ctx.setup.run_dir,
        ctx.episode_rows,
        action_diagnostics=action_diagnostics,
    )

    last_train_result = ctx.train_results[-1] if ctx.train_results else None
    reward_jobs: list[tuple[Any, str, Path]] = []
    video_jobs: list[tuple[Any, Path]] = []
    if last_train_result is not None:
        reward_jobs.append(
            (
                last_train_result.simulation_series,
                "train last",
                ctx.paths["train_last_reward_plot"],
            )
        )
    if ctx.eval_results:
        best_eval_idx = int(
            max(range(len(ctx.eval_results)), key=lambda i: _episode_return(ctx.eval_results[i]))
        )
        best_eval = ctx.eval_results[best_eval_idx]
        reward_jobs.append(
            (
                best_eval.simulation_series,
                f"eval best (ep {best_eval_idx + 1})",
                ctx.paths["eval_best_reward_plot"],
            )
        )
        video_jobs.append((best_eval.simulation_series, ctx.paths["eval_best_video"]))

    if cfg.background_artifacts and ctx.worker is not None:
        for series, label, out_path in reward_jobs:
            ctx.worker.submit_reward_plot(series, label=label, out_path=out_path)
        for series, out_path in video_jobs:
            ctx.worker.submit_video_export(series, out_path)
        ctx.worker.submit_run_plots(ctx.episode_rows)
    else:
        ctx.artifact_errors.extend(
            run_artifacts_sync(
                reward_jobs=reward_jobs,
                video_jobs=video_jobs,
                run_dir=ctx.setup.run_dir,
                episode_rows=ctx.episode_rows,
            )
        )

    worker = ctx.worker
    if worker is not None:
        ctx.artifact_errors.extend(worker.shutdown(wait=True))
        ctx.worker = None

    result = TrainingWorkflowResult(
        warmup_results=ctx.warmup_results,
        train_results=ctx.train_results,
        eval_results=ctx.eval_results,
        checkpoint_path=ctx.checkpoint_path or checkpoint_path(ctx.setup.run_dir),
        train_kpis=_summarize_phase("train", ctx.train_results),
        eval_kpis=_summarize_phase("eval", ctx.eval_results),
        artifact_paths=ctx.paths,
        artifact_errors=list(ctx.artifact_errors),
        _artifact_worker=None,
    )
    ctx.close()
    return result


def run_training_workflow(
    setup: TrainingWorkflowSetup,
    *,
    show_progress: bool = True,
) -> TrainingWorkflowResult:
    ctx = open_training_workflow(setup, show_progress=show_progress)
    try:
        run_warmup(ctx)
        run_training(ctx)
        return run_eval(ctx)
    except Exception:
        if ctx.worker is not None and ctx.config.background_artifacts:
            ctx.worker.shutdown(wait=False)
        raise
    finally:
        ctx.close()


def print_training_kpis(result: TrainingWorkflowResult) -> None:
    print("Training KPIs")
    print(f"  checkpoint:        {result.checkpoint_path}")
    print(f"  run_dir:           {result.artifact_paths['config'].parent}")
    for kpis in (result.train_kpis, result.eval_kpis):
        print(f"  {kpis.phase}:")
        print(f"    episodes:        {kpis.episodes}")
        print(f"    mean return:     {kpis.return_mean:.2f} ± {kpis.return_std:.2f}")
        print(f"    best return:     {kpis.return_best:.2f} (ep {kpis.best_episode_idx + 1})")
    early_stop_episodes = [
        (phase, idx + 1, ep.steps, ep.configured_episode_steps)
        for phase, episodes in (
            ("warmup", result.warmup_results),
            ("train", result.train_results),
        )
        for idx, ep in enumerate(episodes)
        if ep.ended_early_on_budget
    ]
    if early_stop_episodes:
        print("  early-stop warnings (capture budget exhausted):")
        for phase, ep_no, steps, configured in early_stop_episodes:
            print(f"    {phase} ep {ep_no}: {steps}/{configured} steps")
    if result.artifact_errors:
        print(f"  artifact errors:   {len(result.artifact_errors)}")
    diag_path = result.artifact_paths["config"].parent / "summary_metrics.json"
    if diag_path.exists():
        import json

        summary = json.loads(diag_path.read_text(encoding="utf-8"))
        diag = summary.get("action_diagnostics", {})
        train_diag = diag.get("train", {})
        if train_diag:
            print("  action diagnostics (train):")
            print(
                f"    torque |norm| mean/std: "
                f"{train_diag.get('torque_norm_mean', 0):.3f} / "
                f"{train_diag.get('torque_norm_std', 0):.3f}"
            )
            print(
                f"    torque saturated (>0.9): "
                f"{100.0 * float(train_diag.get('torque_saturated_fraction', 0)):.1f}%"
            )
            print(
                f"    shutters meaningful (reward > ε): "
                f"{100.0 * float(train_diag.get('shutter_meaningful_fraction', 0)):.1f}% "
                f"({train_diag.get('shutter_cmd_count', 0)} cmds)"
            )
            print(
                f"    mean |ω| at shutter [rad/s]: "
                f"{float(train_diag.get('mean_abs_omega_rad_s_at_shutter', 0)):.4f}"
            )


def display_training_artifacts(result: TrainingWorkflowResult) -> None:
    """Notebook helper: wait for background exports and display key plots."""
    from IPython.display import Image, Markdown, display

    result.wait_for_artifacts()
    display(Markdown("### Training artifacts"))
    for key in (
        "returns_plot",
        "learning_curves_plot",
        "train_last_reward_plot",
        "eval_best_reward_plot",
    ):
        path = result.artifact_paths.get(key)
        if path is not None and path.exists():
            display(Markdown(f"**{key}** — `{path}`"))
            display(Image(filename=str(path)))
    video = result.artifact_paths.get("eval_best_video")
    if video is not None and video.exists():
        display(Markdown(f"**eval_best_video** — `{video}`"))
    if result.artifact_errors:
        display(Markdown("**Artifact warnings:**\n" + "\n".join(f"- {e}" for e in result.artifact_errors)))


def export_training_episode_video(
    result: EpisodeResult,
    out_path: Path,
) -> Path:
    from utils.ml_training.training_run_artifacts import export_training_episode_video_sync

    return export_training_episode_video_sync(result.simulation_series, out_path)
