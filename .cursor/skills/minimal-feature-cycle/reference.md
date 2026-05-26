# Reference — Minimal Feature Cycle

Deep dive on the patterns named in SKILL.md. Read when the high-level rule isn't enough.

## Notebook-thin pattern

The notebook is a controller, not a library. Every cell either drives a function call into production code or describes intent.

Standard cell shape after the cwd setup:

```python
import your_module as _m
from importlib import reload
reload(_m)
from your_module import your_target
```

Why `reload`:

- Notebooks accumulate stale module state across cells. Without `reload`, edits in `your_module.py` don't take effect.
- `reload` only reloads the named module, not its dependencies. If you edit a deeper module, reload that one too.
- Frozen dataclasses and enums survive `reload` poorly. If you must mutate them in tests, use a fresh kernel instead.

Anti-patterns:

- Defining the function you're testing inside the notebook. It diverges from production silently.
- Copy-pasting "just for this cell". The diverged copy will outlive the cell.
- Keeping plotting helpers in the notebook. Promote them to `backend/notebooks/utils/`.

## Notebook simplify (subskill)

When Phase 2 produced a monolithic ipynb (> ~500 lines, multiple cells with `def`, verification logic inlined), follow [notebook-simplify.md](notebook-simplify.md): classify cells (iteration / setup / verification / display), extract to modules beside the notebook under `backend/notebooks/<workspace>/`, leave reload-and-run cells only. Real reference layout: `backend/notebooks/eliott_wave_extractor/` (`fib_extraction.py` = iteration target, `v2_verification.py` = hardened checks).

## Ground-truth independence

Fixtures encode a contract between the system and the world. The expected values must come from somewhere the system cannot reach.

Valid sources:

- Human measurement (operator reads a value off the artifact, types it into the fixture).
- Geometric or algebraic construction independent of the code under test.
- A sibling tool or older trusted implementation.

Invalid source:

- The current output of the code under test. The fixture locks whatever drift is present and pytest goes green forever.

Symptom that this rule was broken: pytest passes, but a human looking at the output says "that's obviously wrong".

## Three-gate validation model

| Gate | What it proves | What it cannot prove |
|------|----------------|----------------------|
| Unit | A pure function maps inputs to outputs as specified | The function is wired into the right caller |
| End-to-end with fixtures | Real inputs produce expected outputs end-to-end | Outputs look right to an operator |
| Human visual / artifact review | The artifact matches operator intent | Nothing — but it's the only gate that catches semantic drift |

Place each behaviour in exactly one home. Duplicated coverage wastes maintenance; a missing home is a regression waiting to ship.

## Instrumentation

When a hypothesis needs runtime evidence:

- Write NDJSON lines to `.cursor/debug_logs/debug-<sessionId>.log` (one JSON object per line).
- Never write debug logs to the repo root. Map any tool-provided root path into `.cursor/debug_logs/` and keep the filename.
- For notebook-triggered logging, resolve the output path from the notebook file directory, never from the active-cell CWD. If the notebook path is unavailable, require an explicit base-directory argument instead of falling back to `Path.cwd()`.
- Wrap each insertion in `# region agent log` / `# endregion` (or the equivalent for the language) so the editor folds it.
- Remove instrumentation only after post-fix verification confirms the fix; do not strip it during the fix attempt.

```python
from pathlib import Path

debug_dir = Path(repo_root) / ".cursor" / "debug_logs"
debug_dir.mkdir(parents=True, exist_ok=True)
debug_log_path = debug_dir / f"debug-{session_id}.log"
```

## Promotion checklist

When a notebook-only change is ready to graduate:

- [ ] The function lives in the package matching its responsibility (logic vs operator-facing UX).
- [ ] Imports across the codebase resolve to the new location; no shim left behind unless backward compatibility was explicitly requested.
- [ ] Unit tests cover the changed behaviour and at least one of the failures seen during Phase 4.
- [ ] End-to-end fixtures cover one sample per regime the change must support.
- [ ] Plotting and operator helpers live under `backend/notebooks/utils/`, not in the notebook.
- [ ] The notebook now imports the promoted helper; no parallel definition remains.

## Lifecycle moves

Plan files start in `.cursor/plans/00-initialized/` and move through `01-building/`, optionally `02-debugging-in-review/` and `03-targeted-tests/`, then `04-final-validation/`, and finally `99-archive/`.

Move the file when the stage you are in stops describing your activity. Do not rename across moves; the filename is the plan identity.

Human UX review section 4b:

- Always present in the plan, even when not applicable.
- When the change has an observable surface, complete the walkthrough and record what was inspected.
- When no surface exists, write one line: `Human UX review: N/A — <reason>`. Refactors behind a stable API are the common case.

## Common failure modes

- **Notebook drift**: helpers grow in the notebook, diverge from production, and bugs hide in the divergence. Catch by grepping for function definitions in `*.ipynb` cells before promote.
- **Self-referential fixtures**: expected values were copied from `cal.resolve(target)` or a similar call into the code under test. Catch by asking "where did this number come from?" for each fixture value.
- **Symptom patches**: a tolerance was widened, an exception was caught, a log was silenced. Catch by reading the diff with the question "what is this defending against?".
- **Plan files frozen in `01-building`**: the work is done but the file never moved. Catch at archive time; the plan stage should always reflect current activity.
