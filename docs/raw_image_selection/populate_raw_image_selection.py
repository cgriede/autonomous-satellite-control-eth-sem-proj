#!/usr/bin/env python3
"""Populate docs/raw_image_selection with plots, themed frames, and source videos.

Layout::

    docs/raw_image_selection/
      README.md
      MANIFEST.csv / MANIFEST.md
      plots/                          # learning curves, returns, diagnostics
      themes/
        01_target_placement/{frames,source}/
        02_cloud_motion/{frames,source}/
        03_safety_maneuver/{frames,source}/
        04_selective_shutter/{frames,source}/
        05_learning_vs_not/{frames,source}/

Usage (repo root, conda auto-sat)::

    python docs/raw_image_selection/populate_raw_image_selection.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import cv2

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "docs" / "raw_image_selection"


def _short(path: Path) -> str:
    return hashlib.sha1(path.as_posix().encode()).hexdigest()[:8]


def _link_or_copy(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "exists"
    try:
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


@dataclass
class Row:
    id: str
    kind: str  # plot | frame | source_video
    theme: str
    learning_label: str  # learning | not_learning | na
    section_hint: str
    source_repo_path: str
    dest: str
    notes: str


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


def collect_plots(limit: int = 120) -> list[Row]:
    rows: list[Row] = []
    plots = sorted((_REPO / "backend" / "autonomous_control" / "runs").rglob("plots/*.png"))
    by_run: dict[str, list[Path]] = defaultdict(list)
    for p in plots:
        by_run[p.parents[1].name].append(p)

    priority = (
        "learning_curves.png",
        "returns_by_episode.png",
        "eval_episode_diagnostics.png",
        "warmup_episode_diagnostics.png",
    )
    picked: list[Path] = []
    for pref in priority:
        for files in by_run.values():
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

    out = _OUT / "plots"
    for i, src in enumerate(picked[:limit]):
        theme, section = _tag_plot(src.name)
        run = src.parents[1].name
        dest = out / f"plot_{i:03d}_{theme}_{_short(src)}.png"
        how = _link_or_copy(src, dest)
        learn = "na"
        rl = run.lower()
        if any(k in rl for k in ("shutter_split", "vector_budget", "decoupled_dual_vector")):
            learn = "learning"
        elif any(k in rl for k in ("safe_mode_penalty", "model_size", "shutter_mpo", "mpo_t0")):
            learn = "not_learning"
        rows.append(
            Row(
                id=f"plot-{i:03d}",
                kind="plot",
                theme=theme,
                learning_label=learn,
                section_hint=section,
                source_repo_path=src.relative_to(_REPO).as_posix(),
                dest=dest.relative_to(_OUT).as_posix(),
                notes=f"{how}; run={run}",
            )
        )
    return rows


def _read_meta(path: Path) -> tuple[cv2.VideoCapture, int, float]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {path}")
    last = max(int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) - 1, 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    return cap, last, fps


def _extract_neighbors(
    video: Path,
    *,
    center_frac: float,
    n_neighbors: int,
    frames_dir: Path,
    id_prefix: str,
    theme: str,
    section: str,
    learning_label: str,
    notes: str,
) -> list[Row]:
    assert n_neighbors in (3, 5, 7)
    cap, last, fps = _read_meta(video)
    center = int(round(center_frac * last))
    half = n_neighbors // 2
    stride = max(1, int(round(0.02 * last)))
    indices = [max(0, min(last, center + (k - half) * stride)) for k in range(n_neighbors)]
    uniq: list[int] = []
    seen: set[int] = set()
    for i in indices:
        if i not in seen:
            seen.add(i)
            uniq.append(i)

    rows: list[Row] = []
    frames_dir.mkdir(parents=True, exist_ok=True)
    for j, fi in enumerate(uniq):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ok, bgr = cap.read()
        if not ok or bgr is None:
            continue
        t_s = fi / fps if fps > 0 else 0.0
        fname = f"{id_prefix}_n{j:02d}_of_{len(uniq):02d}_f{fi:06d}_t{t_s:06.1f}s.png"
        dest = frames_dir / fname
        cv2.imwrite(str(dest), bgr)
        rows.append(
            Row(
                id=f"{id_prefix}-{j:02d}",
                kind="frame",
                theme=theme,
                learning_label=learning_label,
                section_hint=section,
                source_repo_path=video.relative_to(_REPO).as_posix(),
                dest=dest.relative_to(_OUT).as_posix(),
                notes=f"{notes}; neighbor {j+1}/{len(uniq)}; frame={fi}",
            )
        )
    cap.release()
    return rows


def _attach_source(
    video: Path,
    source_dir: Path,
    theme: str,
    learning_label: str,
    notes: str,
    *,
    dest_name: str | None = None,
) -> Row | None:
    if not video.exists():
        return None
    # Unique name: run folder + original filename (avoids eval_best.mp4 collisions)
    if dest_name is None:
        run_hint = video.parents[1].name if video.parent.name == "videos" else video.stem
        dest_name = f"{run_hint}__{video.name}"
    dest = source_dir / dest_name
    how = _link_or_copy(video, dest)
    pointer = source_dir / f"{Path(dest_name).stem}.SOURCE.txt"
    pointer.write_text(
        f"repo_path: {video.relative_to(_REPO).as_posix()}\n"
        f"absolute: {video.resolve().as_posix()}\n"
        f"link_mode: {how}\n"
        f"notes: {notes}\n",
        encoding="utf-8",
    )
    return Row(
        id=f"src-{_short(dest)}",
        kind="source_video",
        theme=theme,
        learning_label=learning_label,
        section_hint="na",
        source_repo_path=video.relative_to(_REPO).as_posix(),
        dest=dest.relative_to(_OUT).as_posix(),
        notes=f"{how}; {notes}",
    )


def build_themes() -> list[Row]:
    rows: list[Row] = []
    themes = _OUT / "themes"

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

    # 01 targets
    t1 = themes / "01_target_placement"
    if baseline.exists():
        r = _attach_source(baseline, t1 / "source", "static-target-placement", "na", "baseline overflight")
        if r:
            rows.append(r)
        for frac, tag in [(0.15, "early"), (0.35, "approach"), (0.50, "mid"), (0.75, "late")]:
            rows += _extract_neighbors(
                baseline,
                center_frac=frac,
                n_neighbors=3,
                frames_dir=t1 / "frames",
                id_prefix=f"targets-{tag}",
                theme="static-target-placement",
                section="Introduction / Methods",
                learning_label="na",
                notes=f"baseline corridor ({tag})",
            )

    # 02 clouds
    t2 = themes / "02_cloud_motion"
    cloud_src = baseline_vec if baseline_vec.exists() else baseline
    if cloud_src.exists():
        r = _attach_source(cloud_src, t2 / "source", "dynamic-cloud-generation", "na", "cloud motion source")
        if r:
            rows.append(r)
        if baseline.exists() and baseline != cloud_src:
            r2 = _attach_source(baseline, t2 / "source", "dynamic-cloud-generation", "na", "alt baseline")
            if r2:
                rows.append(r2)
        for frac, n, tag in [(0.30, 5, "early5"), (0.45, 5, "mid5"), (0.55, 7, "mid7"), (0.70, 5, "late5")]:
            rows += _extract_neighbors(
                cloud_src,
                center_frac=frac,
                n_neighbors=n,
                frames_dir=t2 / "frames",
                id_prefix=f"clouds-{tag}",
                theme="dynamic-cloud-generation",
                section="Methods",
                learning_label="na",
                notes="cloud field neighbor series",
            )

    # 03 safety
    t3 = themes / "03_safety_maneuver"
    safety_attached: set[str] = set()
    for label, vid, frac in [
        ("ref0", torque_eval, 0.40),
        ("ref0b", torque_eval, 0.60),
        ("safe-pen", safe_mode_eval, 0.35),
        ("safe-penb", safe_mode_eval, 0.55),
        ("mpo-torque", torque_mpo, 0.45),
    ]:
        if not vid.exists():
            continue
        key = vid.resolve().as_posix()
        if key not in safety_attached:
            r = _attach_source(
                vid, t3 / "source", "dynamic-safety-maneuver", "not_learning", f"safety scout {label}"
            )
            if r:
                rows.append(r)
            safety_attached.add(key)
        rows += _extract_neighbors(
            vid,
            center_frac=frac,
            n_neighbors=5,
            frames_dir=t3 / "frames",
            id_prefix=f"safety-{label}",
            theme="dynamic-safety-maneuver",
            section="Methods / Discussion",
            learning_label="not_learning",
            notes="torque-mode safety scout cycle",
        )

    # 04 selective shutter (learning behaviour)
    t4 = themes / "04_selective_shutter"
    if sac_best.exists():
        r = _attach_source(sac_best, t4 / "source", "behaviour-selective-shutter", "learning", "Exp9 SAC eval_best")
        if r:
            rows.append(r)
        for frac, tag in [(0.20, "a"), (0.40, "b"), (0.60, "c"), (0.80, "d")]:
            rows += _extract_neighbors(
                sac_best,
                center_frac=frac,
                n_neighbors=3,
                frames_dir=t4 / "frames",
                id_prefix=f"shutter-{tag}",
                theme="behaviour-selective-shutter",
                section="Results",
                learning_label="learning",
                notes="Exp9 selective shutter stills",
            )

    # 05 learning vs not learning (sensible: paired stills + curves already in plots/)
    t5 = themes / "05_learning_vs_not"
    pairs = [
        (
            "learning",
            "Exp9 SAC shutter-split (eval +106)",
            _REPO
            / "backend"
            / "autonomous_control"
            / "runs"
            / "9998217165798903_ml_sac_shutter_split_15-43-20"
            / "videos"
            / "eval_best.mp4",
            [0.25, 0.50, 0.75],
        ),
        (
            "learning",
            "Exp11 MPO vector (eval +45.5)",
            _REPO
            / "backend"
            / "autonomous_control"
            / "runs"
            / "9998217142297111_ml_mpo_decoupled_dual_vector_sparse_22-15-02"
            / "videos"
            / "eval_best.mp4",
            [0.30, 0.55, 0.75],
        ),
        (
            "learning",
            "Exp7 SAC vector budget (first positive)",
            _REPO
            / "backend"
            / "autonomous_control"
            / "runs"
            / "9998217172220712_ml_sac_vector_budget_13-56-17"
            / "videos"
            / "eval_best.mp4",
            [0.35, 0.60],
        ),
        (
            "not_learning",
            "Exp1 MPO shutter threshold (flat fail)",
            _REPO
            / "backend"
            / "autonomous_control"
            / "runs"
            / "9998217254656575_ml_shutter_mpo_t09_15-02-22"
            / "videos"
            / "eval_best.mp4",
            [0.30, 0.55, 0.75],
        ),
        (
            "not_learning",
            "Exp5 MPO width collapse",
            _REPO
            / "backend"
            / "autonomous_control"
            / "runs"
            / "9998217218692971_ml_mpo_model_size_mpo_s_01-01-46"
            / "videos"
            / "eval_best.mp4",
            [0.30, 0.55, 0.75],
        ),
        (
            "not_learning",
            "Exp10 safe-mode penalty (worst)",
            safe_mode_eval,
            [0.30, 0.55, 0.75],
        ),
    ]
    for learn_lab, desc, vid, fracs in pairs:
        if not vid.exists():
            continue
        r = _attach_source(vid, t5 / "source", "learning-vs-not", learn_lab, desc)
        if r and not any(x.dest == r.dest for x in rows):
            rows.append(r)
        # also copy matching learning_curves if present
        run_dir = vid.parents[1]
        curve = run_dir / "plots" / "learning_curves.png"
        if curve.exists():
            dest = t5 / "frames" / f"curve_{learn_lab}_{run_dir.name[:40]}_{_short(curve)}.png"
            how = _link_or_copy(curve, dest)
            rows.append(
                Row(
                    id=f"lvn-curve-{_short(curve)}",
                    kind="plot",
                    theme="learning-vs-not",
                    learning_label=learn_lab,
                    section_hint="Results",
                    source_repo_path=curve.relative_to(_REPO).as_posix(),
                    dest=dest.relative_to(_OUT).as_posix(),
                    notes=f"{how}; {desc}",
                )
            )
        for k, frac in enumerate(fracs):
            rows += _extract_neighbors(
                vid,
                center_frac=frac,
                n_neighbors=3,
                frames_dir=t5 / "frames",
                id_prefix=f"lvn-{learn_lab}-{k}",
                theme="learning-vs-not",
                section="Results / Discussion",
                learning_label=learn_lab,
                notes=desc,
            )

    return rows


def write_docs(rows: list[Row]) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    csv_path = _OUT / "MANIFEST.csv"
    md_path = _OUT / "MANIFEST.md"
    readme = _OUT / "README.md"

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()))
        w.writeheader()
        for r in rows:
            w.writerow(asdict(r))

    by_theme: dict[str, int] = defaultdict(int)
    by_kind: dict[str, int] = defaultdict(int)
    by_learn: dict[str, int] = defaultdict(int)
    for r in rows:
        by_theme[r.theme] += 1
        by_kind[r.kind] += 1
        by_learn[r.learning_label] += 1

    md = [
        "# Raw image selection manifest",
        "",
        f"Generated: `{stamp}`",
        f"Total entries: **{len(rows)}**",
        "",
        "## By kind",
        "",
        "| Kind | Count |",
        "|------|------:|",
    ]
    for k, n in sorted(by_kind.items()):
        md.append(f"| `{k}` | {n} |")
    md += ["", "## By theme", "", "| Theme | Count |", "|-------|------:|"]
    for k, n in sorted(by_theme.items(), key=lambda kv: -kv[1]):
        md.append(f"| `{k}` | {n} |")
    md += ["", "## Learning label", "", "| Label | Count |", "|-------|------:|"]
    for k, n in sorted(by_learn.items()):
        md.append(f"| `{k}` | {n} |")
    md += [
        "",
        "## Theme folders",
        "",
        "| Folder | Purpose |",
        "|--------|---------|",
        "| `themes/01_target_placement/` | static target corridor |",
        "| `themes/02_cloud_motion/` | dynamic cloud neighbor series |",
        "| `themes/03_safety_maneuver/` | torque safety cycle scouts |",
        "| `themes/04_selective_shutter/` | learned selective shutter |",
        "| `themes/05_learning_vs_not/` | learning vs not-learning paired stills + curves |",
        "",
        "Each theme has `frames/` and `source/` (MP4 hardlink/copy + `*.SOURCE.txt` pointer).",
        "",
        "To re-pick frames: open the source MP4, note time, re-run extract or adjust this script.",
        "",
    ]
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    readme.write_text(
        "\n".join(
            [
                "# Raw image selection",
                "",
                "Working pool of report visuals (plots + video frames + source MP4s).",
                "Not yet the final LaTeX `figures/` set — promote winners after review.",
                "",
                "See `MANIFEST.md` / `MANIFEST.csv`.",
                "",
                "Regenerate:",
                "",
                "```powershell",
                "conda activate auto-sat",
                "python docs/raw_image_selection/populate_raw_image_selection.py",
                "```",
                "",
                "## Learning vs not learning",
                "",
                "Included under `themes/05_learning_vs_not/`: paired eval stills and learning curves",
                "from Exp 7/9/11 (learning) vs Exp 1/5/10 (not learning). Sensible for Results/Discussion",
                "contrast without new experiments.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = {
        "generated_utc": stamp,
        "n_entries": len(rows),
        "by_kind": dict(by_kind),
        "by_theme": dict(by_theme),
        "by_learning_label": dict(by_learn),
        "out": _OUT.relative_to(_REPO).as_posix(),
    }
    (_OUT / "MANIFEST_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def main() -> None:
    _OUT.mkdir(parents=True, exist_ok=True)
    rows: list[Row] = []
    rows += collect_plots(limit=120)
    rows += build_themes()
    write_docs(rows)
    n_frames = sum(1 for r in rows if r.kind == "frame")
    n_plots = sum(1 for r in rows if r.kind == "plot")
    n_vid = sum(1 for r in rows if r.kind == "source_video")
    if n_frames + n_plots < 100:
        raise SystemExit(f"Too few image artifacts: frames={n_frames} plots={n_plots}")
    print(f"ok: plots={n_plots} frames={n_frames} source_videos={n_vid} total={len(rows)}")


if __name__ == "__main__":
    main()
