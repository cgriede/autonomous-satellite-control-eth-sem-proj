---
name: debug-workflow
description: >-
  Workspace debugging conventions (debug logs, probe placement). Use whenever in
  debug mode, when prompted to debug anything, or when adding runtime logging probes.
---

# Debug Workflow

## Debug log location

**Always** write probe logs under **`.cursor/debug_logs/`** at the workspace (repo) root.

**Never** write to the repo root, `backend/`, notebook folders, or any other working directory — even if a debug-mode prompt names a path like `debug-<sessionId>.log` at the project root. Remap that filename into `.cursor/debug_logs/`.

```python
import json
import time
from pathlib import Path

# From backend/simulation/foo.py → parents[2] is repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_log = _REPO_ROOT / ".cursor" / "debug_logs" / "<topic>.log"
_log.parent.mkdir(parents=True, exist_ok=True)
_log.open("a", encoding="utf-8").write(
    json.dumps({"sessionId": "<id>", "ts": int(time.time() * 1000), ...}) + "\n"
)
```

Replace `parents[N]` so `_REPO_ROOT` is the directory that contains `.cursor/` and `backend/`. Common cases:

| File location | `N` (parents) |
|---------------|----------------|
| `backend/simulation/*.py` | 2 |
| `backend/scripts/*.py` | 2 |
| `backend/notebooks/...` (resolve from notebook path) | varies — count up to repo root |

For notebooks, resolve `N` from the notebook file path, not from `Path.cwd()`.

Use a **topic** filename per investigation (e.g. `reward-kernel-1a7e56.log`), not a bare `debug.log` in the repo root.

`.cursor/debug_logs/` is gitignored; safe to append during debug sessions.

## Leading-space import error

**Symptom:** `ModuleNotFoundError: No module named ' scripts'` (space before `scripts`).

**Cause:** Launch config or subprocess arg has a stray leading space: `"-m', ' scripts.daily_operations"`.

**Fix:** Remove the leading space from the `module` field in `launch.json`, or from the subprocess list:

```python
# correct
cmd = [sys.executable, "-m", "scripts.update_prices"]
# broken
cmd = [sys.executable, "-m", " scripts.update_prices"]
```

If the terminal `python -m scripts.daily_operations --help` works but the debug launcher fails — it is always the launch config string, not the code.
