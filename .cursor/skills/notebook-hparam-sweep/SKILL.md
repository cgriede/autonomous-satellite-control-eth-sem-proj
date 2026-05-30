---
name: notebook-hparam-sweep
description: >-
  Run a hyperparameter calibration sweep for an LRF extraction notebook (FibTunables
  or any dataclass tunables) without nbconvert overhead. Writes a disposable Python
  sweep script, executes it via `conda activate LRF`, reads the JSON results, updates
  the notebook tunables cell with the winning config, and produces a structured
  accuracy-vs-recall report. Use when the user asks to tune, calibrate, sweep, or
  benchmark hyperparameters in a notebook extraction pipeline; or says "run configs",
  "find best config", or "hyperparameter tuning".
disable-model-invocation: true
---

# Notebook Hyperparameter Sweep

## Context

- **Tunables dataclass**: `FibTunables` in `backend/notebooks/eliott_wave_extractor/v2_config.py`
- **Metrics**: `aggregate_staged_metrics`, `pipeline_throughput_kpis`, `validation_dataframe` in `fib_v2_metrics.py`
- **Sweep harness already exists**: `v2_param_sweep.run_v2_param_sweep` + grids in `v2_param_sweep.py` — use it for grid sweeps; write a bespoke script for targeted rounds
- **Shell**: PowerShell on Windows — use `;` not `&&`; run as `conda activate LRF; cd backend; python ...`

## Clarifying questions (ask before starting)

1. **Primary metric + tie-breaker** — e.g. "rank by `correct_enough_rate`; tie-break `wrong_data_rate`; exclude `ok_count=0` from accuracy ranking."
2. **Budget** — max configs, max wall time, and whether to stop early if a threshold is met.
3. **Baseline numbers** — ask for or re-run one baseline config to anchor comparisons.
4. **Allowed edit surface** — confirm which parameters are in scope (only `FibTunables`? which fields?) and whether a disposable `_sweep.py` is OK.
5. **Early-stop target** — must be sanity-checked: if the baseline is 0 zones the 95% target is unreachable by tuning alone; flag this immediately.
6. **"Accuracy" definition** — when `correct_enough = 0` everywhere, clarify that "accuracy" means lowest `wrong_data_rate` among configs with `ok_count ≥ 1`, not "smallest error on silent configs."

## Workflow

### 1. Write `_tune_sweep_run.py` (disposable)

Place in the same folder as the notebook. Key structure:

```python
# cwd setup — backend root on sys.path
# BASE = FibTunables(...) # starting point
# CONFIGS: list[tuple[str, FibTunables]] = [...]
# for name, tunables in CONFIGS:
#     v2_rows, stage_stats = fx.run_extraction(run_entries, tunables)
#     fx.apply_hardening_pass(v2_rows, tunables)
#     m = aggregate_staged_metrics(v2_rows, ...)
#     tp = pipeline_throughput_kpis(v2_rows)
#     # collect + print one-liner; early-stop check
# write _tune_sweep_results_<round>.json
```

Always set `ocr_debug_print=False` in sweep configs for speed and clean logs.

### 2. Execution (PowerShell)

```powershell
conda activate LRF; cd c:\Users\cedri\code\LRF\backend; python notebooks/eliott_wave_extractor/_tune_sweep_run.py
```

`block_until_ms` ≈ `n_configs × ~45s × 1.15` — set enough buffer.

### 3. Analysis strategy

Run **two rounds**:
- **Round 1 (broad)**: vary one dominant lever per group (OCR PSM, scan color, zone assembly). 10–13 configs. Identify the active lever — look at `ocr_levels_pct_of_optimal` as the first gate; if it's < 30% nothing downstream can save it.
- **Round 2 (focused)**: 10–12 configs around the winning lever axis only. Grid the 1–2 params that actually moved the needle.

**Known finding for fib extraction (as of 2025-05-24):**
- `ocr_psm=11` is the dominant lever (+60 pp OCR throughput vs `psm=6`).
- `use_loose_for_pipeline` was a no-op (`loose_only_line_matches=0`); do not waste configs on it unless the regex changes.
- Scan/zone params (`scan_hue_tol`, `zone_span_tol_px`, `scan_dark_*`) have near-zero effect when OCR is the bottleneck.
- Lowering `ocr_min_conf` (15 vs 20) and `ocr_right_min_x_frac` (0.30 vs 0.35) adds recall but increases `wrong_data_rate` proportionally.

### 4. Update notebook

Edit the `FibTunables(...)` block directly in the `.ipynb` JSON using `StrReplace` on the raw source lines — `EditNotebook` is fragile if cell structure has shifted. Then clean up `_tune_sweep_run.py` and result JSONs.

## Report template

Deliver two configs: **best recall** and **best accuracy (among producers)**:

```
## Best recall — <config_name>

| KPI | Value |
|-----|-------|
| zones_pct_of_optimal | X% |
| ocr_levels_pct_of_optimal | X% |
| coverage_annotated | X |
| ok_count | N |
| wrong_data_rate_annotated | X |
| correct_enough_count_annotated | N |

Tunables: ...

## Best accuracy (lowest wrong_data_rate, ok_count ≥ 1) — <config_name>

| KPI | Value |
...

## Full results table (top N of M)

| Config | zones_% | ocr_% | span_% | cov_ann | ok | wrong_rate | correct_enough |
...

## Bottleneck diagnosis

Stage-by-stage: where the funnel collapses and whether it is a code issue vs tunable.

## What did NOT help (stop tuning these)

- ...
```

## Code improvement signals to report

If throughput plateaus with good OCR but poor zones, flag these as **code** issues — not tunable:

- `use_loose_for_pipeline` is a no-op → regex / line-join improvement needed
- Span→zone clustering dropping levels → inspect `zone_avg_conf_min` gate vs `span_confidence` values
- `correct_enough = 0` with zones present → ratio/price normalization or label-matching logic
- Any stage where wider tolerances *reduce* throughput → likely a sorting/ordering bug

## Constraints

- Only modify the `FibTunables(...)` block in the notebook (lines scoped by user). Never touch extraction logic or metrics code.
- Prefer no-signal over wrong signal: disqualify configs with `precision_floor_any_extra_zones = True` from accuracy rank.
- Archive sweep scripts and JSONs after update (delete them); do not commit to git.
