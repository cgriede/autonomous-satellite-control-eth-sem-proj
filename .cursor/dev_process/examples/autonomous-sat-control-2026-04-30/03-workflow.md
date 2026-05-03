# 03 - Workflow (TDD + Architecture Slices)

Execution playbook for small, reviewable changes in this repository.

## A) TDD Vertical Slices

### Step-by-step checklist
- [ ] Define one smallest behavior in one sentence using canonical terms.
- [ ] Declare owner module (`simulation`, `autonomous_control`, `render`, `environment_definition`).
- [ ] Write one failing test first (Red) for that exact behavior.
- [ ] Implement minimum code to pass (Green), no side refactors.
- [ ] Refactor only after green; keep behavior unchanged.
- [ ] Verify unit consistency for all physical quantities (pint-aware).
- [ ] Run focused tests and record next slice boundary.

### Entry criteria
- Behavior is clear and testable.
- Ownership is explicit.
- Expected artifact level is clear (`SimulationTimestepState` vs `SimulationStateSeries`).
- Unit expectations are explicit.

### Exit criteria
- Test fails before code and passes after code.
- No duplicate simulation path introduced.
- Train/eval/render stay on shared canonical outputs.
- Render remains view-only.
- `SimulationStateSeries` contract is preserved or intentionally extended.

### Review checklist
- [ ] Test name describes behavior.
- [ ] Red step failure is meaningful.
- [ ] Green implementation is minimal.
- [ ] No reward/camera/physics ownership leak outside simulation.
- [ ] No shadow recomputation in render.
- [ ] Unit math remains explicit and consistent.

### Common failure modes
- Broad tests that validate too many behaviors.
- Weak assertions producing false green.
- Renderer-side recomputation instead of extending simulation outputs.
- Ad-hoc episode state replacing `SimulationStateSeries`.
- Unitless physics values.

### Prompt snippet
```text
Implement one strict TDD vertical slice.
Behavior: <one-sentence behavior>
Constraints:
- canonical simulation rollout ownership stays in simulation
- train/eval/render consume shared canonical outputs
- render is view-only
- SimulationStateSeries remains episode-level contract
- physical quantities remain pint-consistent
Do Red -> Green -> Refactor and report verification.
```

## B) AI-Friendly Architecture Slices

### Step-by-step checklist
- [ ] Define feature boundary by behavior, not by horizontal layer.
- [ ] Expose one small stable API; hide internal complexity.
- [ ] Co-locate types/logic/tests near owner module.
- [ ] Keep cross-module coupling explicit and minimal.
- [ ] Keep simulation-owned signals generated once in canonical path.
- [ ] Keep render as consumer-only.
- [ ] Validate naming against canonical vocabulary.

### Entry criteria
- Slice boundary and ownership are explicit.
- Public API and dependencies are identified.
- Contract impact on `SimulationStateSeries` is known.

### Exit criteria
- One coherent behavior is traceable end-to-end.
- Public interface stays minimal.
- No new shadow simulation path appears.
- Render remains view-only.
- Unit semantics stay explicit across boundaries.

### Review checklist
- [ ] Feature boundary is clear and domain-aligned.
- [ ] Public API is small and stable.
- [ ] No horizontal sprawl.
- [ ] Canonical rollout ownership preserved.
- [ ] Shared outputs for train/eval/render preserved.
- [ ] `SimulationStateSeries` preserved or extended intentionally.

### Common failure modes
- Splitting one behavior across many unrelated modules.
- Overexposed helper APIs.
- Hidden fallback computations in render.
- Alternate reward/camera/physics paths outside simulation.
- Inconsistent naming for the same concept.

### Prompt snippet
```text
Design one AI-friendly architecture slice.
Behavior: <one-sentence feature>
Requirements:
- vertical slice and deep module boundary
- preserve canonical simulation rollout ownership
- preserve shared train/eval/render outputs
- keep render view-only
- keep SimulationStateSeries as episode artifact
- keep physical units explicit and consistent
Deliver API boundary, minimal steps, risks, and tests.
```
