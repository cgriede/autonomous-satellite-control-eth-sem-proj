---
name: minimal-feature-cycle-notebook-simplify
description: Simplify an oversized minimal-feature notebook until a human can grasp it in one pass. Extract hardened verification, setup, and display into local modules beside the notebook; leave only reload-and-run cells for the code under development. Use when a notebook has grown past ~500 lines or ~8 code cells with definitions, the user says the notebook is bloated or hard to follow, or Phase 2 drifted into a monolithic ipynb.
---

# Notebook simplify (minimal-feature-cycle subskill)

Parent: [SKILL.md](SKILL.md). Apply **during or after Phase 2** when the notebook is the iteration surface but no longer readable as a controller.

## When to run

Treat the notebook as **too large for one human read** if any of these hold:

| Signal | Typical threshold |
|--------|-------------------|
| File size | `.ipynb` **> ~500 lines** (often mostly outputs) or **> ~1.5k lines** even after clearing outputs |
| Code cells | **> ~8** code cells, or **> ~3** cells that each define functions |
| Definitions in notebook | `grep` / search finds **`def `** in multiple cells (helpers duplicated across cells) |
| Verification baked in | Metrics tables, sweep grids, or overlay drawing **reimplemented** in the notebook instead of imported |
| Operator confusion | User says they cannot see what to edit, what is “the algorithm”, or what is “just checks” |

If only outputs are huge: **clear outputs first**, re-check. If still unwieldy, run this subskill.

**Do not** run on notebooks that are already thin controllers (cwd + config + `reload` + one call + verification imports).

## Outcome

A notebook a human can scan in **under two minutes**:

1. Cwd setup (template cell — do not delete)
2. Config + load data (`run_entries`, paths, tunables)
3. **`reload(<iteration_module>)` + run extraction** ← only cell that changes daily
4. Verification (metrics, table, plots) — import only, no logic
5. Optional: audit export, param sweep, cleanup

Target: **~10–15 cells**, **no `def`** in the notebook except cwd helper.

## Classify before moving

For each code cell, assign **one** bucket:

| Bucket | Move to | Notebook keeps |
|--------|---------|----------------|
| **Iteration** (algorithm under dev) | `<notebook_dir>/<feature>_extraction.py` or similar | `reload` + one call |
| **Setup / IO** | `<notebook_dir>/…_run_context.py`, `…_config.py` | config instance + `load_*()` |
| **Verification** (metrics, validation df, aggregates) | existing metrics module or `…_verification.py` | `print_*` / `display(df)` |
| **Display** (matplotlib, overlays) | `backend/notebooks/utils/` or `…_display.py` | loop or `show_*_batch(...)` |
| **Artifacts** (export PNG/JSON/manifest) | `…_audit_export.py` if already present | 5–10 line call |
| **Tuning harness** (param sweep) | `…_param_sweep.py` | commented example + one-liner |

**Logic vs UX** (same as parent Phase 5): business logic → `automation/...` only after promotion; until then keep iteration modules **next to the notebook** under `backend/notebooks/<workspace>/`.

## Extraction rules

1. **Move, do not rewrite behavior** in the first pass — same functions, dataclass tunables instead of scattered globals when helpful.
2. **One iteration module** — the file the developer edits (`fib_extraction.py`, not three parallel copies).
3. **Deduplicate** — if verification reimplements `_num_key` / match counts already in a metrics module, delete notebook copy; call `validation_dataframe()` (or add it there once).
4. **Stale imports** — after folder renames, grep `notebooks.ocr_analysis_extraction` (or old package names) and fix to the current package.
5. **Clear notebook outputs** when rewriting the ipynb JSON so git diffs stay reviewable.
6. **`importlib.reload`** on modules the operator edits (`reload(fx)` before `run_extraction`).

### Suggested local module set (adapt names)

```
backend/notebooks/<workspace>/
  <feature>.ipynb          # thin controller
  <feature>_config.py      # V2FibRunConfig, FibTunables
  <feature>_run_context.py # RunEntry, load_run_entries
  <feature>_extraction.py  # run_extraction — iteration target
  <feature>_verification.py
  <feature>_display.py     # optional
  <feature>_param_sweep.py # optional
```

Worked example: `backend/notebooks/eliott_wave_extractor/V2-fib-box-extraction.ipynb` + `fib_extraction.py`, `v2_config.py`, `v2_run_context.py`, `v2_verification.py`, `fib_v2_display.py`, `v2_param_sweep.py`.

## Notebook template after simplify

```python
# config + load
from notebooks.<workspace>.<feature>_config import V2FibRunConfig
from notebooks.<workspace>.<feature>_run_context import load_run_entries, print_load_summary
cfg = V2FibRunConfig(...)
run_entries, failures, paths = load_run_entries(cfg, db_session=db_session)
```

```python
# iterate
from importlib import reload
from notebooks.<workspace> import <feature>_extraction as fx
reload(fx)
v2_rows, stats = fx.run_extraction(run_entries, cfg.tunables)
```

```python
# verify
from importlib import reload
from notebooks.<workspace> import <feature>_verification as vv
reload(vv)
vv.print_metrics_summary(v2_rows, stats, ...)
display(vv.print_validation_table(v2_rows)[cols])
```

## Validation after simplify

- [ ] `json.load` on the `.ipynb` succeeds
- [ ] Imports resolve from `backend/` cwd (notebook cell 1)
- [ ] Existing unit tests for extracted helpers still pass (`pytest` on `test_*` scripts if present)
- [ ] No `def ` left in notebook except cwd helper
- [ ] Human can name the **one file** to edit for algorithm changes

## Anti-patterns

- Splitting into ten tiny modules without a clear iteration target
- Leaving verification logic in the notebook “because it’s hardened”
- Promoting to `automation/` before the API stabilizes (local modules first)
- Deleting sweep/export cells instead of moving to optional tail cells

## When done

Return to parent [SKILL.md](SKILL.md) Phase 2–3: notebook stays thin; new behavior gets unit tests beside the extracted module, not new notebook cells.
