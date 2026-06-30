"""Load/save frozen SimulationStateSeries fixtures (no simulation imports)."""

from __future__ import annotations

import gzip
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np

FIXTURES_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"

FIXTURE_FILES: dict[str, str] = {
    "training_sparse": "training_sparse_episode.pkl.gz",
    "high_cloud": "high_cloud_notebook.pkl.gz",
    "gate": "gate_minimal.pkl.gz",
}


def assert_renderable(series: Any) -> None:
    n_bins = int(series.camera_observation_line_codes.shape[1])
    if n_bins < 1:
        raise ValueError(f"series must have n_bins >= 1, got {n_bins}")
    sim_total_s = float(series.metadata.sim_total_s)
    if not np.isfinite(sim_total_s) or sim_total_s <= 0.0:
        raise ValueError(f"metadata.sim_total_s must be finite and > 0, got {sim_total_s}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_series_fixture(path: Path, series: Any) -> dict[str, Any]:
    """Pickle series to gzip; return manifest entry fields."""
    assert_renderable(series)
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb", compresslevel=6) as gz:
        pickle.dump(series, gz, protocol=pickle.HIGHEST_PROTOCOL)
    n_steps = int(series.camera_observation_line_codes.shape[0])
    n_clouds = int(series.cloud_arc_radius_km.shape[1])
    n_bins = int(series.camera_observation_line_codes.shape[1])
    return {
        "path": path.name,
        "sha256_hex": _sha256_file(path),
        "n_sim_steps": n_steps,
        "sim_total_s": float(series.metadata.sim_total_s),
        "n_bins": n_bins,
        "n_clouds": n_clouds,
        "bytes": int(path.stat().st_size),
    }


def load_series_fixture_file(path: Path) -> Any:
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Fixture not found: {path}")
    with gzip.open(path, "rb") as gz:
        series = pickle.load(gz)
    assert_renderable(series)
    return series


def _read_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(
            f"Fixture manifest missing: {MANIFEST_PATH}. "
            "Run bake_series_fixtures.py --all first."
        )
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def read_manifest() -> dict[str, Any]:
    return _read_manifest()


def load_frozen_series(fixture_id: str) -> Any:
    """Load a committed fixture by id; verify SHA256 when manifest present."""
    if fixture_id not in FIXTURE_FILES:
        raise KeyError(f"Unknown fixture_id {fixture_id!r}; choose from {list(FIXTURE_FILES)}")
    rel_name = FIXTURE_FILES[fixture_id]
    path = FIXTURES_DIR / rel_name
    manifest = _read_manifest()
    entries = manifest.get("fixtures") or {}
    entry = entries.get(fixture_id)
    if entry is not None:
        expected = entry.get("sha256_hex")
        if expected:
            actual = _sha256_file(path)
            if actual != expected:
                raise ValueError(
                    f"Fixture {fixture_id} SHA256 mismatch: expected {expected}, got {actual}"
                )
    return load_series_fixture_file(path)


def write_manifest(
    fixtures: dict[str, dict[str, Any]],
    *,
    baked_from: str,
    export_frames: dict[str, dict[str, int]] | None = None,
) -> Path:
    payload: dict[str, Any] = {
        "baked_from": baked_from,
        "fixtures": fixtures,
    }
    if export_frames:
        for fixture_id, frames in export_frames.items():
            if fixture_id in fixtures:
                fixtures[fixture_id].update(frames)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return MANIFEST_PATH


def compute_export_frame_counts(sim_total_s: float) -> dict[str, int]:
    from environment_definition.constants import RENDER, SIMULATION
    from environment_definition.constants.UNIT_REGISTRY import UREG

    export_speed_multiplier = float(SIMULATION.export_speed_multiplier)
    anim_ms = RENDER.animation_interval.to(UREG.ms).magnitude
    dt_sim_s = (anim_ms / 1000.0) * export_speed_multiplier
    stride_1 = max(2, int(np.ceil(float(sim_total_s) / dt_sim_s)) + 1)
    stride = max(1, int(RENDER.export_frame_stride))
    indices = list(range(0, stride_1, stride))
    if indices[-1] != stride_1 - 1:
        indices.append(stride_1 - 1)
    return {
        "export_frames_stride_1": int(stride_1),
        "export_frames_stride_2": len(indices),
    }
