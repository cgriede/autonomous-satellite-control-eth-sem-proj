"""Canonical 52-dim factored action layout for Exp 14 (single source of truth)."""

from __future__ import annotations

import numpy as np

N_TARGETS = 50
N_ACTION_DIMS = 52

TARGET_SLICE = slice(0, 50)
MOVE_IDX = 50
SHUTTER_IDX = 51

BOOL_GYM_THRESHOLD = 0.0
GYM_TRUE = 1.0
GYM_FALSE = -1.0


def encode_applied_action(
    target_idx: int,
    move_gym: float,
    shutter_gym: float,
) -> np.ndarray:
    """Build 52-dim replay action from applied (sampled) policy step."""
    if not 0 <= int(target_idx) < N_TARGETS:
        raise ValueError(f"target_idx={target_idx} out of [0, {N_TARGETS})")
    action = np.zeros(N_ACTION_DIMS, dtype=np.float32)
    action[int(target_idx)] = 1.0
    action[MOVE_IDX] = float(move_gym)
    action[SHUTTER_IDX] = float(shutter_gym)
    return action


def encode_warmup_action(
    target_idx: int,
    move: bool,
    shutter: bool,
) -> np.ndarray:
    """Build 52-dim replay action from warmup baseline step (Dirac target distribution)."""
    return encode_applied_action(
        target_idx=int(target_idx),
        move_gym=GYM_TRUE if move else GYM_FALSE,
        shutter_gym=GYM_TRUE if shutter else GYM_FALSE,
    )


def decode_target_idx(action: np.ndarray) -> int:
    """Recover executed target index from stored one-hot."""
    return int(np.argmax(np.asarray(action)[TARGET_SLICE]))


def decode_move(action: np.ndarray) -> bool:
    return float(np.asarray(action)[MOVE_IDX]) > BOOL_GYM_THRESHOLD


def decode_shutter(action: np.ndarray) -> bool:
    return float(np.asarray(action)[SHUTTER_IDX]) > BOOL_GYM_THRESHOLD


__all__ = [
    "BOOL_GYM_THRESHOLD",
    "GYM_FALSE",
    "GYM_TRUE",
    "MOVE_IDX",
    "N_ACTION_DIMS",
    "N_TARGETS",
    "SHUTTER_IDX",
    "TARGET_SLICE",
    "decode_move",
    "decode_shutter",
    "decode_target_idx",
    "encode_applied_action",
    "encode_warmup_action",
]
