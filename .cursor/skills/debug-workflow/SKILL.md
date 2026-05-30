---
name: debug-workflow
description: LRF debugging conventions. Use whenever in debug mode, when prompted to debug anything, or when adding runtime logging probes.
---

# Debug Workflow

## Debug log location

**Always** write probe logs to `.cursor/debug_logs/`. Never write to the repo root, `backend/`, or any other working directory.

```python
import json, time
from pathlib import Path
_log = Path(__file__).resolve().parents[N] / ".cursor/debug_logs/<topic>.log"
_log.parent.mkdir(parents=True, exist_ok=True)
_log.open("a").write(json.dumps({"ts": int(time.time()*1000), ...}) + "\n")
```

Replace `N` with the number of `parent` steps needed to reach the workspace root.  
For notebooks, resolve `N` from the notebook file path, not from `Path.cwd()`.

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
