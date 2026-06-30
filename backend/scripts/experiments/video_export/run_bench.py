"""Sim-free video export benchmark CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

from _runner_common import RESULTS_DIR, bench_video_export, load_frozen_series


def _default_workers() -> int:
    return min(os.cpu_count() or 4, 8)


def _load_export_patch(spec: str):
    if ":" in spec:
        module_name, attr = spec.split(":", 1)
    else:
        module_name, attr = spec, "patched_save"
    mod = importlib.import_module(module_name)
    return getattr(mod, attr)


def _run_isolated(args: argparse.Namespace) -> dict:
    out_path = args.out
    if out_path is None:
        raise ValueError("--out is required when using --isolate-gpu")
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--fixture",
        args.fixture,
        "--encoder",
        args.encoder,
        "--repeat",
        str(args.repeat),
        "--out",
        str(out_path),
        "--no-isolate-gpu",
    ]
    if args.export_patch:
        cmd.extend(["--export-patch", args.export_patch])
    if args.workers:
        cmd.extend(["--workers", str(args.workers)])
    env = os.environ.copy()
    if args.workers:
        env["VIDEO_EXPORT_WORKERS"] = str(args.workers)
    subprocess.run(cmd, cwd=str(EXPERIMENT_ROOT), env=env, check=True)
    return json.loads(out_path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark MP4 export on frozen fixtures")
    parser.add_argument(
        "--fixture",
        choices=("training_sparse", "high_cloud", "gate"),
        default="gate",
    )
    parser.add_argument("--encoder", choices=("ffmpeg", "mpl"), default="ffmpeg")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--workers", type=int, default=0, help="For parallel export patch")
    parser.add_argument("--export-patch", type=str, default=None, help="module:attr e.g. c_parallel_frames._export_fork:patched_save")
    parser.add_argument("--isolate-gpu", action="store_true", help="Run bench in subprocess (clean CUDA context)")
    parser.add_argument("--no-isolate-gpu", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--out", type=Path, default=None, help="JSON output path")
    args = parser.parse_args()

    if args.workers > 0:
        os.environ["VIDEO_EXPORT_WORKERS"] = str(args.workers)
    elif "VIDEO_EXPORT_WORKERS" not in os.environ and args.export_patch:
        os.environ["VIDEO_EXPORT_WORKERS"] = str(_default_workers())

    if args.isolate_gpu and not args.no_isolate_gpu:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        args.out = RESULTS_DIR / f"bench_{args.fixture}_{stamp}.json"
        _run_isolated(args)
        print(f"Wrote {args.out}")
        return

    series = load_frozen_series(args.fixture)
    patch = _load_export_patch(args.export_patch) if args.export_patch else None

    runs: list[dict] = []
    for _ in range(max(1, int(args.repeat))):
        out_mp4 = RESULTS_DIR / f"bench_{args.fixture}_preview.mp4"
        runs.append(
            bench_video_export(
                series,
                out_mp4,
                fixture_id=args.fixture,
                encoder=args.encoder,
                export_patch=patch,
            )
        )

    payload = {
        "fixture_id": args.fixture,
        "encoder": args.encoder,
        "export_patch": args.export_patch,
        "workers": int(os.environ.get("VIDEO_EXPORT_WORKERS", 0) or 0),
        "runs": runs,
        "export_wall_s_mean": sum(r["export_wall_s"] for r in runs) / len(runs),
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
