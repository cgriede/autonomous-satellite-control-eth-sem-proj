from __future__ import annotations

import sys
from pathlib import Path


# Ensure tests can import top-level backend modules (simulation, autonomous_control, etc.)
# when pytest is launched from the repository root.
BACKEND_DIR = Path(__file__).resolve().parents[1]
backend_path = str(BACKEND_DIR)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
