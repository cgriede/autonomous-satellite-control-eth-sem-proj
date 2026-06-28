"""H6: MPO + dense latent reward + 10× applied shutter capture."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from _runner_common import (
    PhaseSpec,
    RESULTS_DIR,
    run_hypothesis_phase,
    verdict_from_signal,
    write_analysis_card,
    write_hypothesis_result,
)

H6_JSON = RESULTS_DIR / "h6_mpo_dense_latent.json"
H6_ANALYSIS = EXPERIMENT_ROOT / "H6-dense-latent_analysis.md"


def _h6_diagnostics(kpis: dict[str, Any]) -> dict[str, Any]:
    rows = kpis.get("debug_episodes") or []
    pos_steps = [int(r.get("positive_reward_steps", 0)) for r in rows]
    returns = [float(r.get("episode_return", 0.0)) for r in rows]
    return {
        "mean_positive_reward_steps": float(np.mean(pos_steps)) if pos_steps else 0.0,
        "train_return_integral": float(np.sum(returns)),
        "train_returns": returns,
    }


def phase_h6_mpo_dense_latent(*, show_progress: bool = False) -> dict[str, Any]:
    spec = PhaseSpec(
        phase_id="h6",
        hypothesis_id="mpo_dense_latent_10x_shutter",
        run_id="h6_mpo_dense_latent",
        reward_mode="dense_latent_10x_applied",
        agent_kind="mpo",
        rebuild_warmup_cache=True,
    )
    kpis = run_hypothesis_phase(spec, show_progress=show_progress)
    h6_diag = _h6_diagnostics(kpis)
    kpis["h6_diagnostics"] = h6_diag
    signal = kpis["learning_signal"]
    verdict = verdict_from_signal(signal)
    write_hypothesis_result(
        H6_JSON,
        experiment_id="ml_algo_overnight",
        hypothesis_id="mpo_dense_latent_10x_shutter",
        phase="h6",
        frozen_input={
            "seed": 7,
            "reward_mode": "dense_latent_10x_applied",
            "rebuild_warmup_cache": True,
        },
        treatment={"kpis": kpis, "h6_diagnostics": h6_diag},
        learning_signal=signal,
        verdict=verdict,
    )
    write_analysis_card(
        H6_ANALYSIS,
        hypothesis_id="mpo_dense_latent_10x_shutter",
        json_path=H6_JSON,
        sections={
            "Hypothesis": "Dense latent every step + 10× applied shutter credit unblocks MPO learning.",
            "Setup": f"run_dir: `{kpis['run_dir']}`; warmup cache rebuilt for reward fingerprint.",
            "Primary KPI": f"learning_mode={signal['learning_mode']}; train={signal['train_returns']}",
            "H6 diagnostics": str(h6_diag),
            "Eval": f"eval_return_mean={signal['eval_return_mean']}",
            "Compare H1": "Contrast with h1a/h1b sparse arms on same dt profile.",
            "Verdict": verdict,
            "Artifacts": str(kpis.get("artifacts", {})),
        },
    )
    return kpis
