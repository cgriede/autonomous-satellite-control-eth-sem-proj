"""Run directory naming: newest-first sort prefix."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from utils.ml_training.ml_training_utils import (
    create_run_dir,
    experiment_name_from_run_slug,
    format_run_dir_name,
    format_experiment_name,
    has_run_sort_prefix,
    list_run_dirs_for_slug,
    make_run_id,
    remove_run_dirs_for_slug,
    resolve_run_dir,
    run_naming_core,
    run_slug_from_dir_name,
    run_sort_prefix,
)


def test_run_naming_core_strips_prefix_timestamp_and_ml() -> None:
    assert run_naming_core("ml_shutter_mpo_t09_15-02-22") == "shutter_mpo_t09"
    assert (
        run_naming_core("9998217254656575_ml_shutter_mpo_t09_15-02-22")
        == "shutter_mpo_t09"
    )
    assert run_naming_core("ml_overnight_h4_sac_00-28-52") == "overnight_h4_sac"
    assert run_naming_core("ml_overnight_h0_dt_1.5s") == "overnight_h0_dt_1.5s"


def test_experiment_name_from_run_slug() -> None:
    assert experiment_name_from_run_slug("ml_shutter_mpo_t09_15-02-22") == "shutter mpo t09"
    assert format_experiment_name("shutter_mpo_t05") == "shutter mpo t05"


def test_newer_run_sorts_before_older() -> None:
    t_old = datetime(2026, 1, 1, tzinfo=timezone.utc)
    t_new = datetime(2026, 6, 29, tzinfo=timezone.utc)
    old_name = make_run_id(slug="probe", now=t_old)
    new_name = make_run_id(slug="probe", now=t_new)
    assert has_run_sort_prefix(old_name)
    assert has_run_sort_prefix(new_name)
    assert new_name < old_name
    assert run_slug_from_dir_name(new_name) == "probe"


def test_sort_prefix_decreases_over_time() -> None:
    earlier = run_sort_prefix(datetime(2026, 6, 1, tzinfo=timezone.utc))
    later = run_sort_prefix(datetime(2026, 6, 2, tzinfo=timezone.utc))
    assert later < earlier


def test_create_run_dir_applies_prefix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("utils.ml_training.ml_training_utils.RUNS_ROOT", tmp_path)
    run_dir = create_run_dir(run_id="ml_test_arm")
    assert run_dir.is_dir()
    assert has_run_sort_prefix(run_dir.name)
    assert run_slug_from_dir_name(run_dir.name) == "ml_test_arm"


def test_resolve_and_remove_by_slug(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("utils.ml_training.ml_training_utils.RUNS_ROOT", tmp_path)
    fixed_now = datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
    older = tmp_path / format_run_dir_name("ml_smoke", now=fixed_now)
    newer = tmp_path / format_run_dir_name(
        "ml_smoke",
        now=datetime(2026, 6, 29, 13, 0, 0, tzinfo=timezone.utc),
    )
    older.mkdir()
    newer.mkdir()

    resolved = resolve_run_dir("ml_smoke")
    assert resolved == newer
    assert list_run_dirs_for_slug("ml_smoke") == [newer, older]

    remove_run_dirs_for_slug("ml_smoke")
    assert not older.exists()
    assert not newer.exists()
