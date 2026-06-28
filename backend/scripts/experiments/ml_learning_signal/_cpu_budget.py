"""Cap BLAS/OpenMP/torch threads for ml_learning_signal runners.

Import this module before numpy/torch so parallel subagent jobs do not each
claim all logical cores (N processes × all cores → oversubscription).

Override with env ``ASC_CPU_THREADS`` (integer, default heuristic below).
"""

from __future__ import annotations

import os


def _resolve_thread_count() -> int:
    raw = os.environ.get("ASC_CPU_THREADS")
    if raw is not None and raw.strip():
        return max(1, int(raw))
    n_logical = os.cpu_count() or 4
    # Dev laptop: assume up to ~2 concurrent experiment jobs; cap per process at 4.
    return max(1, min(4, n_logical // 2))


def apply_cpu_thread_budget(*, threads: int | None = None) -> int:
    n = max(1, int(threads if threads is not None else _resolve_thread_count()))
    for key in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        os.environ.setdefault(key, str(n))
    try:
        import torch

        torch.set_num_threads(n)
        if hasattr(torch, "set_num_interop_threads"):
            torch.set_num_interop_threads(max(1, n // 2))
    except ImportError:
        pass
    return n


_APPLIED = apply_cpu_thread_budget()
