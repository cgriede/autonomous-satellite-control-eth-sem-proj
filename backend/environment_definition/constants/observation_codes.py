"""Indexed primary-camera observation codes (space / earth / cloud / target T0..Tn)."""

from __future__ import annotations

import numpy as np

from .SIMULATION import (
    OBSERVATION_CLOUD,
    OBSERVATION_EARTH,
    OBSERVATION_LINE_NOT_COMPUTED,
    OBSERVATION_SPACE,
    OBSERVATION_TARGET,
)

# ``OBSERVATION_TARGET`` (3) is target index 0 (T0); index i → code 3 + i.
OBSERVATION_TARGET_CODE_BASE = int(OBSERVATION_TARGET)


def observation_target_code_for_index(target_index: int) -> np.int8:
    """Observation-line code for mission target ``target_index`` (0 → T0)."""
    if target_index < 0:
        raise ValueError("target_index must be non-negative.")
    code = OBSERVATION_TARGET_CODE_BASE + int(target_index)
    if code > 127:
        raise ValueError(f"target_index {target_index} exceeds int8 observation code range.")
    return np.int8(code)


def target_index_from_observation_code(code: int) -> int | None:
    """Map a target observation code to its mission target index, or ``None``."""
    c = int(code)
    if c < OBSERVATION_TARGET_CODE_BASE:
        return None
    return c - OBSERVATION_TARGET_CODE_BASE


def is_observation_target_code(code: int) -> bool:
    return int(code) >= OBSERVATION_TARGET_CODE_BASE


def observation_code_to_ascii(code: int) -> str:
    """
    Single-character ASCII for one observation-line bin.

    Targets render as digits ``0``–``9`` for T0–T9, then ``A``–``Z`` for T10–T35.
  Space ``-``, earth ``E``, cloud ``C``, not computed ``?``.
    """
    c = int(code)
    if c == int(OBSERVATION_SPACE):
        return "-"
    if c == int(OBSERVATION_EARTH):
        return "E"
    if c == int(OBSERVATION_CLOUD):
        return "C"
    if c == int(OBSERVATION_LINE_NOT_COMPUTED):
        return "?"
    if is_observation_target_code(c):
        idx = target_index_from_observation_code(c)
        assert idx is not None
        if idx < 10:
            return str(idx)
        if idx < 36:
            return chr(ord("A") + idx - 10)
        raise ValueError(f"no ASCII glyph for target index {idx}")
    raise ValueError(f"unknown observation code: {c}")


def observation_target_ascii_label(code: int) -> str:
    """Human label ``T0``, ``T1``, … for telemetry / docs."""
    idx = target_index_from_observation_code(code)
    if idx is None:
        raise ValueError(f"code {code} is not a target code")
    return f"T{idx}"
