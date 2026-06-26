"""Structured controller observations: scalar features + vision code lines."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import torch

from environment_definition.constants import SIMULATION
from simulation.attitude_controller import target_boresight_angle_rad
from utils.geometry.mission_stripe_disk import target_areas_midpoint_disk_xy_km_on_sphere

from .feature_selection import (
    VISION_OBSERVATION_LINE_KEYS,
    ControllerFeatureConfig,
    mission_scalar_key_names,
    select_controller_inputs_from_timestep,
)

if TYPE_CHECKING:
    from simulation.state_types import SimulationTimestepState


def _wrap_pi(angle_rad: float) -> float:
    return float(((angle_rad + math.pi) % (2.0 * math.pi)) - math.pi)


@dataclass(frozen=True)
class ControllerEpisodeContext:
    """Per-episode values not stored on ``SimulationTimestepState``."""

    capture_budget_remaining: float
    target_anchor_xy_km: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "target_anchor_xy_km",
            np.asarray(self.target_anchor_xy_km, dtype=np.float64).reshape(-1, 2),
        )


def resolve_target_anchor_xy_km(
    target_areas: tuple[Any, ...],
    *,
    earth_radius_km: float,
) -> np.ndarray:
    """Disk (x, z) anchor [km] per mission target area."""
    if not target_areas:
        return np.zeros((0, 2), dtype=np.float64)
    rows: list[np.ndarray] = []
    for area in target_areas:
        xy = target_areas_midpoint_disk_xy_km_on_sphere(
            (area,),
            earth_radius_km=float(earth_radius_km),
        )
        rows.append(np.asarray(xy, dtype=np.float64).reshape(2))
    anchors = np.stack(rows, axis=0)
    # #region agent log
    try:
        import json
        import time
        from pathlib import Path

        _log = (
            Path(__file__).resolve().parents[2]
            / "debug-0e4792.log"
        )
        _log.open("a", encoding="utf-8").write(
            json.dumps(
                {
                    "sessionId": "0e4792",
                    "hypothesisId": "A",
                    "location": "controller_observation.py:resolve_target_anchor_xy_km",
                    "message": "per-target anchors resolved",
                    "data": {
                        "n_target_areas": len(target_areas),
                        "anchors_shape": list(anchors.shape),
                    },
                    "timestamp": int(time.time() * 1000),
                    "runId": "post-fix",
                }
            )
            + "\n"
        )
    except Exception:
        pass
    # #endregion
    return anchors


def compute_target_bearing_errors_rad(
    *,
    sat_pos_xy_km: np.ndarray,
    body_z_angle_rad: float,
    target_anchor_xy_km: np.ndarray,
) -> np.ndarray:
    """Signed bearing error per target [rad]: boresight angle minus body +Z."""
    sat = np.asarray(sat_pos_xy_km, dtype=float).reshape(2)
    anchors = np.asarray(target_anchor_xy_km, dtype=float).reshape(-1, 2)
    if anchors.shape[0] == 0:
        return np.zeros((0,), dtype=np.float64)
    errors = np.empty(anchors.shape[0], dtype=np.float64)
    for i, anchor in enumerate(anchors):
        theta_target = target_boresight_angle_rad(sat, anchor)
        errors[i] = _wrap_pi(theta_target - float(body_z_angle_rad))
    return errors


def mission_scalar_values_from_context(
    *,
    timestep: "SimulationTimestepState",
    episode_context: ControllerEpisodeContext,
    feature_config: ControllerFeatureConfig,
) -> dict[str, float]:
    """Mission scalars keyed like ``mission_scalar_key_names``."""
    cfg = feature_config
    values: dict[str, float] = {}
    if cfg.include_capture_budget:
        values["capture_budget_remaining"] = float(episode_context.capture_budget_remaining)
    if cfg.include_target_bearing_errors:
        errors = compute_target_bearing_errors_rad(
            sat_pos_xy_km=timestep.sat_pos_xy_km,
            body_z_angle_rad=float(timestep.body_z_angle_rad),
            target_anchor_xy_km=episode_context.target_anchor_xy_km,
        )
        for i, err in enumerate(errors):
            values[f"target_bearing_error_rad_{i}"] = float(err)
    return values


@dataclass(frozen=True)
class ControllerObservationLayout:
    """Fixed observation structure for one controller feature configuration."""

    scalar_keys: tuple[str, ...]
    vision_keys: tuple[str, ...]
    vision_seq_lens: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.vision_keys) != len(self.vision_seq_lens):
            raise ValueError("vision_keys and vision_seq_lens must have equal length.")

    @property
    def scalar_dim(self) -> int:
        return len(self.scalar_keys)

    @property
    def num_vision_streams(self) -> int:
        return len(self.vision_keys)

    def vision_cache_key(self, key: str) -> str:
        return f"vision_{key}"


@dataclass(frozen=True)
class ControllerObservation:
    """One controller timestep: scalars plus ordered int8 vision lines."""

    scalars: np.ndarray
    vision: tuple[np.ndarray, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scalars", np.asarray(self.scalars, dtype=np.float32).reshape(-1))
        object.__setattr__(
            self,
            "vision",
            tuple(np.asarray(line, dtype=np.int8).reshape(-1) for line in self.vision),
        )

    def copy(self) -> ControllerObservation:
        return ControllerObservation(
            scalars=self.scalars.copy(),
            vision=tuple(line.copy() for line in self.vision),
        )


def controller_observation_layout(
    feature_config: ControllerFeatureConfig | None = None,
    *,
    secondary_camera_observation_line_n_bins: int = 0,
    n_mission_targets: int = 0,
) -> ControllerObservationLayout:
    cfg = feature_config if feature_config is not None else ControllerFeatureConfig()
    if cfg.needs_mission_scalars and n_mission_targets < 0:
        raise ValueError("n_mission_targets must be >= 0 when mission scalars are enabled.")
    mission_keys = mission_scalar_key_names(
        n_targets=int(n_mission_targets),
        include_budget=cfg.include_capture_budget,
        include_bearings=cfg.include_target_bearing_errors,
    )
    scalar_keys = cfg.attitude_keys + cfg.orbit_keys + mission_keys
    vision_keys: list[str] = []
    vision_seq_lens: list[int] = []
    for key in cfg.vision_keys:
        if key not in VISION_OBSERVATION_LINE_KEYS:
            raise ValueError(f"Unsupported vision key for CNN encoder: {key!r}.")
        vision_keys.append(key)
        if key == "camera_observation_line_codes":
            vision_seq_lens.append(int(SIMULATION.camera_observation_line_n_bins))
        elif key == "secondary_camera_observation_line_codes":
            vision_seq_lens.append(int(secondary_camera_observation_line_n_bins))
    return ControllerObservationLayout(
        scalar_keys=tuple(scalar_keys),
        vision_keys=tuple(vision_keys),
        vision_seq_lens=tuple(vision_seq_lens),
    )


def build_controller_observation_from_timestep(
    *,
    timestep: "SimulationTimestepState",
    feature_config: ControllerFeatureConfig | None = None,
    layout: ControllerObservationLayout | None = None,
    secondary_camera_observation_line_n_bins: int = 0,
    episode_context: ControllerEpisodeContext | None = None,
    n_mission_targets: int = 0,
) -> ControllerObservation:
    """Build structured observation from one simulation timestep."""
    cfg = feature_config if feature_config is not None else ControllerFeatureConfig()
    if layout is None:
        layout = controller_observation_layout(
            feature_config=cfg,
            secondary_camera_observation_line_n_bins=secondary_camera_observation_line_n_bins,
            n_mission_targets=n_mission_targets,
        )
    if cfg.needs_mission_scalars and episode_context is None:
        raise ValueError(
            "episode_context is required when mission scalar features are enabled."
        )
    selected = select_controller_inputs_from_timestep(
        timestep=timestep,
        feature_config=cfg,
    )
    mission_values: dict[str, float] = {}
    if cfg.needs_mission_scalars:
        assert episode_context is not None
        mission_values = mission_scalar_values_from_context(
            timestep=timestep,
            episode_context=episode_context,
            feature_config=cfg,
        )
    scalars: list[float] = []
    for key in layout.scalar_keys:
        if key in mission_values:
            scalars.append(float(mission_values[key]))
            continue
        if key not in selected:
            # #region agent log
            try:
                import json
                import time
                from pathlib import Path

                _log = Path(__file__).resolve().parents[2] / "debug-0e4792.log"
                _log.open("a", encoding="utf-8").write(
                    json.dumps(
                        {
                            "sessionId": "0e4792",
                            "hypothesisId": "C",
                            "location": "controller_observation.py:build_controller_observation_from_timestep",
                            "message": "scalar key missing from timestep and mission_values",
                            "data": {
                                "key": key,
                                "mission_value_keys": sorted(mission_values.keys())[:6],
                                "n_mission_values": len(mission_values),
                                "n_scalar_keys": len(layout.scalar_keys),
                            },
                            "timestamp": int(time.time() * 1000),
                        }
                    )
                    + "\n"
                )
            except Exception:
                pass
            # #endregion
            raise KeyError(
                f"Scalar feature '{key}' is not on SimulationTimestepState "
                "and was not computed as a mission scalar."
            )
        value = selected[key]
        if isinstance(value, (bool, int, float, np.generic)):
            scalars.append(float(value))
            continue
        raise TypeError(f"Scalar feature '{key}' must be numeric, got {type(value).__name__}.")
    vision_lines: list[np.ndarray] = []
    for key in layout.vision_keys:
        value = selected[key]
        vision_lines.append(np.asarray(value, dtype=np.int8).reshape(-1))
    return ControllerObservation(
        scalars=np.asarray(scalars, dtype=np.float32),
        vision=tuple(vision_lines),
    )


def controller_observation_to_tensors(
    obs: ControllerObservation,
    *,
    device: torch.device,
) -> tuple[torch.Tensor, tuple[torch.Tensor, ...]]:
    scalars = torch.as_tensor(obs.scalars, dtype=torch.float32, device=device)
    vision = tuple(
        torch.as_tensor(line, dtype=torch.int8, device=device).unsqueeze(0)
        for line in obs.vision
    )
    return scalars, vision


def controller_observation_batch_to_tensors(
    observations: list[ControllerObservation],
    *,
    device: torch.device,
) -> tuple[torch.Tensor, tuple[torch.Tensor, ...]]:
    if not observations:
        raise ValueError("observations must be non-empty.")
    scalars = torch.as_tensor(
        np.stack([obs.scalars for obs in observations], axis=0),
        dtype=torch.float32,
        device=device,
    )
    num_streams = len(observations[0].vision)
    vision = tuple(
        torch.as_tensor(
            np.stack([obs.vision[i] for obs in observations], axis=0),
            dtype=torch.int8,
            device=device,
        )
        for i in range(num_streams)
    )
    return scalars, vision


def observation_matches_layout(
    obs: Any,
    layout: ControllerObservationLayout,
) -> bool:
    if not isinstance(obs, ControllerObservation):
        return False
    if obs.scalars.shape != (layout.scalar_dim,):
        return False
    if len(obs.vision) != layout.num_vision_streams:
        return False
    for line, expected_len in zip(obs.vision, layout.vision_seq_lens):
        if line.shape != (expected_len,):
            return False
    return True


__all__ = [
    "ControllerEpisodeContext",
    "ControllerObservation",
    "ControllerObservationLayout",
    "build_controller_observation_from_timestep",
    "compute_target_bearing_errors_rad",
    "controller_observation_batch_to_tensors",
    "controller_observation_layout",
    "controller_observation_to_tensors",
    "mission_scalar_values_from_context",
    "observation_matches_layout",
    "resolve_target_anchor_xy_km",
]
