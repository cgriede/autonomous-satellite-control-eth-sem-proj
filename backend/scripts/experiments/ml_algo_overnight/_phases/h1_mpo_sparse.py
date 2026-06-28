"""H1a sparse MPO + H1b fixed-η MPO."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agents.sac_agent_fork import configure_stable_eta_mpo
from _runner_common import (
    PhaseSpec,
    RESULTS_DIR,
    run_hypothesis_phase,
    verdict_from_signal,
    write_analysis_card,
    write_hypothesis_result,
)

H1A_JSON = RESULTS_DIR / "h1a_mpo_sparse.json"
H1B_JSON = RESULTS_DIR / "h1b_mpo_stable_eta.json"
H1A_ANALYSIS = EXPERIMENT_ROOT / "H1-mpo-sparse_analysis.md"
H1B_ANALYSIS = EXPERIMENT_ROOT / "H1b-mpo-stable-eta_analysis.md"


def _write_phase_result(path: Path, analysis_path: Path, *, hypothesis_id: str, kpis: dict[str, Any]) -> None:
    signal = kpis["learning_signal"]
    verdict = verdict_from_signal(signal)
    write_hypothesis_result(
        path,
        experiment_id="ml_algo_overnight",
        hypothesis_id=hypothesis_id,
        phase=kpis["phase_id"],
        frozen_input={
            "seed": 7,
            "reward_mode": kpis["reward_mode"],
            "dt_profile": kpis["dt_profile"],
            "train_episodes": kpis["dt_profile"].get("train_episodes"),
        },
        treatment={"kpis": kpis},
        learning_signal=signal,
        verdict=verdict,
    )
    write_analysis_card(
        analysis_path,
        hypothesis_id=hypothesis_id,
        json_path=path,
        sections={
            "Hypothesis": f"MPO with production sparse reward ({hypothesis_id}).",
            "Setup": f"Agent: {kpis['agent_kind']}; run_dir: `{kpis['run_dir']}`",
            "Primary KPI": f"learning_mode={signal['learning_mode']}; train={signal['train_returns']}",
            "Eval": f"eval_return_mean={signal['eval_return_mean']}",
            "Stability": f"KL/η: {kpis.get('learning_stats')}",
            "Verdict": verdict,
            "Next": "Compare H1a vs H1b for η dual stability.",
            "Artifacts": str(kpis.get("artifacts", {})),
        },
    )


def phase_h1a_mpo_sparse(*, show_progress: bool = False) -> dict[str, Any]:
    spec = PhaseSpec(
        phase_id="h1a",
        hypothesis_id="mpo_sparse",
        run_id="h1a_mpo_sparse",
        reward_mode="sparse",
        agent_kind="mpo",
        rebuild_warmup_cache=True,
    )
    kpis = run_hypothesis_phase(spec, show_progress=show_progress)
    _write_phase_result(H1A_JSON, H1A_ANALYSIS, hypothesis_id="mpo_sparse", kpis=kpis)
    return kpis


def phase_h1b_mpo_stable_eta(*, show_progress: bool = False) -> dict[str, Any]:
    def _hook(setup: Any) -> Any:
        configure_stable_eta_mpo(setup.agent)
        return setup

    spec = PhaseSpec(
        phase_id="h1b",
        hypothesis_id="mpo_sparse_stable_eta",
        run_id="h1b_mpo_stable_eta",
        reward_mode="sparse",
        agent_kind="mpo",
        rebuild_warmup_cache=False,
        agent_setup_hook=_hook,
    )
    kpis = run_hypothesis_phase(spec, show_progress=show_progress)
    _write_phase_result(H1B_JSON, H1B_ANALYSIS, hypothesis_id="mpo_sparse_stable_eta", kpis=kpis)
    return kpis


def phase_h1_mpo(*, show_progress: bool = False) -> dict[str, dict[str, Any]]:
    return {
        "h1a": phase_h1a_mpo_sparse(show_progress=show_progress),
        "h1b": phase_h1b_mpo_stable_eta(show_progress=show_progress),
    }
