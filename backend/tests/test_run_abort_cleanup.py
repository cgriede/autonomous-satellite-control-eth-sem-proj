"""Abort stderr markers and aborted-run directory sweep."""

from __future__ import annotations

from pathlib import Path

from utils.ml_training.ml_training_utils import (
    ABORTED_RUNS_DIRNAME,
    RUN_ABORT_STDERR_FILENAME,
    is_run_aborted,
    run_has_substantive_artifacts,
    sweep_aborted_run_directories,
    write_run_abort_stderr,
)
from utils.ml_training.training_run_artifacts import write_config_snapshot


def test_successful_run_has_no_stderr_marker(tmp_path: Path) -> None:
    run_dir = tmp_path / "9999000000000001_ml_ok"
    run_dir.mkdir()
    assert not is_run_aborted(run_dir)


def test_abort_stderr_written_on_exception(tmp_path: Path) -> None:
    run_dir = tmp_path / "9999000000000002_ml_fail"
    run_dir.mkdir()
    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        path = write_run_abort_stderr(run_dir, exc)
    assert path.name == RUN_ABORT_STDERR_FILENAME
    text = path.read_text(encoding="utf-8")
    assert "RuntimeError" in text
    assert "boom" in text
    assert is_run_aborted(run_dir)


def test_substantive_artifacts_detects_episodes_csv(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    write_config_snapshot(run_dir, {"workflow": {"seed": 1}})
    assert not run_has_substantive_artifacts(run_dir)
    (run_dir / "episodes.csv").write_text("global_idx,phase\n0,train\n", encoding="utf-8")
    assert run_has_substantive_artifacts(run_dir)


def test_sweep_archives_partial_aborted_run(tmp_path: Path) -> None:
    run_dir = tmp_path / "9999000000000003_ml_partial"
    run_dir.mkdir()
    write_config_snapshot(run_dir, {"workflow": {"seed": 1}})
    (run_dir / "episodes.csv").write_text("global_idx,phase\n0,warmup\n", encoding="utf-8")
    write_run_abort_stderr(run_dir, RuntimeError("stopped"))

    result = sweep_aborted_run_directories(runs_root=tmp_path)
    assert len(result.archived) == 1
    assert not run_dir.exists()
    archived = tmp_path / ABORTED_RUNS_DIRNAME / run_dir.name
    assert archived.is_dir()
    assert (archived / RUN_ABORT_STDERR_FILENAME).is_file()


def test_sweep_removes_config_only_aborted_run(tmp_path: Path) -> None:
    run_dir = tmp_path / "9999000000000004_ml_empty"
    run_dir.mkdir()
    write_config_snapshot(run_dir, {"workflow": {"seed": 1}})
    write_run_abort_stderr(run_dir, RuntimeError("early"))

    result = sweep_aborted_run_directories(runs_root=tmp_path)
    assert len(result.removed) == 1
    assert not run_dir.exists()
    assert not (tmp_path / ABORTED_RUNS_DIRNAME).exists()


def test_sweep_skips_successful_runs(tmp_path: Path) -> None:
    run_dir = tmp_path / "9999000000000005_ml_success"
    run_dir.mkdir()
    write_config_snapshot(run_dir, {"workflow": {"seed": 1}})
    (run_dir / "episodes.csv").write_text("global_idx,phase\n0,train\n", encoding="utf-8")

    result = sweep_aborted_run_directories(runs_root=tmp_path)
    assert result.actions == ()
    assert run_dir.is_dir()
