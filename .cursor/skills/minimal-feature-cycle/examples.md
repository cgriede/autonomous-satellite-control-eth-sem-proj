# Examples — Minimal Feature Cycle

One worked cycle, cited for reference. Read when you need a concrete shape; do not generalise from this single case.

## ANA-OCR-TIME — timeframe-aware axis calibration

**Backlog framing:** propagate the distinction between `1M` (monthly) and `1m` (minute) through the calibration pipeline so per-chart fixtures resolve to the right pixel positions.

**Notebook (Phase 2):** [backend/notebooks/minimal_feature_cycle/eliott_wave_extractor_calibration_time_classification.ipynb](../../../backend/notebooks/minimal_feature_cycle/eliott_wave_extractor_calibration_time_classification.ipynb). Five cells: cwd setup, outline, feature build with `reload`, verification plan, pytest runner, plus a visual sign-off loop added because the change has an operator-visible surface.

**Promoted code (Phase 5):** [backend/automation/process_analysis_data/extractors/analysis_image_extractor.py](../../../backend/automation/process_analysis_data/extractors/analysis_image_extractor.py) — `_classify_time_axis_mode`, `_time_axis_line_looks_date_like`, `parse_calibration_datetime`.

**Promoted display helper:** [backend/notebooks/utils/calibration_display.py](../../../backend/notebooks/utils/calibration_display.py) — `build_calibration_display_data`, `display_calibrated_overlay`. Operator UX, so it stays under `notebooks/utils/`, not inside `automation/`.

**Tests (Phase 3):**

- Unit: [backend/automation/process_analysis_data/tests/test_analysis_image_extractor.py](../../../backend/automation/process_analysis_data/tests/test_analysis_image_extractor.py) (`test_classify_time_axis_mode`, `test_time_axis_line_looks_date_like`, `test_parse_calibration_datetime`).
- End-to-end fixtures: [backend/automation/process_analysis_data/tests/test_axis_calibration.py](../../../backend/automation/process_analysis_data/tests/test_axis_calibration.py) — one parametrized case per regime (`1M`, `2d`, `1d`, `4h`, `15m`).
- Display helper: [backend/tests/notebooks/test_calibration_display.py](../../../backend/tests/notebooks/test_calibration_display.py).
- Visual gate: notebook section 4 (overlay loop), confirmed by the user.

## Lesson — Phase 4 in practice

A fixture said `expected_x: 158.58` for the monthly chart. Pytest stayed green. The overlay placed the purple line near the year 2006 while the chart's publication date was 2025. Pytest was wrong because `expected_x` had been set to the output of `resolve()` itself.

The instrumentation pass (NDJSON to `.cursor/debug_logs/`) dumped the anchor list. One anchor was `text="V8 Tradingview 4 HKCM"` with `parsed_dt=2025-08-04T00:00:00+00:00` at `x_full=159`. The line-level dateutil fuzzy parse had turned the watermark text into a date, and that date plus its x became the brackets `resolve()` interpolated inside.

Source fix: reject OCR lines from the time-axis strip when they contain no year and no month token. The watermark is no longer eligible to become an anchor.

Fixture fix: `expected_x = 1214.12`, measured from the visible 2024 and 2026 anchors, independent of `resolve()`.

What did not happen: no tolerance was widened, no test was skipped, no fallback was added to mask the bad anchor. The fix is at the source and the failure mode is now unreachable.
