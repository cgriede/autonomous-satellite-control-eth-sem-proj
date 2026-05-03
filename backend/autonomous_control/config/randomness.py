"""Centralized ML randomness configuration and seeding utilities."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random

import numpy as np
import torch


@dataclass(frozen=True)
class RandomnessConfig:
    """Single-source seed configuration for ML/runtime randomness."""

    seed: int = 0


def apply_global_seed(config: RandomnessConfig | int) -> int:
    """Seed python, numpy, and torch RNGs from one source."""
    seed = int(config if isinstance(config, int) else config.seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    return seed


def derive_seed(base_seed: int, namespace: str, index: int = 0) -> int:
    """Derive stable 32-bit sub-seeds for reproducible sub-components."""
    payload = f"{int(base_seed)}::{namespace}::{int(index)}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:8], 16)

