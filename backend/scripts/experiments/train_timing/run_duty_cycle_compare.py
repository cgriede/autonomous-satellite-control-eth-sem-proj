#!/usr/bin/env python
"""Compare learn duty-cycle knobs (collect N stores, burst M trains)."""

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

# (label, train_every_n_steps, updates_per_step)
DEFAULT_VARIANTS: tuple[tuple[str, int, int], ...] = (
    ("baseline_1x1", 1, 1),
    ("duty_4x4", 4, 4),
    ("duty_4x1", 4, 1),
    ("duty_10x1", 10, 1),
    ("duty_100x1", 100, 1),
    ("duty_10x10", 10, 10),
    ("duty_100x100", 100, 100),
)


def _format_markdown(rows: list[dict], *, run_at: str) -> str:
    lines = [
        "# Learn duty-cycle comparison",
        "",
        f"- **Run at:** {run_at}",
        "",
        "Knobs: `train_every_n_steps` = collect stores before learn gate; "
        "`updates_per_step` = train() calls per gate. "
        "Matched duty `N×N` keeps ~same total train updates as baseline.",
        "",
        "| Variant | collect | burst | wall (s) | steps/s | train updates | train % | sim % | get_action % |",
        "|---------|---------|-------|----------|---------|---------------|---------|-------|--------------|",
    ]
    baseline_sps = rows[0]["steps_per_s"] if rows else 1.0
    for row in rows:
        top = {c["key"]: c for c in row.get("categories", [])}
        train_pct = top.get("train", {}).get("pct_of_wall", 0.0)
        sim_pct = top.get("sim_step", {}).get("pct_of_wall", 0.0)
        act_pct = top.get("get_action", {}).get("pct_of_wall", 0.0)
        speedup = row["steps_per_s"] / baseline_sps if baseline_sps > 0 else 0.0
        lines.append(
            f"| {row['variant']} | {row['collect']} | {row['burst']} | "
            f"{row['episode_wall_s']:.2f} | {row['steps_per_s']:.2f} "
            f"({speedup:.2f}×) | {row['n_train_updates']} | "
            f"{train_pct:.1f}% | {sim_pct:.1f}% | {act_pct:.1f}% |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    warnings.filterwarnings("ignore", category=RuntimeWarning, message="All-NaN slice encountered")
    parser = argparse.ArgumentParser(description="Sweep learn duty-cycle variants.")
    parser.add_argument("--dt-label", default="dt_1.5s")
    parser.add_argument(
        "--variants",
        nargs="*",
        default=[],
        help="Optional subset of variant labels (default: all).",
    )
    parser.add_argument(
        "--rebuild-warmup-cache",
        action="store_true",
        help="Rebuild warmup cache for first variant only.",
    )
    args = parser.parse_args()

    variants = DEFAULT_VARIANTS
    if args.variants:
        wanted = set(args.variants)
        variants = tuple(v for v in DEFAULT_VARIANTS if v[0] in wanted)
        if not variants:
            raise SystemExit(f"No matching variants in {wanted}")

    run_at = datetime.now(timezone.utc).isoformat()
    results_dir = EXPERIMENT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for idx, (label, collect, burst) in enumerate(variants):
        report = profile_train_episode(
            run_slug=f"train_timing_duty_{label}",
            dt_label=args.dt_label,
            train_every_n_steps=collect,
            updates_per_step=burst,
            rebuild_warmup_bundle_cache=args.rebuild_warmup_cache and idx == 0,
        )
        row = {
            "variant": label,
            "collect": collect,
            "burst": burst,
            "episode_wall_s": report["episode_wall_s"],
            "steps_per_s": report["steps_per_s"],
            "n_sim_steps": report["n_sim_steps"],
            "n_controller_stores": report["n_controller_stores"],
            "n_train_updates": report["n_train_updates"],
            "categories": report["categories"],
            "context": report.get("context", {}),
        }
        rows.append(row)
        print(
            f"{label}: wall={row['episode_wall_s']:.2f}s "
            f"steps/s={row['steps_per_s']:.2f} trains={row['n_train_updates']}"
        )

    payload = {"run_at_utc": run_at, "dt_label": args.dt_label, "variants": rows}
    json_path = results_dir / "duty_cycle_compare.json"
    md_path = results_dir / "duty_cycle_compare.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(_format_markdown(rows, run_at=run_at), encoding="utf-8")
    print(f"\nWrote {json_path.name}, {md_path.name}")


if __name__ == "__main__":
    main()
