#!/usr/bin/env python3
"""
Extract PNG frames from an MP4 for agent vision inspection.

Outputs land under ``.cursor/video_frame_inspect/data/<run_id>/`` with a manifest
the agent can read, then open individual PNGs via the Read tool.

Usage (conda env ASC)::

    python .cursor/tools/video_frame_inspect/extract_frames.py PATH/to/video.mp4 --count 6
    python .cursor/tools/video_frame_inspect/extract_frames.py video.mp4 --sim-steps 0,1148,2522 --sim-n-steps 2523
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

# Repo root = parents[3] from this file (.cursor/tools/video_frame_inspect/extract_frames.py)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DATA_ROOT = _REPO_ROOT / ".cursor" / "video_frame_inspect" / "data"

# Matches render export in render/render_main.py::save_one_pass_video_30x (defaults).
_DEFAULT_ANIMATION_INTERVAL_MS = 50.0
_DEFAULT_EXPORT_SPEED_MULTIPLIER = 30.0


@dataclass(frozen=True)
class ExtractedFrame:
    frame_index: int
    time_s: float
    filename: str
    sim_step: int | None = None
    label: str | None = None


@dataclass(frozen=True)
class ExtractionManifest:
    video_path: str
    run_id: str
    output_dir: str
    fps: float
    frame_count: int
    duration_s: float
    width: int
    height: int
    extracted_at_utc: str
    frames: tuple[ExtractedFrame, ...]
    notes: str | None = None


def _parse_int_list(raw: str | None) -> list[int]:
    if not raw:
        return []
    out: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return out


def _parse_float_list(raw: str | None) -> list[float]:
    if not raw:
        return []
    out: list[float] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        out.append(float(part))
    return out


def _sanitize_run_id(stem: str) -> str:
    cleaned = re.sub(r"[^\w.\-]+", "_", stem).strip("_")
    return cleaned or "video"


def _video_frame_count(cap: cv2.VideoCapture) -> int:
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if n > 0:
        return n
    # Some codecs report 0; count by seeking (slower fallback).
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    count = 0
    while True:
        ok, _ = cap.read()
        if not ok:
            break
        count += 1
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    return count


def _sim_step_to_video_frame(
    sim_step: int,
    *,
    sim_n_steps: int,
    sim_total_s: float,
    animation_interval_ms: float,
    export_speed_multiplier: float,
) -> int:
    """Map simulation step index → export video frame (render EXPORT pipeline)."""
    if sim_n_steps < 2:
        raise ValueError("sim_n_steps must be >= 2")
    if sim_total_s <= 0.0:
        raise ValueError("sim_total_s must be > 0")
    dt_sim_s = (animation_interval_ms / 1000.0) * export_speed_multiplier
    export_num_frames = max(2, int(np.ceil(sim_total_s / dt_sim_s)) + 1)
    normalized = float(np.clip(sim_step / (sim_n_steps - 1), 0.0, 1.0))
    sim_t = normalized * sim_total_s
    frame = int(round(sim_t / dt_sim_s))
    return int(np.clip(frame, 0, export_num_frames - 1))


def _percent_to_frame(percent: float, *, last_frame: int) -> int:
    p = float(np.clip(percent, 0.0, 100.0))
    return int(round(p / 100.0 * last_frame))


def _evenly_spaced_frames(count: int, *, last_frame: int) -> list[int]:
    if count < 1:
        raise ValueError("--count must be >= 1")
    if count == 1:
        return [0]
    return [int(round(i * last_frame / (count - 1))) for i in range(count)]


def _read_frame_at(cap: cv2.VideoCapture, frame_index: int) -> np.ndarray:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
    ok, bgr = cap.read()
    if not ok or bgr is None:
        raise RuntimeError(f"Failed to read frame {frame_index}")
    return bgr


def _unique_sorted(indices: list[int], *, last_frame: int) -> list[int]:
    clipped = [int(np.clip(i, 0, last_frame)) for i in indices]
    return sorted(set(clipped))


def extract_frames(
    video_path: Path,
    *,
    output_dir: Path | None = None,
    frame_indices: list[int] | None = None,
    percents: list[float] | None = None,
    count: int | None = None,
    sim_steps: list[int] | None = None,
    sim_n_steps: int | None = None,
    sim_total_s: float | None = None,
    animation_interval_ms: float = _DEFAULT_ANIMATION_INTERVAL_MS,
    export_speed_multiplier: float = _DEFAULT_EXPORT_SPEED_MULTIPLIER,
    labels: dict[int, str] | None = None,
    run_id: str | None = None,
) -> ExtractionManifest:
    video_path = video_path.resolve()
    if not video_path.is_file():
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV could not open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = _video_frame_count(cap)
    last_frame = max(0, frame_count - 1)
    duration_s = (frame_count / fps) if fps > 0 else 0.0

    requested: list[tuple[int, int | None, str | None]] = []

    if sim_steps:
        if sim_n_steps is None or sim_total_s is None:
            raise ValueError("--sim-steps requires --sim-n-steps and --sim-total-s")
        for step in sim_steps:
            vf = _sim_step_to_video_frame(
                step,
                sim_n_steps=sim_n_steps,
                sim_total_s=sim_total_s,
                animation_interval_ms=animation_interval_ms,
                export_speed_multiplier=export_speed_multiplier,
            )
            requested.append((vf, step, labels.get(step) if labels else None))

    if frame_indices:
        for fi in frame_indices:
            requested.append((fi, None, labels.get(fi) if labels else None))

    if percents:
        for pct in percents:
            fi = _percent_to_frame(pct, last_frame=last_frame)
            requested.append((fi, None, labels.get(fi) if labels else f"pct_{pct:g}"))

    if count is not None:
        for fi in _evenly_spaced_frames(count, last_frame=last_frame):
            requested.append((fi, None, None))

    if not requested:
        requested = [(fi, None, None) for fi in _evenly_spaced_frames(6, last_frame=last_frame)]

    # Deduplicate by video frame; keep first sim_step / label association.
    by_frame: dict[int, tuple[int | None, str | None]] = {}
    for vf, sim_step, label in requested:
        if vf not in by_frame:
            by_frame[vf] = (sim_step, label)

    frames_to_write = _unique_sorted(list(by_frame.keys()), last_frame=last_frame)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rid = run_id or f"{_sanitize_run_id(video_path.stem)}_{stamp}"
    out_dir = (output_dir or (_DEFAULT_DATA_ROOT / rid)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted: list[ExtractedFrame] = []
    for vf in frames_to_write:
        sim_step, label = by_frame.get(vf, (None, None))
        bgr = _read_frame_at(cap, vf)
        time_s = (vf / fps) if fps > 0 else 0.0
        suffix = f"_sim{sim_step}" if sim_step is not None else ""
        label_suffix = f"_{_sanitize_run_id(label)}" if label else ""
        filename = f"frame_{vf:06d}_t{time_s:06.2f}s{suffix}{label_suffix}.png"
        out_path = out_dir / filename
        if not cv2.imwrite(str(out_path), bgr):
            cap.release()
            raise RuntimeError(f"Failed to write {out_path}")
        extracted.append(
            ExtractedFrame(
                frame_index=vf,
                time_s=float(time_s),
                filename=filename,
                sim_step=sim_step,
                label=label,
            )
        )

    cap.release()

    manifest = ExtractionManifest(
        video_path=str(video_path),
        run_id=rid,
        output_dir=str(out_dir),
        fps=fps,
        frame_count=frame_count,
        duration_s=duration_s,
        width=width,
        height=height,
        extracted_at_utc=datetime.now(timezone.utc).isoformat(),
        frames=tuple(extracted),
        notes=(
            "Open PNGs with the Read tool for vision inspection. "
            "sim_step mapping uses render EXPORT defaults "
            f"(animation_interval_ms={animation_interval_ms}, "
            f"export_speed_multiplier={export_speed_multiplier})."
        ),
    )
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(asdict(manifest), indent=2), encoding="utf-8")
    return manifest


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Extract PNG frames from MP4 for agent vision inspection.",
    )
    p.add_argument("video", type=Path, help="Path to input .mp4")
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: .cursor/video_frame_inspect/data/<run_id>)",
    )
    p.add_argument("--run-id", type=str, default=None, help="Subfolder name under data/")
    p.add_argument("--frames", type=str, default=None, help="Comma-separated video frame indices, e.g. 0,100,500")
    p.add_argument("--percent", type=str, default=None, help="Comma-separated percentages along timeline, e.g. 0,25,50,75,100")
    p.add_argument("--count", type=int, default=None, help="Extract N evenly spaced frames")
    p.add_argument("--sim-steps", type=str, default=None, help="Comma-separated simulation step indices (maps to video frames)")
    p.add_argument("--sim-n-steps", type=int, default=None, help="Total simulation steps (e.g. rollout series length)")
    p.add_argument("--sim-total-s", type=float, default=None, help="Episode sim duration in seconds (metadata.sim_total_s)")
    p.add_argument(
        "--animation-interval-ms",
        type=float,
        default=_DEFAULT_ANIMATION_INTERVAL_MS,
        help="RENDER.animation_interval in ms (default: 50)",
    )
    p.add_argument(
        "--export-speed-multiplier",
        type=float,
        default=_DEFAULT_EXPORT_SPEED_MULTIPLIER,
        help="SIMULATION.export_speed_multiplier (default: 30)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    manifest = extract_frames(
        args.video,
        output_dir=args.out,
        frame_indices=_parse_int_list(args.frames),
        percents=_parse_float_list(args.percent),
        count=args.count,
        sim_steps=_parse_int_list(args.sim_steps),
        sim_n_steps=args.sim_n_steps,
        sim_total_s=args.sim_total_s,
        animation_interval_ms=float(args.animation_interval_ms),
        export_speed_multiplier=float(args.export_speed_multiplier),
        run_id=args.run_id,
    )
    print(f"manifest={manifest.output_dir}/manifest.json")
    print(f"frames={len(manifest.frames)}  video_frames={manifest.frame_count}  fps={manifest.fps:.3f}")
    for fr in manifest.frames:
        sim = f" sim_step={fr.sim_step}" if fr.sim_step is not None else ""
        print(f"  {fr.filename}  (frame={fr.frame_index} t={fr.time_s:.2f}s{sim})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
