# Autonomous-Sat-Control Example Pack (2026-04-30)

This pack is a concrete process run for this repository using the 4-step workflow:

1. Drill / Shared Understanding
2. Ubiquitous Naming + Physical Representation + Description
3. TDD Vertical Slices
4. AI-Friendly Architecture Slices

## Files

- `01-drill.md` - clarification-first prompts, question bank, and implementation gate.
- `02-naming.md` - canonical vocabulary, naming rules, units/representation rules.
- `03-workflow.md` - TDD and architecture-slice checklists with entry/exit criteria.
- `04-synthesis.md` - combined "good run" execution template that ties 01-03 together.

## How To Use

1. Start with `01-drill.md` and do not code until ambiguity is removed.
2. Lock terms and units from `02-naming.md`.
3. Execute one smallest behavior via `03-workflow.md`.
4. Use `04-synthesis.md` as the final run sheet before implementation and review.

## Repository Invariants This Pack Preserves

- One episode equals one canonical simulation rollout.
- Train/eval/render consume the same simulation outputs.
- Simulation owns physics/camera/reward-signal computation.
- Render is view-only.
- `SimulationStateSeries` is the episode-level artifact contract.
- Physical quantities remain unit-consistent with pint-based conventions where applicable.
