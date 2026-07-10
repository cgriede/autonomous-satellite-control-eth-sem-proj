"""Conversion verification checks A–G for Exp 14 action/actuator wiring."""

from __future__ import annotations

import sys
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import numpy as np
import torch

from autonomous_control.controller_observation import controller_observation_layout
from simulation.attitude_controller import target_boresight_angle_rad
from simulation.obc_pointing_request import theta_target_to_u

from _action_constants import (
    GYM_FALSE,
    GYM_TRUE,
    MOVE_IDX,
    SHUTTER_IDX,
    decode_move,
    decode_shutter,
    decode_target_idx,
    encode_applied_action,
    encode_warmup_action,
)
from _env_setup_fork import build_exp14_env_setup_fixed
from _mission_score import compute_episode_mission_score
from _profile_baseline import FEATURE_CONFIG

from s01_utils.baseline_overflight import run_baseline_overflight_rollout


class VerifyError(AssertionError):
    pass


def run_verify_checks() -> dict[str, bool]:
    checks: dict[str, bool] = {}

    sampled_idx = 23
    move_z = 0.88
    shutter_z = -0.5
    move_gym = float(torch.tanh(torch.tensor(move_z)))
    shutter_gym = float(torch.tanh(torch.tensor(shutter_z)))
    action = encode_applied_action(
        target_idx=sampled_idx,
        move_gym=move_gym,
        shutter_gym=shutter_gym,
    )

    checks["A_sample_to_onehot"] = (
        action.shape == (52,)
        and action[23] == 1.0
        and action[22] == 0.0
        and abs(float(action[:50].sum()) - 1.0) < 1e-4
    )
    checks["B_index_layout"] = (
        abs(float(action[MOVE_IDX]) - move_gym) < 1e-5
        and abs(float(action[SHUTTER_IDX]) - shutter_gym) < 1e-5
    )
    checks["C_decode_roundtrip"] = (
        decode_target_idx(action) == 23
        and decode_move(action) is True
        and decode_shutter(action) is False
    )
    swapped = action.copy()
    swapped[MOVE_IDX], swapped[SHUTTER_IDX] = swapped[SHUTTER_IDX], swapped[MOVE_IDX]
    checks["D_swap_detection"] = decode_move(swapped) is False and decode_shutter(swapped) is True

    setup = build_exp14_env_setup_fixed()
    resolved = setup.resolve(require_camera=True)
    earth_radius_km = float(resolved.earth_radius.to(resolved.ureg.km).magnitude)
    from autonomous_control.controller_observation import resolve_target_anchor_xy_km

    anchors = resolve_target_anchor_xy_km(
        tuple(resolved.target_areas or ()),
        earth_radius_km=earth_radius_km,
    )
    target_anchor = anchors[decode_target_idx(action)]
    sat_pos = np.array([0.0, 6871.0], dtype=float)
    theta_orbit = np.pi / 4
    theta_target = target_boresight_angle_rad(sat_pos, target_anchor)
    u = theta_target_to_u(theta_target_rad=theta_target, theta_orbit_rad=theta_orbit)
    checks["E_actuator_u_bounded"] = -1.0 <= float(u) <= 1.0

    wu = encode_warmup_action(target_idx=7, move=True, shutter=False)
    checks["F_warmup_format"] = (
        wu[7] == 1.0
        and abs(float(wu[:50].sum()) - 1.0) < 1e-4
        and wu[MOVE_IDX] == GYM_TRUE
        and wu[SHUTTER_IDX] == GYM_FALSE
        and decode_target_idx(wu) == 7
        and decode_move(wu) is True
        and decode_shutter(wu) is False
    )

    rollout = run_baseline_overflight_rollout(
        setup,
        show_progress=False,
        attitude_request_mode="vector",
        targets_per_episode=10,
    )
    score = compute_episode_mission_score(rollout.series, rollout.cmd_steps)
    checks["G_baseline_score_positive"] = float(score) > 0.0
    checks["G_baseline_vector_mode"] = True

    layout = controller_observation_layout(
        feature_config=FEATURE_CONFIG,
        secondary_camera_observation_line_n_bins=int(
            resolved.secondary_camera_observation_line_n_bins
        ),
        n_mission_targets=len(resolved.target_areas or ()),
    )
    checks["G_obs_layout"] = layout.scalar_dim == 3 + 50 + 50 + 1

    import _screen_runner as _screen_runner_mod
    from _exp14_artifacts import export_screen_arm_artifacts

    checks["H_screen_artifact_export_bound"] = (
        callable(export_screen_arm_artifacts)
        and getattr(_screen_runner_mod, "export_screen_arm_artifacts", None)
        is export_screen_arm_artifacts
    )

    if not all(checks.values()):
        failed = [name for name, ok in checks.items() if not ok]
        raise VerifyError(f"Verify checks failed: {failed}")
    return checks


__all__ = ["run_verify_checks", "VerifyError"]
