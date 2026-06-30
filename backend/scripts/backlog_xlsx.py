"""Compatibility shim — canonical tool: .cursor/tools/backlog/backlog_xlsx.py"""

from __future__ import annotations

import sys
from pathlib import Path

_TOOL_DIR = Path(__file__).resolve().parents[2] / ".cursor" / "tools" / "backlog"
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

from backlog_xlsx import *  # noqa: F403

if __name__ == "__main__":
    from backlog_xlsx import main

    raise SystemExit(main())
