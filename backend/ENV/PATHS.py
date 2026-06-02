"""Canonical filesystem paths for repo-local artifacts."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

BACKLOG_XLSX = _REPO_ROOT / "backlog.xlsx"
