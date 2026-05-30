# Example — OCR Calibration Cleanup

One worked example. Inputs were two commit hashes produced by another agent running [.cursor/skills/minimal-feature-cycle/SKILL.md](../minimal-feature-cycle/SKILL.md) on time-axis OCR calibration: `ed7888d` and `392e751`.

## Phase 0 (the one we missed)

`git status` at review start showed 100+ unrelated paths: a layout migration of `backend/scripts/`, untracked notebook directories, miscellaneous training-run manifests. None of it was related to the calibration commits being reviewed.

We did not run Phase 0. Consequence:

- Focused cleanup commit landed cleanly (`b36385d`).
- Notebook archive commit landed cleanly (`0a4ff65`).
- `git pull` then collided with a remote Elliott-wave refactor that had moved `pipeline/analysis_image.py` -> `analysis_image.py` and archived `base_data_ocr_parse.py`.
- The mixed working tree turned a 1-conflict merge into 6 conflicts (modify/delete on three test files, content conflict in `analysis_image_extractor.py`, two unrelated module deletions).
- Resolving took ~20 minutes; reproducing it cleanly would have taken ~2 minutes.

After the cleanup shipped, the user surfaced the lesson: *"we should have just committed the unrelated file moves first before running our thing"*. The late `2ec8c6d` chore commit finally absorbed the working-tree noise.

This example is why Phase 0 exists in SKILL.md.

## Phase 1 — Frame

`git show ed7888d --stat` and `git show 392e751 --stat` named the changed files. The candidate list that surfaced from reading the diffs:

- New `VerificationDatetimeResolution` dataclass in `backend/notebooks/utils/calibration_display.py` with 5 fields, used in exactly one function.
- Hardcoded `FIXTURES` list in `backend/automation/process_analysis_data/tests/test_axis_calibration.py` alongside a fresh `axis_calibration/*.json` directory carrying richer metadata — the JSON files were the obvious canonical source.
- Duplicate `parse_timeframe` helper in the new notebook that reimplemented `_normalize_timeframe + TimeFrame` from production.
- `parse_calibration_datetime` had not been exercised against the real OCR header shape (`Jun 10, 2025 12:21 UTC+2`).

The assumptions surfaced to the user:

1. OCR header datetime, when present, should be honoured (not silently dropped to fallback).
2. `axis_calibration/*.json` is intended as canonical fixture metadata.

Both confirmed.

## Phase 2 — Clarifying questions

One AskQuestion round, three items:

- Backward compatibility: **none** (allow breaking internal API renames).
- Notebook scope: keep the notebook with its current outputs as evidence, rerun once after the refactor to verify identical output.
- Datetime fallback policy: fallback to a verification-default datetime but require an explicit metadata flag plus a warning string.

The user also renamed `default datetime` -> `verification datetime` mid-conversation; the new vocabulary propagated through the whole rename.

## Phase 3 — Minimal refactor (net line count discipline)

Initial pass landed +36 lines. The user pushed back: *"This is a notebook utility module, not a production API."* The dataclass was over-engineered for a single consumer.

Simplified pass: drop `VerificationDatetimeResolution`, return a 4-tuple `(dt_utc, raw_text, fallback_used, warning)`. Push the fallback flag and warning into the existing `meta` dict directly. Net delta dropped to +13.

Final refactor surface:

| Change | File | Direction |
|---|---|---|
| `VerificationDatetimeResolution` dataclass removed | `calibration_display.py` | -16 |
| 4-tuple return + meta dict fields | `calibration_display.py` | +3 |
| `validation_dt_*` -> `verification_dt_*` rename | `calibration_display.py` + 2 notebooks + 2 test files | net 0 |
| `_UTC_NAMED_OFFSET_RE` + normalisation | `analysis_image_extractor.py` | +9 |
| Hardcoded `FIXTURES` -> JSON glob loader | `test_axis_calibration.py` | -90 / +20 |
| `parse_timeframe` notebook helper removed | minimal-feature-cycle notebook | -8 |

Net negative once the JSON fixture migration absorbed the dataclass cost.

## Phase 4 — Debug

Two failures came up.

**The `UTC+2` POSIX bug.** A new assertion in `test_parse_calibration_datetime` parsed `"Jun 10, 2025 12:21 UTC+2"` and expected `10:21 UTC`. Initial test failed at `14:21 UTC`. Hypothesis: `dateutil` interprets named `UTC+N` offsets with POSIX semantics. Confirmed by reading dateutil docs; fix was a single regex normalising `UTC+N` -> `+0N:00` before `isoparse`. The test then matched. Bug had been latent on disk; the review surfaced it.

**The stale-kernel false positive.** After the rename landed, the user ran the notebook and Cell 10 raised `TypeError: build_calibration_display_data() got an unexpected keyword argument 'verification_dt_fallback_utc'`. Three hypotheses:

- H-A: Jupyter kernel cached the pre-rename module in `sys.modules`.
- H-B: `StrReplace` wrote to a path Python did not resolve from.
- H-C: An `importlib.reload` was missing in the cell that mattered.

Confirmation procedure: `git show HEAD:backend/notebooks/utils/calibration_display.py | grep verification_dt_fallback_utc` returned 13 hits. Code on disk was correct. H-A confirmed; H-B, H-C, H-D rejected. Fix: kernel restart, not a code change.

This is the canonical example for the stale-kernel section in [reference.md](reference.md).

## Phase 5 — Ship

- Targeted pytest: 38/38 changed-module tests passed. Two unrelated pre-existing failures (`extract_result` attribute error) noted as out-of-scope.
- Human UX walkthrough: re-ran the notebook end-to-end after kernel restart; all 5 calibration overlays rendered identically to pre-refactor outputs.
- Notebook archived: `backend/notebooks/minimal_feature_cycle/eliott_wave_extractor_calibration_time_classification.ipynb` -> `archive/` subdirectory, recorded in commit message that human review passed.
- One production-ready cleanup commit (`b36385d`), one archive commit (`0a4ff65`), one late `chore:` commit (`2ec8c6d`) that should have been Phase 0.

## Takeaways for the skill

- Phase 0 is non-negotiable; the worked example proved its absence is expensive.
- Line count negotiation with the user mid-refactor is healthy. The first cut was +36; the final cut was net-negative. Asking "do we actually need this type?" twice saved 23 lines.
- A failing test on the new shape is information, not a barrier. The `UTC+2` test surfaced a latent bug in the code being reviewed.
- Stale-kernel errors look like signature mismatches. Always confirm disk state with `git show` before suspecting the rename.
