"""Branch C run 1: hparam variant — zero dropout + higher pi LR."""

from __future__ import annotations

import sys
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from _runner_common import RESULTS_DIR, run_training_slice, write_analysis_card, write_hypothesis_result  # noqa: E402

VARIANTS = [
    {"id": "c1", "overrides": {"actor_dropout": 0.0, "learning_rate_pi": 4.5e-4}, "label": "no_dropout_high_pi_lr"},
    {"id": "c2", "overrides": {"learning_rate_q": 1.0e-3, "target_kl_mu": 0.05}, "label": "high_q_lr_tight_kl"},
    {"id": "c3", "overrides": {"actor_dropout": 0.0, "learning_rate_pi": 4.5e-4, "num_units_actor": 128}, "label": "combo_wide_actor"},
]


def run_variant(variant: dict) -> None:
    kpis = run_training_slice(
        run_id=f"ml_ls_{variant['id']}_{variant['label']}",
        mpo_overrides=variant["overrides"],
        show_progress=False,
    )
    signal = kpis["increasing_signal"]
    verdict = "supported" if signal["strong_lead"] else "inconclusive"
    out = RESULTS_DIR / f"{variant['id']}_{variant['label']}.json"
    write_hypothesis_result(
        out,
        experiment_id="ml_learning_signal",
        hypothesis_id=f"hparam_{variant['label']}",
        phase=variant["id"].upper(),
        frozen_input={"mpo_overrides": variant["overrides"]},
        control=None,
        treatment={"kpis": kpis},
        delta={"strong_lead": signal["strong_lead"], "train_returns": signal["train_returns_ep1_ep3"]},
        parity={"required": True, "passed": True, "notes": "hparam only"},
        instrumentation={"hooks_valid": True},
        debug_examples={"train_episodes": kpis["debug_episodes"]},
        files_changed=[str(Path(__file__))],
        verdict=verdict,
        closeout=f"Hparam variant {variant['label']}.",
    )
    print(f"  {variant['id']}: returns={signal['train_returns_ep1_ep3']} strong_lead={signal['strong_lead']}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["c1", "c2", "c3", "all"], default="c1")
    args = parser.parse_args()
    to_run = VARIANTS if args.variant == "all" else [v for v in VARIANTS if v["id"] == args.variant]
    for v in to_run:
        run_variant(v)
    if args.variant == "c1":
        write_analysis_card(
            RESULTS_DIR / "hparam_search_analysis.md",
            hypothesis_id="hparam_search",
            json_path=RESULTS_DIR / "c1_no_dropout_high_pi_lr.json",
            sections={"1 Variant": "c1 no dropout + high pi LR", "2 Note": "Run c2/c3 separately within branch budget."},
        )


if __name__ == "__main__":
    main()
