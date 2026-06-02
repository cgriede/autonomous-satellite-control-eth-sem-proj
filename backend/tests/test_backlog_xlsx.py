"""Backlog workbook read/validate contract."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.backlog_xlsx import (
    assert_backlog_workbook_healthy,
    init_default_backlog,
    read_backlog_entries,
)


class BacklogXlsxTest(unittest.TestCase):
    def test_init_and_read_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "backlog.xlsx"
            init_default_backlog(path)
            assert_backlog_workbook_healthy(path)
            entries = read_backlog_entries(path)
            self.assertGreaterEqual(len(entries), 10)
            uids = {e["uid"] for e in entries}
            self.assertIn("FEAT-004", uids)
            self.assertIn("BUG-001", uids)


if __name__ == "__main__":
    unittest.main()
