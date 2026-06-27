"""Utilities for run directories, checkpoints, and run logs."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import MODELS_ROOT


def make_run_id(now: datetime | None = None) -> str:
    ts = now if now is not None else datetime.now(tz=timezone.utc)
    return ts.strftime("%Y-%m-%d_%H-%M-%S")


def ensure_models_root() -> Path:
    MODELS_ROOT.mkdir(parents=True, exist_ok=True)
    return MODELS_ROOT


def create_run_dir(run_id: str | None = None) -> Path:
    ensure_models_root()
    rid = run_id or make_run_id()
    run_dir = MODELS_ROOT / rid
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def resolve_run_dir(run_id: str) -> Path:
    return MODELS_ROOT / run_id


def checkpoint_path(run_dir: Path, filename: str = "agent.pt") -> Path:
    return run_dir / filename


def run_log_path(run_dir: Path) -> Path:
    return run_dir / "run_log.md"


def aggregate_jsonl_path() -> Path:
    ensure_models_root()
    return MODELS_ROOT / "runs.jsonl"


def append_jsonl_record(record: dict[str, Any]) -> None:
    path = aggregate_jsonl_path()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, separators=(",", ":")) + "\n")


def init_run_markdown(run_dir: Path, *, title: str, metadata: dict[str, Any]) -> Path:
    path = run_log_path(run_dir)
    lines = [f"# {title}", "", "## Metadata", ""]
    for key, value in metadata.items():
        lines.append(f"- {key}: `{value}`")
    lines += ["", "## Events", ""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def append_run_markdown_event(run_dir: Path, heading: str, payload: dict[str, Any]) -> None:
    path = run_log_path(run_dir)
    lines = [f"### {heading}", ""]
    for key, value in payload.items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def telemetry_dir(run_dir: Path) -> Path:
    path = run_dir / "telemetry"
    path.mkdir(parents=True, exist_ok=True)
    return path


def telemetry_events_path(run_dir: Path) -> Path:
    return telemetry_dir(run_dir) / "events.jsonl"


def telemetry_latest_path(run_dir: Path) -> Path:
    return telemetry_dir(run_dir) / "latest.json"


def telemetry_step_path(run_dir: Path) -> Path:
    return telemetry_dir(run_dir) / "current_step.json"


class RunTelemetryWriter:
    """Thread-safe JSONL + latest snapshot writer for live polling UIs."""

    def __init__(self, run_dir: Path) -> None:
        self._run_dir = run_dir
        self._events_path = telemetry_events_path(run_dir)
        self._latest_path = telemetry_latest_path(run_dir)
        self._step_path = telemetry_step_path(run_dir)
        self._lock = threading.Lock()

    def _write_event(self, payload: dict[str, Any]) -> None:
        with self._events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, separators=(",", ":")) + "\n")

    def _write_latest(self, payload: dict[str, Any]) -> None:
        self._latest_path.write_text(
            json.dumps(payload, separators=(",", ":"), indent=2),
            encoding="utf-8",
        )

    def on_run_started(self, *, metadata: dict[str, Any]) -> None:
        record = {
            "event": "run_started",
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
            "run_dir": str(self._run_dir),
            **metadata,
        }
        with self._lock:
            self._write_event(record)
            self._write_latest(record)

    def on_worker_status(self, *, worker_id: int, status: str, episode_idx: int | None = None) -> None:
        record = {
            "event": "worker_status",
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
            "worker_id": int(worker_id),
            "status": str(status),
            "episode_idx": None if episode_idx is None else int(episode_idx),
        }
        with self._lock:
            self._write_event(record)

    def on_episode_finished(
        self,
        *,
        phase: str,
        episode_idx: int,
        episode_return: float,
        steps: int,
        episodes_per_second: float | None,
        rolling_return_mean: float | None,
    ) -> None:
        record = {
            "event": "episode_finished",
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
            "phase": str(phase),
            "episode_idx": int(episode_idx),
            "episode_return": float(episode_return),
            "steps": int(steps),
            "episodes_per_second": None if episodes_per_second is None else float(episodes_per_second),
            "rolling_return_mean": None if rolling_return_mean is None else float(rolling_return_mean),
        }
        with self._lock:
            self._write_event(record)
            self._write_latest(record)

    def on_step_snapshot(
        self,
        *,
        episode_idx: int,
        step_idx: int,
        sim_time_s: float,
        reward: float,
        worker_id: int | None = None,
        episode_return: float | None = None,
        phase: str | None = None,
        done: bool | None = None,
        capture_budget_remaining: int | None = None,
        safe_mode_activations: int | None = None,
    ) -> None:
        record = {
            "event": "step_snapshot",
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
            "episode_idx": int(episode_idx),
            "step_idx": int(step_idx),
            "sim_time_s": float(sim_time_s),
            "reward": float(reward),
            "worker_id": None if worker_id is None else int(worker_id),
        }
        if episode_return is not None:
            record["episode_return"] = float(episode_return)
        if phase is not None:
            record["phase"] = str(phase)
        if done is not None:
            record["done"] = bool(done)
        if capture_budget_remaining is not None:
            record["capture_budget_remaining"] = int(capture_budget_remaining)
        if safe_mode_activations is not None:
            record["safe_mode_activations"] = int(safe_mode_activations)
        with self._lock:
            self._write_event(record)
            self._write_latest(record)
            self._step_path.write_text(
                json.dumps(record, separators=(",", ":"), indent=2),
                encoding="utf-8",
            )

    def on_training_log(
        self,
        *,
        message: str,
        mode: str | None = None,
        episode_idx: int | None = None,
    ) -> None:
        record = {
            "event": "training_log",
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
            "message": str(message),
        }
        if mode is not None:
            record["phase"] = str(mode)
        if episode_idx is not None:
            record["episode_idx"] = int(episode_idx)
        with self._lock:
            self._write_event(record)

