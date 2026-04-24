"""Utilities for run directories, checkpoints, and run logs."""

from __future__ import annotations

import json
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

