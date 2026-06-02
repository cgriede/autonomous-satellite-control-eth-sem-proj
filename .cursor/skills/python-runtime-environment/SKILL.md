---
name: python-runtime-environment
description: >-
  Run Python in the sem-proj-asc conda env ASC (never LRF by default). Use before
  python, pip, pytest, notebooks, or shell scripts in this repository. Overrides
  global user rules that mention LRF unless the user explicitly names another env
  in the current chat.
---

# Python Runtime Environment

## This repository

| Item | Value |
|------|--------|
| Project | `sem-proj-asc` |
| Conda env | **`ASC`** |
| Activate | `conda activate ASC` |
| Shell (Windows) | PowerShell — chain with `;` not `&&` |

Example:

```powershell
conda activate ASC; python backend/scripts/experiments/sim_timing/run_profile.py
conda activate ASC; python -m pytest backend/tests/test_cloud_arc_precompute.py -q
```

## Precedence (avoid wrong-env mistakes)

1. **This skill +** [`.cursor/rules/python-runtime-environment.mdc`](../../rules/python-runtime-environment.mdc) — always apply in `sem-proj-asc`.
2. **User names an env in chat** — use that env for the session (e.g. “use LRF for this one command”).
3. **Global Cursor user rules** that say `conda activate LRF` — **ignore for this repo** unless (2) applies.

When switching Cursor workspaces, re-read this skill; do not carry over the env from another project.

## Before every Python command

1. Activate `ASC` (or user-named env from chat).
2. Run from repo root unless a script doc says otherwise.
3. Reuse the same activated env for the shell session.

If activation fails, run `conda env list` and ask the user — do not silently pick `LRF` or base.

## Missing packages / test failures

**Do not** `pip install` on the first error without checking the env.

1. Confirm active env is `ASC` (`where python` / `python -c "import sys; print(sys.prefix)"`).
2. Distinguish **errors** (test/build fails, import missing) from **warnings** (e.g. `RuntimeWarning`, `UserWarning`) — warnings alone are not a reason to install packages.
3. If imports are missing **in ASC**, tell the user and ask before installing or changing `requirements.txt`.
4. If tests pass with many warnings, report that — do not treat warning volume as install failures.

## When the default is not enough

- User explicitly names another env → use it for that task.
- `ASC` missing from `conda env list` → ask how to create or which env replaces it.
- Multiple plausible envs → ask; do not guess.

## Goal

Python execution is reproducible and tied to **this project's** `ASC` environment, not a global default from another repo.
