"""Write summary + plots from saved arm_kpis/ (no re-train)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"
for path in (BACKEND_DIR, S01_DIR, OVERNIGHT_ROOT, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import numpy as np

from _plot_shutter import write_all_plots
from _shutter_runner import verdict_for_arm, write_analysis_card, write_hypothesis_result
from run_shutter_threshold import (
    ANALYSIS_MD,
    RESULTS_DIR,
    SUMMARY_JSON,
    backfill_arm_kpis_from_summary,
    load_arm_kpis,
    merge_arm_results,
)


def main() -> None:
    backfill_arm_kpis_from_summary()
    plot_arms = merge_arm_results({})
    baseline_cmds = list((load_arm_kpis("mpo_t05") or {}).get("shutter_cmds_per_episode") or [])
    plot_paths = write_all_plots(plot_arms)
    arm_summaries = {}
    for arm_id, kpis in plot_arms.items():
        v = verdict_for_arm(kpis, baseline_cmds=baseline_cmds if arm_id != "mpo_t05" else None)
        arm_summaries[arm_id] = {
            "verdict": v,
            "threshold": kpis.get("threshold"),
            "learning_mode": (kpis.get("learning_signal") or {}).get("learning_mode"),
            "train_returns": kpis.get("train_returns") or [],
            "shutter_cmds_per_episode": kpis.get("shutter_cmds_per_episode") or [],
            "eval_return_mean": kpis.get("eval_return_mean"),
            "wall_s": kpis.get("wall_s"),
        }
    summary = {
        "experiment_id": "ml_shutter_threshold",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "dt_profile": json.loads((RESULTS_DIR / "dt_profile.json").read_text(encoding="utf-8")),
        "arms": arm_summaries,
        "plots": plot_paths,
    }
    write_hypothesis_result(SUMMARY_JSON, **summary)
    write_analysis_card(
        ANALYSIS_MD,
        hypothesis_id="shutter_threshold_mpo",
        json_path=SUMMARY_JSON,
        sections={
            "Hypothesis": "Threshold 0.9 reduces MPO shutter spam vs 0.5 with 15s capture window.",
            "Arms": json.dumps(arm_summaries, indent=2),
            "Plots": "\n".join(f"- `{p}`" for p in plot_paths),
            "Verdict": json.dumps({k: v["verdict"] for k, v in arm_summaries.items()}),
        },
    )
    for arm_id, s in arm_summaries.items():
        cmds = s["shutter_cmds_per_episode"]
        print(
            f"{arm_id}: verdict={s['verdict']} "
            f"mean_shutter_cmds={float(np.mean(cmds)):.1f} "
            f"learning_mode={s['learning_mode']}"
        )
    print(f"Wrote {SUMMARY_JSON}")


if __name__ == "__main__":
    main()
