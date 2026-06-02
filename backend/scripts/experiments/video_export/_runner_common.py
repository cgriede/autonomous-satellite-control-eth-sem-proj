"""Shared timing, codec probe, and fixed-contract JSON for video export experiments."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

from environment_definition.constants import RenderMode
from render.render_main import _resolve_ffmpeg_executable, render_from_series
from simulation.run_simulation import run_simulation

from _frozen_baseline import build_baseline_sim_config, build_high_cloud_setup

RESULTS_DIR = EXPERIMENT_ROOT / "results"


def _json_default(obj: Any) -> Any:
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Not JSON serializable: {type(obj)}")


def write_result(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")


def write_hypothesis_result(
    path: Path,
    *,
    experiment_id: str,
    hypothesis_id: str,
    phase: str,
    frozen_input: dict[str, Any],
    control: dict[str, Any] | None,
    treatment: dict[str, Any] | None,
    delta: dict[str, Any],
    parity: dict[str, Any],
    instrumentation: dict[str, Any],
    debug_examples: dict[str, Any],
    files_changed: list[str],
    verdict: str,
    closeout: str,
) -> None:
    payload = {
        "experiment_id": experiment_id,
        "hypothesis_id": hypothesis_id,
        "phase": phase,
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_input": frozen_input,
        "control": control,
        "treatment": treatment,
        "delta": delta,
        "parity": parity,
        "instrumentation": instrumentation,
        "debug_examples": debug_examples,
        "files_changed": files_changed,
        "verdict": verdict,
        "closeout": closeout,
    }
    write_result(path, payload)


def build_frozen_simulation_series():
    setup = build_high_cloud_setup()
    sim_cfg = build_baseline_sim_config()
    series = run_simulation(setup=setup, simulation_config=sim_cfg)
    return setup, series


def probe_video(path: Path) -> dict[str, Any]:
    p = path.resolve()
    info: dict[str, Any] = {
        "path": str(p),
        "exists": p.exists(),
        "bytes": int(p.stat().st_size) if p.exists() else 0,
        "codec": None,
        "width": None,
        "height": None,
        "duration_s": None,
    }
    if not p.exists():
        return info

    ffmpeg_exe, via = _resolve_ffmpeg_executable()
    if ffmpeg_exe is None:
        info["probe_via"] = "none"
        return info

    proc = subprocess.run(
        [ffmpeg_exe, "-hide_banner", "-i", str(p)],
        capture_output=True,
        text=True,
        check=False,
    )
    info["probe_via"] = via
    for line in proc.stderr.splitlines():
        if "Duration:" in line and info["duration_s"] is None:
            try:
                dur_token = line.split("Duration:", 1)[1].split(",", 1)[0].strip()
                h, m, s = dur_token.split(":")
                info["duration_s"] = float(h) * 3600.0 + float(m) * 60.0 + float(s)
            except (ValueError, IndexError):
                pass
        if "Video:" in line:
            chunk = line.split("Video:", 1)[1]
            info["codec"] = chunk.strip().split(",", 1)[0].strip()
            if "x" in chunk:
                for part in chunk.split(","):
                    part = part.strip()
                    if "x" in part and part[0].isdigit():
                        wh = part.split()[0]
                        w, h = wh.split("x", 1)
                        info["width"] = int(w)
                        info["height"] = int(h)
                        break
    return info


def bench_video_export(
    series,
    out_path: Path,
    *,
    export_patch: Callable[[Path | None], Path] | None = None,
    render_pre_hook: Callable[[], Callable[[], None]] | None = None,
) -> dict[str, Any]:
    """Time one MP4 export; optional ``export_patch`` replaces ``save_one_pass_video_30x``."""
    import render.render_main as render_mod

    out_path = Path(out_path).resolve()
    if out_path.exists():
        out_path.unlink()

    original_save = render_mod.save_one_pass_video_30x
    if export_patch is not None:
        render_mod.save_one_pass_video_30x = export_patch

    restore_render = render_pre_hook() if render_pre_hook is not None else None
    try:
        t0 = time.perf_counter()
        render_from_series(
            simulation_series=series,
            render_mode=RenderMode.EXPORT,
            output_path=out_path,
        )
        export_wall_s = time.perf_counter() - t0
    finally:
        render_mod.save_one_pass_video_30x = original_save
        if restore_render is not None:
            restore_render()

    video = probe_video(out_path)
    n_frames_drawn = None
    if export_patch is not None and hasattr(export_patch, "_last_n_frames_drawn"):
        n_frames_drawn = export_patch._last_n_frames_drawn

    from environment_definition.constants import RENDER, SIMULATION
    from environment_definition.constants.UNIT_REGISTRY import UREG

    export_speed_multiplier = float(SIMULATION.export_speed_multiplier)
    anim_ms = RENDER.animation_interval.to(UREG.ms).magnitude
    dt_sim_s = (anim_ms / 1000.0) * export_speed_multiplier
    sim_total_s = float(series.metadata.sim_total_s)
    baseline_frames = max(2, int(np.ceil(sim_total_s / dt_sim_s)) + 1)

    frames_per_s = (
        float(n_frames_drawn) / max(export_wall_s, 1e-9)
        if n_frames_drawn is not None
        else float(baseline_frames) / max(export_wall_s, 1e-9)
    )

    return {
        "export_wall_s": float(export_wall_s),
        "baseline_frame_count": int(baseline_frames),
        "n_frames_drawn": int(n_frames_drawn) if n_frames_drawn is not None else int(baseline_frames),
        "export_frames_per_s": float(frames_per_s),
        "video": video,
    }


def patch_lite_export_panels() -> tuple[dict[str, bool], Callable[[], None]]:
    """Context manager as factory: disable heavy dashboard panels for export-only runs."""
    import render.render_main as render_mod

    keys = (
        "SHOW_TELEMETRY",
        "SHOW_REWARD_PLOT",
        "SHOW_TORQUE_PLOT",
        "SHOW_1D_SAT_VIEW_SECONDARY",
    )
    saved = {k: bool(getattr(render_mod, k)) for k in keys}

    def apply() -> None:
        render_mod.SHOW_TELEMETRY = False
        render_mod.SHOW_REWARD_PLOT = False
        render_mod.SHOW_TORQUE_PLOT = False
        render_mod.SHOW_1D_SAT_VIEW_SECONDARY = False

    def restore() -> None:
        for k, v in saved.items():
            setattr(render_mod, k, v)

    apply()
    return saved, restore


def write_analysis_card(path: Path, *, hypothesis_id: str, json_path: Path) -> None:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    control = payload.get("control") or {}
    treatment = payload.get("treatment") or {}
    delta = payload.get("delta") or {}
    parity = payload.get("parity") or {}
    lines = [
        f"# Analysis — {hypothesis_id}",
        "",
        "## 1. Hypothesis",
        payload.get("frozen_input", {}).get("description", ""),
        "",
        "## 2. Frozen input",
        f"- Scenario: {payload.get('frozen_input', {}).get('scenario', '?')}",
        f"- Clouds: {payload.get('frozen_input', {}).get('n_items', '?')}",
        "",
        "## 3. Control KPI",
        f"- export_wall_s: {control.get('export_wall_s')}",
        f"- export_frames_per_s: {control.get('export_frames_per_s')}",
        f"- n_frames_drawn: {control.get('n_frames_drawn')}",
        "",
        "## 4. Treatment KPI",
        f"- export_wall_s: {treatment.get('export_wall_s')}",
        f"- export_frames_per_s: {treatment.get('export_frames_per_s')}",
        f"- n_frames_drawn: {treatment.get('n_frames_drawn')}",
        "",
        "## 5. Delta",
        f"- export_speedup: {delta.get('export_speedup')}",
        f"- relative_wall_reduction_pct: {delta.get('relative_wall_reduction_pct')}",
        "",
        "## 6. Parity",
        f"- passed: {parity.get('passed')}",
        f"- notes: {parity.get('notes')}",
        "",
        "## 7. Verdict",
        f"- {payload.get('verdict')}",
        "",
        "## 8. Closeout",
        payload.get("closeout", ""),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
