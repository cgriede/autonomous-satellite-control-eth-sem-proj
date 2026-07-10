#!/usr/bin/env python3
"""Bulk-select ≥100 report figure candidates + extract themed frame series.

Writes under docs/report/semester-project/figures/candidates/ and FIGURE_MANIFEST.md.
Does not re-run training. Uses existing run plots + MP4 frame extracts.

Themes (user request):
  - static: target placement
  - dynamic: random cloud generation (neighbor series)
  - dynamic: safety maneuver (one cycle, neighbor series)

Usage (repo root, conda auto-sat)::

    python docs/report/semester-project/figures/scripts/select_report_candidates.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import cv2

_REPO = Path(__file__).resolve().parents[5]  # .../figures/scripts → repo root
_FIG_ROOT = _REPO / "docs" / "report" / "semester-project" / "figures"
_CAND = _FIG_ROOT / "candidates"
_MANIFEST_MD = _FIG_ROOT / "FIGURE_MANIFEST.md"
_MANIFEST_CSV = _FIG_ROOT / "FIGURE_MANIFEST.csv"

# Prefer hardlink; fall back to copy.
def _link_or_copy(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "exists"
    try:
        os_link = getattr(__import__("os"), "link")
        os_link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


@dataclass
class Row:
    id: str
    status: str  # primary | backup | theme | layout-stub
    theme: str
    section_hint: str
    source: str
    dest: str
    notes: str


def _short_hash(path: Path) -> str:
    return hashlib.sha1(path.as_posix().encode()).hexdigest()[:8]


def _tag_plot(name: str) -> tuple[str, str]:
    n = name.lower()
    if "learning_curve" in n:
        return "trend-learning-curve", "Results"
    if "returns_by_episode" in n:
        return "trend-returns", "Results"
    if "eval_episode" in n:
        return "episode-diagnostics-eval", "Results"
    if "warmup_episode" in n:
        return "episode-diagnostics-warmup", "Experiments"
    if "train_episode" in n:
        return "episode-diagnostics-train", "Results"
    return "plot-other", "Results"


def collect_run_plots(limit: int = 120) -> list[Row]:
    rows: list[Row] = []
    plots = sorted(Path(_REPO / "backend" / "autonomous_control" / "runs").rglob("plots/*.png"))
    # Prefer one of each plot type per run, then fill.
    by_run: dict[str, list[Path]] = defaultdict(list)
    for p in plots:
        by_run[p.parents[1].name].append(p)

    # Round-robin: learning_curves + returns first across runs
    priority = (
        "learning_curves.png",
        "returns_by_episode.png",
        "eval_episode_diagnostics.png",
        "warmup_episode_diagnostics.png",
    )
    picked: list[Path] = []
    for pref in priority:
        for run, files in by_run.items():
            for f in files:
                if f.name == pref and f not in picked:
                    picked.append(f)
                    break
        if len(picked) >= limit:
            break

    for f in plots:
        if len(picked) >= limit:
            break
        if f not in picked:
            picked.append(f)

    for i, src in enumerate(picked[:limit]):
        theme, section = _tag_plot(src.name)
        run = src.parents[1].name
        dest_name = f"plot_{i:03d}_{theme}_{_short_hash(src)}.png"
        dest = _CAND / "plots" / dest_name
        how = _link_or_copy(src, dest)
        rows.append(
            Row(
                id=f"plot-{i:03d}",
                status="backup",
                theme=theme,
                section_hint=section,
                source=src.relative_to(_REPO).as_posix(),
                dest=dest.relative_to(_FIG_ROOT).as_posix(),
                notes=f"{how}; run={run}",
            )
        )
    return rows


def _video_frame_count(path: Path) -> tuple[cv2.VideoCapture, int, float]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {path}")
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    return cap, max(n - 1, 0), fps


def _extract_neighbors(
    video: Path,
    *,
    center_frac: float,
    n_neighbors: int,
    out_dir: Path,
    theme: str,
    section: str,
    id_prefix: str,
    notes: str,
) -> list[Row]:
    """Extract an odd-length neighbor series around center_frac of the video."""
    assert n_neighbors in (3, 5, 7)
    cap, last, fps = _video_frame_count(video)
    center = int(round(center_frac * last))
    half = n_neighbors // 2
    # Spacing: ~2% of video between neighbors so motion is visible
    stride = max(1, int(round(0.02 * last)))
    indices = [max(0, min(last, center + (k - half) * stride)) for k in range(n_neighbors)]
    # Deduplicate while preserving order
    seen: set[int] = set()
    uniq: list[int] = []
    for i in indices:
        if i not in seen:
            seen.add(i)
            uniq.append(i)

    rows: list[Row] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for j, fi in enumerate(uniq):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, bgr = cap.read()
        if not ok or bgr is None:
            continue
        t_s = fi / fps if fps > 0 else 0.0
        fname = f"{id_prefix}_n{j:02d}_of_{len(uniq):02d}_f{fi:06d}_t{t_s:06.1f}s.png"
        dest = out_dir / fname
        cv2.imwrite(str(dest), bgr)
        rows.append(
            Row(
                id=f"{id_prefix}-{j:02d}",
                status="theme",
                theme=theme,
                section_hint=section,
                source=video.relative_to(_REPO).as_posix(),
                dest=dest.relative_to(_FIG_ROOT).as_posix(),
                notes=f"{notes}; neighbor {j+1}/{len(uniq)}; frame={fi}",
            )
        )
    cap.release()
    return rows


def extract_theme_series() -> list[Row]:
    rows: list[Row] = []
    theme_root = _CAND / "themes"

    baseline = _REPO / "backend" / "notebooks" / "s01" / "artifacts" / "07-baseline-overflight.mp4"
    baseline_vec = _REPO / "backend" / "notebooks" / "s01" / "artifacts" / "07-baseline-overflight-vector.mp4"
    torque_eval = (
        _REPO
        / "backend"
        / "autonomous_control"
        / "runs"
        / "9998217183842846_ml_ref_ref0_torque_10-42-36"
        / "videos"
        / "eval_best.mp4"
    )
    safe_mode_eval = (
        _REPO
        / "backend"
        / "autonomous_control"
        / "runs"
        / "9998217144237087_ml_mpo_safe_mode_penalty_safe_mode_penalty_on_21-42-42"
        / "videos"
        / "eval_best.mp4"
    )
    torque_mpo = (
        _REPO
        / "backend"
        / "autonomous_control"
        / "runs"
        / "9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19"
        / "videos"
        / "eval_best.mp4"
    )
    sac_best = (
        _REPO
        / "backend"
        / "autonomous_control"
        / "runs"
        / "9998217165798903_ml_sac_shutter_split_15-43-20"
        / "videos"
        / "eval_best.mp4"
    )

    # --- static: target placement (single + 3-neighbor context) ---
    if baseline.exists():
        rows += _extract_neighbors(
            baseline,
            center_frac=0.35,
            n_neighbors=3,
            out_dir=theme_root / "01_target_placement",
            theme="static-target-placement",
            section="Introduction / Methods",
            id_prefix="theme-targets",
            notes="baseline overflight; corridor/targets visible mid-approach",
        )
        # Extra static stills at other pass fractions
        for frac, tag in [(0.15, "early"), (0.50, "mid"), (0.75, "late")]:
            rows += _extract_neighbors(
                baseline,
                center_frac=frac,
                n_neighbors=3,
                out_dir=theme_root / "01_target_placement",
                theme="static-target-placement",
                section="Introduction / Methods",
                id_prefix=f"theme-targets-{tag}",
                notes=f"baseline still cluster ({tag})",
            )

    # --- dynamic: cloud motion (5 and 7 neighbors) ---
    cloud_src = baseline_vec if baseline_vec.exists() else baseline
    if cloud_src and cloud_src.exists():
        rows += _extract_neighbors(
            cloud_src,
            center_frac=0.45,
            n_neighbors=5,
            out_dir=theme_root / "02_cloud_motion",
            theme="dynamic-cloud-generation",
            section="Methods",
            id_prefix="theme-clouds-5",
            notes="cloud field motion across neighbor frames",
        )
        rows += _extract_neighbors(
            cloud_src,
            center_frac=0.55,
            n_neighbors=7,
            out_dir=theme_root / "02_cloud_motion",
            theme="dynamic-cloud-generation",
            section="Methods",
            id_prefix="theme-clouds-7",
            notes="longer cloud motion series",
        )
        rows += _extract_neighbors(
            cloud_src,
            center_frac=0.30,
            n_neighbors=5,
            out_dir=theme_root / "02_cloud_motion",
            theme="dynamic-cloud-generation",
            section="Methods",
            id_prefix="theme-clouds-early5",
            notes="early-pass cloud motion",
        )

    # --- dynamic: safety maneuver one cycle (torque runs) ---
    for label, vid, frac in [
        ("ref0", torque_eval, 0.40),
        ("ref0b", torque_eval, 0.60),
        ("safe-pen", safe_mode_eval, 0.35),
        ("safe-penb", safe_mode_eval, 0.55),
        ("mpo-torque", torque_mpo, 0.45),
    ]:
        if vid.exists():
            rows += _extract_neighbors(
                vid,
                center_frac=frac,
                n_neighbors=5,
                out_dir=theme_root / "03_safety_maneuver",
                theme="dynamic-safety-maneuver",
                section="Methods / Discussion",
                id_prefix=f"theme-safety-{label}",
                notes="torque-mode eval; scout for safe-mode / aggressive slew cycle",
            )

    # Extra behaviour stills from best SAC (selective shutter candidate pool)
    if sac_best.exists():
        for frac, tag in [(0.25, "a"), (0.45, "b"), (0.65, "c"), (0.80, "d")]:
            rows += _extract_neighbors(
                sac_best,
                center_frac=frac,
                n_neighbors=3,
                out_dir=theme_root / "04_selective_shutter",
                theme="behaviour-selective-shutter",
                section="Results",
                id_prefix=f"theme-shutter-{tag}",
                notes="Exp9 SAC shutter-split eval_best",
            )

    return rows


def write_manifest(rows: list[Row]) -> None:
    _FIG_ROOT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with _MANIFEST_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()) if rows else ["id"])
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))

    by_theme: dict[str, list[Row]] = defaultdict(list)
    for r in rows:
        by_theme[r.theme].append(r)

    lines = [
        "# Figure candidate manifest",
        "",
        f"Generated: `{stamp}`",
        f"Total candidates: **{len(rows)}**",
        "",
        "Status legend: `theme` = requested highlight series; `backup` = bulk pool from run plots;",
        "`primary` = promote after human pick (none yet).",
        "",
        "## Counts by theme",
        "",
        "| Theme | Count |",
        "|-------|------:|",
    ]
    for theme, rs in sorted(by_theme.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        lines.append(f"| `{theme}` | {len(rs)} |")

    lines += [
        "",
        "## Requested highlight series",
        "",
        "| Theme | Folder | Notes |",
        "|-------|--------|-------|",
        "| static target placement | `candidates/themes/01_target_placement/` | baseline corridor stills |",
        "| dynamic clouds | `candidates/themes/02_cloud_motion/` | 5- and 7-neighbor series |",
        "| dynamic safety | `candidates/themes/03_safety_maneuver/` | torque eval neighbor cycles |",
        "",
        "## Next (≤1.5 h)",
        "",
        "1. Open theme folders; mark 1–2 series as `primary` in this file.",
        "2. Promote winners into `figures/` (not `candidates/`) for LaTeX.",
        "3. Regenerate only those stills at higher Earth-photo resolution if needed.",
        "4. Trend charts: use `trend-learning-curve` / `trend-returns` backups or replot from KPI JSON.",
        "",
        f"CSV: `{_MANIFEST_CSV.relative_to(_REPO).as_posix()}`",
        "",
    ]
    _MANIFEST_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "generated_utc": stamp,
        "n_candidates": len(rows),
        "by_theme": {k: len(v) for k, v in by_theme.items()},
        "manifest_md": _MANIFEST_MD.relative_to(_REPO).as_posix(),
        "manifest_csv": _MANIFEST_CSV.relative_to(_REPO).as_posix(),
    }
    (_FIG_ROOT / "FIGURE_MANIFEST_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


def main() -> None:
    _CAND.mkdir(parents=True, exist_ok=True)
    rows: list[Row] = []
    rows += collect_run_plots(limit=120)
    rows += extract_theme_series()
    write_manifest(rows)
    if len(rows) < 100:
        raise SystemExit(f"Only {len(rows)} candidates; expected ≥100")


if __name__ == "__main__":
    main()
