"""Dominant target selection from primary observation-line codes."""

from __future__ import annotations

import numpy as np

from environment_definition.constants.observation_codes import (
    is_observation_target_code,
    target_index_from_observation_code,
)


def dominant_capture_target_index(codes: np.ndarray) -> int | None:
    """
    Mission target index with the most bins on the primary observation line.

    Tie-break: lowest index. Returns ``None`` when no target bins are present.
    """
    arr = np.asarray(codes, dtype=np.int8).ravel()
    counts: dict[int, int] = {}
    for code in arr:
        idx = target_index_from_observation_code(int(code))
        if idx is None:
            continue
        counts[idx] = counts.get(idx, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda item: (item[1], -item[0]))[0]


def primary_target_pixel_coverage(codes: np.ndarray, *, target_index: int | None = None) -> float:
    """
    Fraction of observation-line bins on a target.

    When ``target_index`` is ``None``, counts bins on **any** target (T0, T1, …).
    When set, counts only bins matching that target index.
    """
    arr = np.asarray(codes, dtype=np.int8).ravel()
    if arr.size == 0:
        return 0.0
    if target_index is None:
        hits = sum(1 for c in arr if is_observation_target_code(int(c)))
    else:
        hits = sum(
            1
            for c in arr
            if target_index_from_observation_code(int(c)) == int(target_index)
        )
    return float(hits) / float(arr.size)


def target_visible_from_codes(codes: np.ndarray) -> bool:
    return dominant_capture_target_index(codes) is not None
