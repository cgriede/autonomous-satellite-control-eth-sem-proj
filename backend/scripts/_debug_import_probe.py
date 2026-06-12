"""Probe notebook import paths for camera_verification debug session."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

SESSION = "9fab0b"
LOG = Path(__file__).resolve().parents[2] / "debug-9fab0b.log"


def _log(hypothesis_id: str, message: str, data: dict) -> None:
    payload = {
        "sessionId": SESSION,
        "hypothesisId": hypothesis_id,
        "location": "_debug_import_probe.py",
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
        "runId": "pre-fix",
    }
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


backend_root = Path(__file__).resolve().parents[1]
_s01_dir = backend_root / "notebooks" / "s01"
sys.path.insert(0, str(backend_root))
sys.path.insert(0, str(_s01_dir))

_log(
    "H2-H5",
    "path_setup",
    {
        "backend_root": str(backend_root),
        "s01_dir": str(_s01_dir),
        "s01_on_syspath": str(_s01_dir) in sys.path,
        "top_level_file": (_s01_dir / "camera_verification.py").exists(),
        "pkg_file": (_s01_dir / "s01_utils" / "camera_verification.py").exists(),
        "s01_utils_init": (_s01_dir / "s01_utils" / "__init__.py").exists(),
    },
)

for name in ("camera_verification", "s01_utils", "s01_utils.camera_verification"):
    try:
        __import__(name)
        _log("H1-H3", "import_ok", {"module": name})
    except Exception as exc:
        _log("H1-H3", "import_fail", {"module": name, "error": f"{type(exc).__name__}: {exc}"})

print(f"probe complete -> {LOG}")
