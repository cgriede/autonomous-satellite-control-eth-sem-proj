#!/usr/bin/env python
"""Profile one MPO train episode: sim vs learner vs sync overhead."""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from _profile_runner import profile_train_episode  # noqa: E402


def _format_markdown(report: dict) -> str:
    ctx = report.get("context", {})
    lines = [
        "# Train timing profile — one episode",
        "",
        f"- **Run at:** {report.get('run_at_utc', '')}",
        f"- **DT profile:** {ctx.get('dt_label', '?')}",
        f"- **Device:** {ctx.get('device_name', ctx.get('device', '?'))}",
        f"- **Sim steps:** {report['n_sim_steps']}",
        f"- **Controller stores:** {report['n_controller_stores']}",
        f"- **Train updates:** {report['n_train_updates']}",
        f"- **Episode wall:** {report['episode_wall_s']:.3f} s",
        f"- **Warmup wall (excluded):** {ctx.get('warmup_wall_s', 0.0):.3f} s",
        f"- **Steps/s:** {report['steps_per_s']:.2f}",
        f"- **Per-step wall:** {report['per_step_wall_ms']:.2f} ms",
        f"- **Unaccounted:** {report['unaccounted_s']:.3f} s",
        "",
        "## Knobs",
        "",
        f"- updates_per_step: {ctx.get('updates_per_step')}",
        f"- train_every_n_steps: {ctx.get('train_every_n_steps')}",
        f"- batch_size: {ctx.get('batch_size')}",
        f"- num_samples_q / pi: {ctx.get('num_samples_q')} / {ctx.get('num_samples_pi')}",
        "",
        "## Top consumers (% of episode wall)",
        "",
        "| Rank | Category | Total (s) | Per step (ms) | % wall |",
        "|------|----------|-----------|---------------|--------|",
    ]
    for rank, row in enumerate(report.get("top_7_consumers", []), start=1):
        lines.append(
            f"| {rank} | {row['label']} | {row['total_s']:.3f} | "
            f"{row['per_step_ms']:.3f} | {row['pct_of_wall']:.1f}% |"
        )
    lines.append("")
    lines.append("## All categories")
    lines.append("")
    lines.append("| Category | Total (s) | Per step (ms) | % wall |")
    lines.append("|----------|-----------|---------------|--------|")
    for row in report.get("categories", []):
        lines.append(
            f"| {row['label']} | {row['total_s']:.3f} | "
            f"{row['per_step_ms']:.3f} | {row['pct_of_wall']:.1f}% |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    warnings.filterwarnings("ignore", category=RuntimeWarning, message="All-NaN slice encountered")
    parser = argparse.ArgumentParser(description="Profile one train episode by wall-time category.")
    parser.add_argument(
        "--dt-label",
        default="dt_1.5s",
        choices=("ref_0.4s", "dt_0.8s", "dt_1.0s", "dt_1.5s"),
        help="Simulation dt / controller profile (default: dt_1.5s production compare).",
    )
    parser.add_argument("--updates-per-step", type=int, default=1)
    parser.add_argument("--train-every-n-steps", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument(
        "--rebuild-warmup-cache",
        action="store_true",
        help="Force rebuild warmup bundle cache before profiling.",
    )
    parser.add_argument(
        "--skip-warmup",
        action="store_true",
        help="Skip warmup (buffer must already be primed — not for normal use).",
    )
    parser.add_argument(
        "--tag",
        default="default",
        help="Output filename tag (default: default).",
    )
    args = parser.parse_args()

    report = profile_train_episode(
        run_slug=f"train_timing_{args.tag}",
        dt_label=args.dt_label,
        updates_per_step=args.updates_per_step,
        train_every_n_steps=args.train_every_n_steps,
        batch_size=args.batch_size,
        rebuild_warmup_bundle_cache=args.rebuild_warmup_cache,
        skip_warmup=args.skip_warmup,
    )
    report["run_at_utc"] = datetime.now(timezone.utc).isoformat()

    results_dir = EXPERIMENT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    json_path = results_dir / f"train_episode_{args.tag}.json"
    md_path = results_dir / f"train_episode_{args.tag}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_format_markdown(report), encoding="utf-8")

    ctx = report.get("context", {})
    print(f"\n=== train episode ({args.tag}) ===")
    print(f"  device: {ctx.get('device_name')}")
    print(f"  wall: {report['episode_wall_s']:.2f}s  steps/s: {report['steps_per_s']:.2f}")
    print(f"  stores: {report['n_controller_stores']}  train updates: {report['n_train_updates']}")
    print("  Top consumers:")
    for rank, row in enumerate(report["top_7_consumers"], start=1):
        print(
            f"    {rank}. {row['label']}: {row['total_s']:.3f}s "
            f"({row['pct_of_wall']:.1f}%)"
        )
    print(f"  Wrote {json_path.name}, {md_path.name}")


if __name__ == "__main__":
    main()
