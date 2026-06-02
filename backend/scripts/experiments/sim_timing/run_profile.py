#!/usr/bin/env python
"""Profile simulation loop timing and report top-N time consumers."""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parent
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

from _profile_runner import profile_scenario  # noqa: E402


def _format_markdown(report: dict) -> str:
    ctx = report.get("context", {})
    lines = [
        f"# Sim timing profile — {ctx.get('scenario', '?')}",
        "",
        f"- **Run at:** {report.get('run_at_utc', '')}",
        f"- **Clouds:** {ctx.get('n_clouds', '?')}",
        f"- **Steps:** {report['n_steps']}",
        f"- **Sim loop wall:** {report['sim_loop_wall_s']:.3f} s",
        f"- **Steps/s:** {report['steps_per_s']:.2f}",
        f"- **Per-step wall:** {report['per_step_wall_ms']:.2f} ms",
        f"- **Unaccounted in loop:** {report['unaccounted_in_loop_s']:.3f} s",
        "",
        "## Top 7 time consumers",
        "",
        "| Rank | Category | Total (s) | Per step (ms) | % of sim loop |",
        "|------|----------|-----------|---------------|---------------|",
    ]
    for rank, row in enumerate(report.get("top_7_consumers", []), start=1):
        per_ms = row.get("per_step_ms")
        per_str = "—" if per_ms is None else f"{per_ms:.3f}"
        lines.append(
            f"| {rank} | {row['label']} | {row['total_s']:.3f} | {per_str} | {row['pct_of_sim_loop']:.1f}% |"
        )
    lines.append("")
    lines.append("## All categories")
    lines.append("")
    lines.append("| Category | Total (s) | Per step (ms) | % of sim loop |")
    lines.append("|----------|-----------|---------------|---------------|")
    for row in report.get("categories", []):
        per_ms = row.get("per_step_ms")
        per_str = "—" if per_ms is None else f"{per_ms:.3f}"
        lines.append(
            f"| {row['label']} | {row['total_s']:.3f} | {per_str} | {row['pct_of_sim_loop']:.1f}% |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    warnings.filterwarnings("ignore", category=RuntimeWarning, message="All-NaN slice encountered")
    parser = argparse.ArgumentParser(description="Profile simulation timing by category.")
    parser.add_argument(
        "--scenario",
        choices=("low_cloud", "high_cloud", "sat_sim_interactive", "both"),
        default="both",
        help="Fixture scenario (default: both). sat_sim_interactive = Sat Sim Interactive launch.",
    )
    parser.add_argument(
        "--with-render",
        action="store_true",
        help="Also time render + MP4 export after sim.",
    )
    args = parser.parse_args()

    scenarios = {
        "both": ["low_cloud", "high_cloud"],
        "low_cloud": ["low_cloud"],
        "high_cloud": ["high_cloud"],
        "sat_sim_interactive": ["sat_sim_interactive"],
    }[args.scenario]
    results_dir = EXPERIMENT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    for scenario in scenarios:
        do_render = bool(args.with_render)
        report = profile_scenario(scenario, with_render=do_render)
        report["run_at_utc"] = datetime.now(timezone.utc).isoformat()

        json_path = results_dir / f"{scenario}_timing.json"
        md_path = results_dir / f"{scenario}_timing.md"
        json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        md_path.write_text(_format_markdown(report), encoding="utf-8")

        print(f"\n=== {scenario} (n_clouds={report['context']['n_clouds']}) ===")
        print(f"  steps/s: {report['steps_per_s']:.2f}  wall: {report['sim_loop_wall_s']:.2f}s")
        print("  Top consumers:")
        for rank, row in enumerate(report["top_7_consumers"], start=1):
            per_ms = row.get("per_step_ms")
            extra = f"  ({per_ms:.2f} ms/step)" if per_ms is not None else ""
            print(f"    {rank}. {row['label']}: {row['total_s']:.3f}s ({row['pct_of_sim_loop']:.1f}%){extra}")
        print(f"  Wrote {json_path.name}, {md_path.name}")


if __name__ == "__main__":
    main()
