# 04 - Synthesis (Good Run Template)

Use this as the final integrated run sheet after completing `01` through `03`.

## Objective

Execute one high-quality process run that:
- starts with shared understanding,
- uses canonical vocabulary and explicit physical representation,
- delivers one strict TDD vertical slice,
- preserves architecture invariants.

## Run Sequence

1. **Drill**
   - Use `01-drill.md` starter prompt.
   - Resolve scope, constraints, assumptions, risks.
   - Pass implementation gate checklist.
2. **Naming + Representation**
   - Use `02-naming.md` vocabulary and naming rules.
   - Confirm all physical quantities use explicit units and conversion boundaries.
3. **Workflow**
   - Use `03-workflow.md` TDD and architecture checklists.
   - Execute one Red -> Green -> Refactor slice only.
4. **Final Verification**
   - Validate invariants and acceptance criteria below.

## Final Acceptance Checklist

- [ ] One episode still equals one canonical simulation rollout.
- [ ] Train/eval/render consume the same simulation outputs.
- [ ] Simulation remains owner of physics/camera/reward-signal computation.
- [ ] Render remains view-only.
- [ ] `SimulationStateSeries` remains the episode-level artifact contract.
- [ ] No shadow simulation path introduced in scripts or render code.
- [ ] Physical units are explicit and pint-consistent at boundaries.
- [ ] The slice is test-backed with a clear Red -> Green trace.

## Deliverable Snapshot Template

```markdown
### Process Run Summary
- Behavior slice:
- In-scope files:
- Out-of-scope files:
- Failing test first:
- Minimal implementation:
- Refactor done:

### Invariant Check
- Canonical rollout preserved: yes/no
- Shared train/eval/render outputs preserved: yes/no
- Simulation ownership preserved: yes/no
- Render view-only preserved: yes/no
- SimulationStateSeries contract preserved: yes/no
- Unit consistency preserved: yes/no

### Next Slice
- Smallest next behavior:
- Why deferred:
```

## Notes

- If any invariant fails, stop and narrow scope before continuing.
- If uncertainty remains, return to `01-drill.md` instead of coding forward.
