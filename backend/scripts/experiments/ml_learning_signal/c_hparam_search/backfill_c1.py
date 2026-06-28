"""Backfill c1 result JSON from completed run episodes.csv."""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from _runner_common import (  # noqa: E402
    RESULTS_DIR,
    evaluate_increasing_signal,
    write_hypothesis_result,
)

RUN_DIR = BACKEND_DIR / "autonomous_control" / "models" / "ml_ls_c1_no_dropout_high_pi_lr_17-46-27"
EPISODES_CSV = RUN_DIR / "episodes.csv"
OVERRIDES = {"actor_dropout": 0.0, "learning_rate_pi": 4.5e-4}


def main() -> None:
    rows = list(csv.DictReader(EPISODES_CSV.open(encoding="utf-8")))
    warmup = [float(r["episode_return"]) for r in rows if r["phase"] == "warmup"]
    train = [float(r["episode_return"]) for r in rows if r["phase"] == "train"]
    signal = evaluate_increasing_signal(train)
    kpis = {
        "run_id": "ml_ls_c1_no_dropout_high_pi_lr",
        "run_dir": str(RUN_DIR),
        "warmup_from_cache": True,
        "warmup_returns": warmup,
        "warmup_return_mean": sum(warmup) / len(warmup) if warmup else 0.0,
        "train_returns": train,
        "train_return_mean": sum(train) / len(train) if train else 0.0,
        "train_return_best": max(train) if train else 0.0,
        "increasing_signal": signal,
        "debug_episodes": [],
        "last_train_learning": {},
        "note": "Backfilled from episodes.csv; CLI killed before JSON write.",
    }
    out = RESULTS_DIR / "c1_no_dropout_high_pi_lr.json"
    verdict = "supported" if signal["strong_lead"] else "inconclusive"
    write_hypothesis_result(
        out,
        experiment_id="ml_learning_signal",
        hypothesis_id="hparam_no_dropout_high_pi_lr",
        phase="C1",
        frozen_input={"mpo_overrides": OVERRIDES},
        control=None,
        treatment={"kpis": kpis},
        delta={"strong_lead": signal["strong_lead"], "train_returns": signal["train_returns_ep1_ep3"]},
        parity={"required": True, "passed": True, "notes": "hparam only"},
        instrumentation={"hooks_valid": True},
        debug_examples={"train_episodes": train, "episodes_csv": str(EPISODES_CSV)},
        files_changed=[str(Path(__file__))],
        verdict=verdict,
        closeout=f"Hparam variant no_dropout_high_pi_lr backfilled at {datetime.now(timezone.utc).isoformat()}.",
    )
    print(f"Wrote {out}")
    print(f"  returns={signal['train_returns_ep1_ep3']} strong_lead={signal['strong_lead']}")


if __name__ == "__main__":
    main()
