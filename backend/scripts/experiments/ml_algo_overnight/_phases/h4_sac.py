"""H4: SAC with fixed entropy coefficient (sparse reward)."""

from __future__ import annotations

import sys
from pathlib import Path

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

H4_JSON = RESULTS_DIR / "h4_sac.json"
H4_ANALYSIS = EXPERIMENT_ROOT / "H4-sac_analysis.md"


def phase_h4_sac(*, show_progress: bool = False) -> dict:
    spec = PhaseSpec(
        phase_id="h4",
        hypothesis_id="sac_entropy_fixed_alpha",
        run_id="h4_sac",
        reward_mode="sparse",
        agent_kind="sac",
        rebuild_warmup_cache=False,
    )
    kpis = run_hypothesis_phase(spec, show_progress=show_progress)
    signal = kpis["learning_signal"]
    verdict = verdict_from_signal(signal)
    write_hypothesis_result(
        H4_JSON,
        experiment_id="ml_algo_overnight",
        hypothesis_id="sac_entropy_fixed_alpha",
        phase="h4",
        frozen_input={"seed": 7, "reward_mode": "sparse", "alpha": 0.2},
        treatment={"kpis": kpis},
        learning_signal=signal,
        verdict=verdict,
    )
    write_analysis_card(
        H4_ANALYSIS,
        hypothesis_id="sac_entropy_fixed_alpha",
        json_path=H4_JSON,
        sections={
            "Hypothesis": "Off-policy SAC (fixed α=0.2) learns where MPO fails on sparse EO reward.",
            "Setup": f"run_dir: `{kpis['run_dir']}`; reuses production Actor/Critic.",
            "Primary KPI": f"learning_mode={signal['learning_mode']}; train={signal['train_returns']}",
            "Eval": f"eval_return_mean={signal['eval_return_mean']}",
            "Compare MPO": "Contrast with h1a/h1b/h6 on same dt profile.",
            "Verdict": verdict,
            "Artifacts": str(kpis.get("artifacts", {})),
        },
    )
    return kpis
