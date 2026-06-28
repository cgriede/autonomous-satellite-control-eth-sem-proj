"""Fingerprinted pickle cache for notebook warmup episodes (full ``EpisodeResult``).

Persists ``SimulationStateSeries`` plus ``states`` so renders from ``RUN_DIR`` replay
canonical rollout without re-invoking ``run_episode``.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import pickle
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from environment_definition.constants import SIMULATION
from environment_definition.constants.SATELLITE import REACTION_WHEEL_MAX_TORQUE
from paths import MODELS_ROOT

from autonomous_control.config.randomness import derive_seed
from autonomous_control.feature_selection import ControllerFeatureConfig
from autonomous_control.reward import RewardConfig
from autonomous_control.training_runtime import EpisodeResult, run_episode

NB_WARMUP_BUNDLE_VERSION = 10
_EPISODES_FILENAME = "episodes.pkl.gz"
_META_FILENAME = "meta.json"


def default_notebook_warmup_bundle_root() -> Path:
    out = MODELS_ROOT / "cached_warmup" / "nb_bundle"
    out.mkdir(parents=True, exist_ok=True)
    return out


def satellite_altitude_m_to_float(satellite_altitude: Any) -> float:
    """Scalar satellite altitude in metres for fingerprinting (supports pint quantities)."""
    if hasattr(satellite_altitude, "to"):
        quant = satellite_altitude.to("meter")
        return float(getattr(quant, "magnitude", quant))
    return float(satellite_altitude)


def encode_feature_config_snapshot(
    feature_config: ControllerFeatureConfig | None,
) -> dict[str, Any]:
    cfg = feature_config if feature_config is not None else ControllerFeatureConfig()
    return {
        "attitude_keys": list(cfg.attitude_keys),
        "orbit_keys": list(cfg.orbit_keys),
        "vision_keys": list(cfg.vision_keys),
        "include_capture_budget": bool(cfg.include_capture_budget),
        "include_captured_target_mask": bool(cfg.include_captured_target_mask),
        "include_target_bearing_errors": bool(cfg.include_target_bearing_errors),
    }


def encode_reward_config_snapshot(
    reward_config: RewardConfig | None,
) -> dict[str, Any]:
    cfg = reward_config if reward_config is not None else RewardConfig()
    return {
        "enable_distance_reward": bool(cfg.enable_distance_reward),
        "enable_image_quality_capture": bool(cfg.enable_image_quality_capture),
        "enable_shutter_waste_penalty": bool(cfg.enable_shutter_waste_penalty),
        "enable_torque_effort": bool(cfg.enable_torque_effort),
        "k_shutter_waste": float(cfg.k_shutter_waste),
        "k_torque_effort": float(cfg.k_torque_effort),
        "shutter_waste_reward_epsilon": float(cfg.shutter_waste_reward_epsilon),
    }


def warmup_fingerprint_payload(
    *,
    obs_dim: int,
    action_dim: int,
    max_episode_steps: int,
    camera_observation_line_n_bins: int,
    satellite_altitude_m: float,
    base_seed: int,
    episode_count: int,
    warmup_controller: str,
    feature_config: ControllerFeatureConfig | None,
    reward_config: RewardConfig | None = None,
    early_stop_on_budget_exhausted: bool = False,
    n_mission_targets: int = 0,
    warmup_seed_tag: str = "nb_warmup",
    secondary_camera_observation_line_n_bins: int = 0,
    mission_profile: str = "generic",
    warmup_targets_per_episode: int = 0,
) -> dict[str, Any]:
    return {
        "base_seed": int(base_seed),
        "camera_observation_line_n_bins": int(camera_observation_line_n_bins),
        "episode_count": int(episode_count),
        "max_episode_steps": int(max_episode_steps),
        "nb_warmup_bundle_version": int(NB_WARMUP_BUNDLE_VERSION),
        "obs_dim": int(obs_dim),
        "action_dim": int(action_dim),
        "satellite_altitude_m": float(satellite_altitude_m),
        "feature_config": encode_feature_config_snapshot(feature_config),
        "reward_config": encode_reward_config_snapshot(reward_config),
        "warmup_controller": str(warmup_controller),
        "attitude_controller_enabled": True,
        "early_stop_on_budget_exhausted": bool(early_stop_on_budget_exhausted),
        "n_mission_targets": int(n_mission_targets),
        "warmup_seed_tag": str(warmup_seed_tag),
        "secondary_camera_observation_line_n_bins": int(
            secondary_camera_observation_line_n_bins
        ),
        "mission_profile": str(mission_profile),
        "warmup_targets_per_episode": int(warmup_targets_per_episode),
    }


def digest_for_warmup_fingerprint(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def bundle_dir_for_digest(digest_hex: str, *, cache_root: Path | None = None) -> Path:
    root = cache_root if cache_root is not None else default_notebook_warmup_bundle_root()
    return root / digest_hex


def reset_agent_replay_counters(agent: Any) -> None:
    """Clear replay rows and step accounting (used before hydrating from cache)."""
    buf = agent.buffer
    buf.ptr = 0
    buf.count = 0
    buf.scalars.fill(0.0)
    buf.next_scalars.fill(0.0)
    for arr in buf.vision.values():
        arr.fill(0)
    for arr in buf.next_vision.values():
        arr.fill(0)
    buf.actions.fill(0.0)
    buf.rewards.fill(0.0)
    buf.done.fill(0.0)
    agent.step_counter = 0
    agent.current_ep_return = 0.0
    agent.episode_returns = []


def preload_warmup_buffer_from_episodes(agent: Any, episodes: list[EpisodeResult]) -> int:
    """Replay cached transitions through ``agent.store`` (parity with ``run_episode`` warmups).

    Returns total transitions stored.
    """
    if hasattr(agent, "buffer") and hasattr(agent.buffer, "actions"):
        action_size = int(agent.buffer.actions.shape[1])
    else:
        action_size = int(getattr(agent, "action_size", 1))
    tau_max_nm = float(REACTION_WHEEL_MAX_TORQUE.to("N*m").magnitude)
    n_stored = 0
    for ep in episodes:
        series = ep.simulation_series
        n = ep.steps
        if len(series.t_s) != n + 1:
            raise ValueError(f"episode steps {n} inconsistent with series length {len(series.t_s)}.")
        if len(ep.states) != n + 1:
            raise ValueError(f"len(states) {len(ep.states)} != steps+1 {n + 1}.")
        interval = max(1, int(getattr(ep, "effective_controller_update_interval_steps", 1)))
        agent_cmds = np.asarray(
            series.wheel_torque_agent_cmd_nm if series.wheel_torque_agent_cmd_nm is not None else series.wheel_torque_cmd_nm,
            dtype=float,
        )
        shutter_steps = set(int(s) for s in (series.metadata.take_picture_cmd_steps or ()))
        for i in range(n):
            if i % interval != 0:
                continue
            obs = ep.states[i]
            next_obs = ep.states[i + 1]
            reward = float(series.simulation_reward[i + 1])
            step_k = i + 1
            torque_nm = float(agent_cmds[step_k])
            if action_size == 1:
                action = np.asarray([float(np.clip(torque_nm / tau_max_nm, -1.0, 1.0))], dtype=np.float32)
            elif action_size == 2:
                torque_norm = float(np.clip(torque_nm / tau_max_nm, -1.0, 1.0))
                shutter_gym = 1.0 if step_k in shutter_steps else -1.0
                action = np.asarray([torque_norm, shutter_gym], dtype=np.float32)
            else:
                raise ValueError(f"Unsupported action_size for warmup preload: {action_size}")
            done = i == n - 1
            agent.store((obs, action, reward, next_obs, done))
            n_stored += 1
    return n_stored


def _meta_path(bundle_dir: Path) -> Path:
    return bundle_dir / _META_FILENAME


def _episodes_path(bundle_dir: Path) -> Path:
    return bundle_dir / _EPISODES_FILENAME


def save_warmup_episode_bundle(
    bundle_dir: Path,
    *,
    digest_hex: str,
    fingerprint: dict[str, Any],
    episodes: list[EpisodeResult],
) -> None:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        **fingerprint,
        "digest_sha256_hex": digest_hex,
        "episode_count": len(episodes),
    }
    _meta_path(bundle_dir).write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with gzip.open(_episodes_path(bundle_dir), "wb") as gz:
        pickle.dump(episodes, gz, protocol=pickle.HIGHEST_PROTOCOL)


def try_load_warmup_episode_bundle(
    bundle_dir: Path,
    *,
    expected_fingerprint: dict[str, Any],
    expected_digest_hex: str,
    env: Any,
) -> list[EpisodeResult] | None:
    meta_fp = _meta_path(bundle_dir)
    ep_fp = _episodes_path(bundle_dir)
    if not meta_fp.exists() or not ep_fp.exists():
        return None
    try:
        meta_disk = json.loads(meta_fp.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    digest_disk = meta_disk.get("digest_sha256_hex")
    if digest_disk != expected_digest_hex or digest_disk != bundle_dir.name:
        return None
    for k, expected in expected_fingerprint.items():
        if meta_disk.get(k) != expected:
            return None
    if int(meta_disk.get("episode_count", -1)) != int(expected_fingerprint["episode_count"]):
        return None
    with gzip.open(ep_fp, "rb") as gz:
        episodes_obj: Any = pickle.load(gz)
    if not isinstance(episodes_obj, list):
        return None
    episodes = episodes_obj
    if len(episodes) != int(expected_fingerprint["episode_count"]):
        return None

    from autonomous_control.controller_observation import observation_matches_layout

    layout = getattr(env, "observation_layout", None)
    if layout is None:
        return None
    for ep in episodes:
        if not isinstance(ep, EpisodeResult):
            return None
        if ep.steps + 1 != len(ep.simulation_series.t_s):
            return None
        if ep.states and not observation_matches_layout(ep.states[0], layout):
            return None

    return episodes


def load_or_build_notebook_random_warmup_episodes(
    *,
    env: Any,
    agent: Any,
    base_seed: int,
    episode_count: int,
    satellite_altitude: Any,
    rebuild: bool = False,
    feature_config: ControllerFeatureConfig | None = None,
    reward_config: RewardConfig | None = None,
    warmup_controller: str = "baseline",
    seed_tag: str = "nb_warmup",
    train_updates_per_step: int = 0,
    warmup_baseline_period_s: float = 60.0,
    verbose_print: int = 0,
    cache_root: Path | None = None,
    show_progress: bool = False,
) -> list[EpisodeResult]:
    """Load cached ``EpisodeResult`` list or build it with the notebook seed convention.

    When ``seed_tag`` is ``\"nb_warmup\"``, episode ``i`` uses
    ``derive_seed(base_seed, \"nb_warmup\", i)`` (matches the notebook loop).
    """
    if episode_count <= 0:
        raise ValueError("episode_count must be > 0.")

    obs_dim = int(np.prod(env.observation_space.shape))
    action_dim = int(np.prod(env.action_space.shape))
    max_episode_steps = int(getattr(env, "max_episode_steps"))
    n_bins = int(SIMULATION.camera_observation_line_n_bins)
    alt_m = satellite_altitude_m_to_float(satellite_altitude)

    fingerprint = warmup_fingerprint_payload(
        obs_dim=obs_dim,
        action_dim=action_dim,
        max_episode_steps=max_episode_steps,
        camera_observation_line_n_bins=n_bins,
        satellite_altitude_m=alt_m,
        base_seed=int(base_seed),
        episode_count=int(episode_count),
        warmup_controller=warmup_controller,
        feature_config=feature_config,
        reward_config=reward_config,
    )
    digest = digest_for_warmup_fingerprint(fingerprint)
    bundle_dir = bundle_dir_for_digest(digest, cache_root=cache_root)

    if rebuild and bundle_dir.exists():
        shutil.rmtree(bundle_dir)

    if not rebuild:
        loaded = try_load_warmup_episode_bundle(
            bundle_dir,
            expected_fingerprint=fingerprint,
            expected_digest_hex=digest,
            env=env,
        )
        if loaded is not None:
            reset_agent_replay_counters(agent)
            preload_warmup_buffer_from_episodes(agent, loaded)
            return loaded

    bundle_dir.mkdir(parents=True, exist_ok=True)
    episodes_built: list[EpisodeResult] = []
    episode_indices = range(int(episode_count))
    if show_progress:
        from tqdm.auto import tqdm

        episode_indices = tqdm(episode_indices, desc="Warmup episodes")
    for i in episode_indices:
        rng = np.random.default_rng(derive_seed(int(base_seed), seed_tag, i))
        result = run_episode(
            env,
            agent,
            mode="warmup",
            train_updates_per_step=int(train_updates_per_step),
            warmup_controller=str(warmup_controller),
            warmup_baseline_period_s=float(warmup_baseline_period_s),
            feature_config=feature_config,
            satellite_altitude=satellite_altitude,
            np_rng=rng,
            verbose_print=int(verbose_print),
        )
        episodes_built.append(result)

    save_warmup_episode_bundle(
        bundle_dir,
        digest_hex=digest,
        fingerprint=fingerprint,
        episodes=episodes_built,
    )
    return episodes_built


__all__ = [
    "NB_WARMUP_BUNDLE_VERSION",
    "bundle_dir_for_digest",
    "default_notebook_warmup_bundle_root",
    "digest_for_warmup_fingerprint",
    "encode_feature_config_snapshot",
    "encode_reward_config_snapshot",
    "load_or_build_notebook_random_warmup_episodes",
    "preload_warmup_buffer_from_episodes",
    "reset_agent_replay_counters",
    "satellite_altitude_m_to_float",
    "save_warmup_episode_bundle",
    "try_load_warmup_episode_bundle",
    "warmup_fingerprint_payload",
]
