# Worked Example — Integrating the Minimal-Feature-Cycle Skill

A real sweep run after `.cursor/skills/minimal-feature-cycle/` was created. Used as illustration of the rubric and the extract-then-delete-then-trim sequence. Skim, do not copy verbatim — the file lists are specific to that sweep.

## Setup

- New skill: `.cursor/skills/minimal-feature-cycle/` covered a five-phase backend notebook workflow (scope → notebook prototype → validation → root-cause → promote).
- User goal: "reduce global model context by invoking the skill only when needed; reference the skill or extract logic + delete redundant".
- Pre-sweep state: 60 files across `.cursor/rules/`, `.cursor/memory/`, `.cursor/dev_process/`.

## Phase 1 — Scope and approach

AskQuestion with two scoping questions:

1. Scope: user chose **all three** trees.
2. Approach: user chose **moderate** — extract-then-delete when key logic is already in the skill; move extra logic into the skill first when needed.

Memory was kept out of scope at survey time (10 files, all domain nomenclature with zero workflow overlap).

## Phase 2 — Survey output (abbreviated)

Delegated to an `explore` subagent. Final tally:

- DELETE: 5 files — `.cursor/dev_process/examples/autonomous-sat-control-2026-04-30/` pack (off-domain TDD walkthrough).
- EXTRACT: 2 files — `.cursor/rules/notebook-debug-log-path.mdc` (anti-CWD bullet), `.cursor/rules/process/plans-cycle-process.mdc` (human-review-before-stage-move).
- TRIM: 12 files — 3 always-applied rules (lifecycle, post-impl UX review, testing alignment) + 2 notebook-globbed rules + 2 dev_process READMEs + 2 dev_process library rules + 3 dev_process example templates.
- KEEP: rest (domain rules, planning rules, memory).

A path conflict surfaced during survey: the new skill said debug logs go to `.cursor/debug_logs/` but `notebook-debug-log-path.mdc` said `notebook_dir/debug_logs/`. The skill was canonical (user had explicitly chosen `.cursor/debug_logs/` in the session that authored it). Flag noted for Phase 3.

## Phase 3 — Extract

`notebook-debug-log-path.mdc` → moved its anti-CWD bullet into the skill's `reference.md` Instrumentation section. Canonical path stayed `.cursor/debug_logs/`. Stale path in the rule did not propagate.

`plans-cycle-process.mdc` → moved the "never move a plan between stage folders without explicit human review" sentence into `.cursor/rules/plans-lifecycle-workflow.mdc`. The rule's `05-docs-cleanup/` stage was unused (no directory existed) and was dropped, not extracted. Quantitative promotion thresholds were aspirational and not enforced; dropped.

## Phase 4 — Delete

After Phase 3 closed:

- `.cursor/rules/notebook-debug-log-path.mdc` deleted.
- `.cursor/rules/process/plans-cycle-process.mdc` deleted; empty `process/` directory removed.
- 5-file `autonomous-sat-control-2026-04-30/` pack deleted; empty directory removed.

Plan-vs-execution deviation: three more `dev_process/examples/` templates (`grill-me-prompt-template.md`, `tdd-vertical-slice-template.md`, `architecture-slice-pattern.md`) were on the TRIM list but had **zero** in-domain content — they referenced `SimulationStateSeries`, `RewardKernel`, `backend/render/` modules that do not exist in this repo. Deleted rather than trimmed. Deviation called out in the post-sweep summary.

## Phase 5 — Trim

Always-applied (highest leverage):

- `.cursor/rules/plans-lifecycle-workflow.mdc` 29 → 22 lines. Kept stage list, quality-gates bullets, backlog-size-limits link, extracted human-review line. Added a pointer at the skill.
- `.cursor/rules/post-implementation-human-ux-review.mdc` 27 → 16 lines. Kept mandate sentence + pending/completed/N/A example. Pointer at skill Phase 5.
- `.cursor/rules/testing-refactor-alignment.mdc` 23 → 15 lines. Kept behavior-change-requires-tests + notebook prototyping exception. Pointer at skill Phase 3 and Phase 5.

Notebook-globbed:

- `.cursor/rules/notebook-snippet-cells.mdc` 14 → 9 lines.
- `.cursor/rules/notebook-image-display.mdc` 43 → 30 lines, also fixed a stale `backend/scripts/notebooks/` path to `backend/notebooks/utils/`.

Dev process:

- `.cursor/dev_process/README.md`, `examples/README.md`, and the mirrored workflow-rule stubs all collapsed to a few lines each with a pointer at the skill.

## Phase 6 — Verify

- `rg "notebook-debug-log-path|plans-cycle-process|autonomous-sat-control-2026-04-30|grill-me-prompt-template|tdd-vertical-slice-template|architecture-slice-pattern"` returned one hit inside the skill's `SKILL.md` (Phase 4 was citing the deleted `notebook-debug-log-path.mdc`). Updated the cite to point at `reference.md` instead. Re-ran grep: 0 hits.
- 15 always-applied rules survive under `.cursor/rules/` (matched the survey's residual prediction).
- Lint clean on every edited file.

## Lessons that shaped the rubric

- **Skill cross-references break silently.** The new skill itself cited a rule that was deleted in the same sweep. Phase 6's grep catches this only because the deleted filename appears verbatim. Pattern: always re-check skill body for references to anything in the DELETE list.
- **"Archive or trim" is a false binary for off-domain content.** Off-domain templates with no salvageable bullets should be deleted. Note the deviation in the summary so the user can choose to archive if they prefer.
- **Path conflicts are the real risk in EXTRACT.** A surviving rule and the new skill can both contradict each other and pass a green grep. Reconcile during extraction, not after.
- **Survey delegation paid off.** 60 files would have been slow to walk inline; the explore subagent returned a clean ordered map in one pass and surfaced the path conflict as a flag.
