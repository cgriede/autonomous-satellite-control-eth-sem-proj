"""Utilities for run directories, checkpoints, and run logs."""

from __future__ import annotations

import json
import re
import shutil
import threading
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from paths import BACKEND_ROOT, RUNS_ROOT

# Reverse millisecond key so ascending sort lists newest runs first.
_SORT_PREFIX_WIDTH = 16
_MAX_SORT_KEY = 10**_SORT_PREFIX_WIDTH - 1
_SORT_PREFIX_RE = re.compile(rf"^\d{{{_SORT_PREFIX_WIDTH}}}_")
_RUN_TIMESTAMP_SUFFIX_RE = re.compile(r"_[0-9]{2}-[0-9]{2}-[0-9]{2}$")
_ML_RUN_PREFIX = "ml_"


def _coerce_utc(now: datetime) -> datetime:
    if now.tzinfo is None:
        return now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc)


def run_sort_prefix(now: datetime | None = None) -> str:
    """Fixed-width numeric prefix; smaller values are more recent."""
    ts = _coerce_utc(now if now is not None else datetime.now(tz=timezone.utc))
    remaining_ms = _MAX_SORT_KEY - int(ts.timestamp() * 1000)
    remaining_ms = max(0, min(remaining_ms, _MAX_SORT_KEY))
    return f"{remaining_ms:0{_SORT_PREFIX_WIDTH}d}"


def has_run_sort_prefix(name: str) -> bool:
    return bool(_SORT_PREFIX_RE.match(name))


def run_slug_from_dir_name(dir_name: str) -> str:
    if has_run_sort_prefix(dir_name):
        return dir_name[_SORT_PREFIX_WIDTH + 1 :]
    return dir_name


def run_naming_core(run_slug: str) -> str:
    """Run folder naming core: slug without sort prefix, ``ml_``, or launch timestamp."""
    slug = _sanitize_run_slug(run_slug)
    slug = _RUN_TIMESTAMP_SUFFIX_RE.sub("", slug)
    if slug.startswith(_ML_RUN_PREFIX):
        slug = slug[len(_ML_RUN_PREFIX) :]
    return slug or "run"


def format_experiment_name(naming_core: str) -> str:
    """Human-readable experiment label (spaces instead of underscores)."""
    return naming_core.replace("_", " ")


def experiment_name_from_run_slug(run_slug: str) -> str:
    """Display name for simulation info, derived from a run slug or directory name."""
    return format_experiment_name(run_naming_core(run_slug))


def _sanitize_run_slug(slug: str) -> str:
    cleaned = slug.strip().replace("/", "-").replace("\\", "-")
    if has_run_sort_prefix(cleaned):
        cleaned = run_slug_from_dir_name(cleaned)
    return cleaned or "run"


def format_run_dir_name(slug: str, *, now: datetime | None = None) -> str:
    """Directory name ``{sort_prefix}_{slug}`` with newest-first ordering."""
    return f"{run_sort_prefix(now)}_{_sanitize_run_slug(slug)}"


def make_run_id(*, slug: str = "run", now: datetime | None = None) -> str:
    return format_run_dir_name(slug, now=now)


def list_run_dirs_for_slug(slug: str) -> list[Path]:
    """All run directories whose slug matches ``slug`` (newest first)."""
    ensure_runs_root()
    target = _sanitize_run_slug(slug)
    matches = [
        path
        for path in RUNS_ROOT.iterdir()
        if path.is_dir() and run_slug_from_dir_name(path.name) == target
    ]
    return sorted(matches, key=lambda path: path.name)


def remove_run_dirs_for_slug(slug: str) -> None:
    for path in list_run_dirs_for_slug(slug):
        shutil.rmtree(path)


def ensure_runs_root() -> Path:
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    return RUNS_ROOT


ensure_models_root = ensure_runs_root


def create_run_dir(run_id: str | None = None, exist_ok: bool = False) -> Path:
    ensure_runs_root()
    if run_id is None:
        rid = make_run_id()
    elif has_run_sort_prefix(run_id):
        rid = run_id
    else:
        rid = format_run_dir_name(run_id)
    run_dir = RUNS_ROOT / rid
    run_dir.mkdir(parents=True, exist_ok=exist_ok)
    return run_dir


def resolve_run_dir(run_id: str) -> Path:
    """Resolve by full directory name or by slug (newest matching run)."""
    ensure_runs_root()
    direct = RUNS_ROOT / run_id
    if direct.is_dir():
        return direct
    matches = list_run_dirs_for_slug(run_id)
    if matches:
        return matches[0]
    return direct


def checkpoint_path(run_dir: Path, filename: str = "agent.pt") -> Path:
    return run_dir / filename


def run_log_path(run_dir: Path) -> Path:
    return run_dir / "run_log.md"


def aggregate_jsonl_path() -> Path:
    ensure_runs_root()
    return RUNS_ROOT / "runs.jsonl"


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


RUN_ABORT_STDERR_FILENAME = "stderr.txt"
ABORTED_RUNS_DIRNAME = "_aborted"
_RUN_SWEEP_SKIP_DIRNAMES = frozenset({ABORTED_RUNS_DIRNAME, "cached_warmup"})


def run_abort_stderr_path(run_dir: Path) -> Path:
    return run_dir / RUN_ABORT_STDERR_FILENAME


def is_run_aborted(run_dir: Path) -> bool:
    """True when the run directory contains an abort stderr marker."""
    return run_abort_stderr_path(run_dir).is_file()


def write_run_abort_stderr(run_dir: Path, exc: BaseException) -> Path:
    """Persist traceback for a non-clean workflow exit (successful runs omit this file)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_abort_stderr_path(run_dir)
    lines = [
        f"timestamp_utc: {datetime.now(tz=timezone.utc).isoformat()}",
        f"exception_type: {type(exc).__name__}",
        f"exception_message: {exc}",
        "",
        "traceback:",
        traceback.format_exc(),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def aborted_runs_archive_root(runs_root: Path | None = None) -> Path:
    root = runs_root if runs_root is not None else RUNS_ROOT
    return root / ABORTED_RUNS_DIRNAME


def _run_log_has_events(run_log: Path) -> bool:
    if not run_log.is_file():
        return False
    text = run_log.read_text(encoding="utf-8")
    if "## Events" not in text:
        return False
    after = text.split("## Events", 1)[1].strip()
    return any(line.startswith("###") for line in after.splitlines())


def _episodes_csv_has_rows(episodes_csv: Path) -> bool:
    if not episodes_csv.is_file() or episodes_csv.stat().st_size == 0:
        return False
    lines = [line for line in episodes_csv.read_text(encoding="utf-8").splitlines() if line.strip()]
    return len(lines) > 1


def _telemetry_has_training_events(events_path: Path) -> bool:
    if not events_path.is_file():
        return False
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            return True
        if record.get("event") not in ("run_started",):
            return True
    return False


def run_has_substantive_artifacts(run_dir: Path) -> bool:
    """True when a run produced training data or exports beyond bare config scaffolding."""
    if not run_dir.is_dir():
        return False
    if _run_log_has_events(run_log_path(run_dir)):
        return True
    if _episodes_csv_has_rows(run_dir / "episodes.csv"):
        return True
    if checkpoint_path(run_dir).is_file():
        return True
    if (run_dir / "summary_metrics.json").is_file():
        return True
    if (run_dir / "artifacts_manifest.json").is_file():
        return True
    for sub in ("plots", "episodes", "videos"):
        media_dir = run_dir / sub
        if not media_dir.is_dir():
            continue
        for path in media_dir.iterdir():
            if path.is_file() and path.suffix.lower() in {".png", ".mp4", ".gif", ".webm"}:
                return True
    tensorboard = run_dir / "tensorboard"
    if tensorboard.is_dir():
        for path in tensorboard.rglob("events.out.tfevents.*"):
            if path.is_file() and path.stat().st_size > 0:
                return True
    if _telemetry_has_training_events(telemetry_events_path(run_dir)):
        return True
    return False


def iter_run_directories(runs_root: Path | None = None) -> list[Path]:
    """Top-level ML run directories (newest first), excluding archive/cache roots."""
    root = ensure_runs_root() if runs_root is None else runs_root
    matches = [
        path
        for path in root.iterdir()
        if path.is_dir() and path.name not in _RUN_SWEEP_SKIP_DIRNAMES
    ]
    return sorted(matches, key=lambda path: path.name)


@dataclass(frozen=True)
class AbortedRunSweepAction:
    run_dir: Path
    action: Literal["archived", "removed", "skipped"]
    detail: str


@dataclass(frozen=True)
class AbortedRunSweepResult:
    actions: tuple[AbortedRunSweepAction, ...]

    @property
    def archived(self) -> list[AbortedRunSweepAction]:
        return [item for item in self.actions if item.action == "archived"]

    @property
    def removed(self) -> list[AbortedRunSweepAction]:
        return [item for item in self.actions if item.action == "removed"]

    @property
    def skipped(self) -> list[AbortedRunSweepAction]:
        return [item for item in self.actions if item.action == "skipped"]


def _unique_archive_destination(archive_root: Path, run_name: str) -> Path:
    archive_root.mkdir(parents=True, exist_ok=True)
    candidate = archive_root / run_name
    if not candidate.exists():
        return candidate
    stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return archive_root / f"{run_name}_{stamp}"


def sweep_aborted_run_directories(
    *,
    runs_root: Path | None = None,
    archive_root: Path | None = None,
    dry_run: bool = False,
) -> AbortedRunSweepResult:
    """Archive aborted runs with partial artifacts; delete config-only aborted runs."""
    root = ensure_runs_root() if runs_root is None else runs_root
    archive = archive_root if archive_root is not None else aborted_runs_archive_root(root)
    actions: list[AbortedRunSweepAction] = []

    for run_dir in iter_run_directories(root):
        if not is_run_aborted(run_dir):
            continue
        if run_has_substantive_artifacts(run_dir):
            dest = _unique_archive_destination(archive, run_dir.name)
            if not dry_run:
                shutil.move(str(run_dir), str(dest))
            actions.append(
                AbortedRunSweepAction(
                    run_dir=run_dir,
                    action="archived",
                    detail=str(dest),
                )
            )
        else:
            if not dry_run:
                shutil.rmtree(run_dir)
            actions.append(
                AbortedRunSweepAction(
                    run_dir=run_dir,
                    action="removed",
                    detail="config-only aborted run",
                )
            )

    return AbortedRunSweepResult(actions=tuple(actions))
