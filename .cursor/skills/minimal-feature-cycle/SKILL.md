---
name: minimal-feature-cycle
description: Guide a backlog item through a thin prototype notebook to production using the project's minimal feature cycle. Use when the user says "minimal feature cycle", "minimal feature notebook", "simplify the notebook", "notebook too large", or "let's implement this backlog item as a minimal feature", or when an opened notebook is too big for a human to grasp in one go (then also read notebook-simplify.md). When promote/close is done, ask whether to run minimal-feature-review (/minimal-feature-review).
---

# Minimal Feature Cycle

Run a backlog item through five phases. The notebook is a thin scratchpad over real production modules; validation lives where it belongs; root causes are fixed at the source.

In this workflow, verification means the real output that will be produced when we plug the thing into the simulator, the actual numbers it produces, and the actual artifact a human will inspect. It does not mean generic plots, abstract diagnostics, or notebook-only visuals unless the slice is explicitly limited to a geometry probe.

## Phase 1 — Scope from backlog

1. **Preflight** the live workbook: `python backend/scripts/backlog_xlsx.py check` (see [pm-backlog-review](../pm-backlog-review/SKILL.md) if missing). Read the row by `uid` from [`backlog.xlsx`](../../../backlog.xlsx) — not from `backlog.md` or plan todos alone.
2. Copy [.cursor/plans/00-initialized/DEFAULT_DEVELOPMENT_CYCLE.plan.md](../../plans/00-initialized/DEFAULT_DEVELOPMENT_CYCLE.plan.md) to a new file in `00-initialized/`. Rename with a short suffix.
3. Fill section 0: problem, outcome, non-goals, backward compatibility, acceptance criteria.
4. When scope is fuzzy, ask the questions required by [.cursor/rules/planning-clarifying-questions.mdc](../../rules/planning-clarifying-questions.mdc) before writing code.

## Phase 2 — Build the minimal feature notebook

1. Copy `templates/notebook_template.ipynb` to `backend/notebooks/minimal_feature_cycle/<feature_name>.ipynb`.
2. The notebook imports the production module and calls `importlib.reload(...)` after each edit. No helper logic lives in the notebook.
3. If a helper is reused across cells, promote it to a production module first, then import it. Do not let parallel logic emerge in the notebook.
4. Use the minimal verifying snippet to exercise the changed function with the smallest meaningful inputs.
5. Before implementation, define the verification contract in concrete terms:
   - which real simulator-facing path or integration seam will be exercised,
   - which exact numbers will be printed and inspected,
   - which actual artifact will be inspected,
   - what is explicitly out of scope for this slice.

**Notebook too large?** If the ipynb already exceeds human scan (~500+ lines, many `def` cells, duplicated verification), run the subskill [notebook-simplify.md](notebook-simplify.md) before adding more cells.

## Phase 3 — Validation placement

Three gates. Each has one home:

| Gate | Home | Proves |
|------|------|--------|
| Unit | `*/tests/test_<module>.py` next to the code | Pure behaviour of changed functions |
| End-to-end / fixtures | Fixture directory + parametrized pytest | Full path with realistic inputs; one fixture per regime |
| Human visual / artifact review | Notebook section + plan section 4b | The actual produced artifact and actual produced numbers match operator intent |

Decision rule: **if a regression could ship with all gates green, a gate is in the wrong place**.

For simulator-facing work, prefer verification on the same output path the simulator will actually produce. If the future consumer is `SimulationStateSeries`, render panels, reward outputs, or other runtime-facing artifacts, the notebook should inspect those outputs directly or make the temporary limitation explicit.

Fixture rule: ground truth must come from a source independent of the code under test. Human measurement, geometric construction, or a sibling tool — never `expected = code_under_test_output(...)`.

## Phase 4 — Root-cause discipline

When a test fails or an artifact looks wrong, do not patch the symptom.

Forbidden shortcuts:

- Widening tolerances to make a test pass.
- Setting `expected = current_output` and locking the wrong value.
- Suppressing exceptions, silencing logs, or skipping tests.
- Renaming a failure to make it less visible.

Required loop:

1. State 2-5 concrete hypotheses about why the failure happens.
2. Add minimal instrumentation that distinguishes between them. Write logs to `.cursor/debug_logs/`; never the repo root. See the Instrumentation section in [reference.md](reference.md).
3. Reproduce, read the logs, confirm one hypothesis with cited evidence.
4. Fix at the source so the same class of error cannot recur silently.
5. Lock the behaviour with an assertion or a focused test.
6. Re-run the same real-output verification path and inspect the actual numbers / artifact again.
7. Remove instrumentation after post-fix verification passes.

## Phase 5 — Promote and close

1. Move production code into the package it belongs to. Keep the logic-vs-UX boundary clean: business logic stays in `automation/...`; matplotlib and operator-facing helpers stay in `backend/notebooks/utils/`.
2. Tests live next to the code they cover, not in the notebook.
3. Move the plan file through stages per [.cursor/rules/plans-lifecycle-workflow.mdc](../../rules/plans-lifecycle-workflow.mdc).
4. Complete the human UX walkthrough required by [.cursor/rules/post-implementation-human-ux-review.mdc](../../rules/post-implementation-human-ux-review.mdc), or write `Human UX review: N/A — <one-line reason>` in section 4b.
5. Archive the plan when the done checklist is satisfied.
6. **Update backlog:** set matching `backlog.xlsx` row to `status=done` (see [pm-backlog-review](../pm-backlog-review/SKILL.md)); do not update only `backlog.md`.
7. **Review handoff (required):** Before treating the cycle as finished, ask the user whether to run [.cursor/skills/minimal-feature-review/SKILL.md](../minimal-feature-review/SKILL.md) (`/minimal-feature-review`). Offer a one-line summary of what changed (commits, branch, or plan name) so they can say yes with context. Do not start the review yourself unless they agree — the review skill begins with working-tree hygiene and framed cleanup targets. If review runs and applies a fix, **human confirmation before commit** is mandatory per that skill's Phase 5 (see learnings.md `human-confirm-before-review-ship`).

## Phase flow

```mermaid
flowchart LR
  backlog[Backlog item] --> plan["Plan in 00-initialized"]
  plan --> notebook["Thin notebook: reload + import production"]
  notebook --> instrument["Observe / instrument (.cursor/debug_logs)"]
  instrument --> fix[Source fix - no symptom suppression]
  fix --> gates[Place validation: unit / e2e / visual]
  gates --> promote[Promote: code + tests + notebook utils]
  promote --> backlogDone["backlog.xlsx status=done"]
  backlogDone --> archive["Plan -> 99-archive"]
  archive --> askReview["Ask: /minimal-feature-review?"]
```

## Pointers

- Post-cycle cleanup and ship prep: [minimal-feature-review](../minimal-feature-review/SKILL.md) — run after promote/close when the user accepts the handoff.
- Patterns and rules in depth: [reference.md](reference.md).
- One worked example from a real cycle: [examples.md](examples.md). Read on request.
- Oversized notebook cleanup: [notebook-simplify.md](notebook-simplify.md) (subskill).
