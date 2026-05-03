# TDD Vertical Slice Template (This Repository)

Working copy for one end-to-end behavior. Keep slices small enough to narrate in a single PR or commit cluster.

---

## Blank Template (Copy for Each New Slice)

### Slice Definition

- **Feature name**:
- **User-visible outcome**:
- **Smallest behavior to verify now**:
- **Non-goals for this slice**:
- **Module owner** (`simulation` / `render` / `autonomous_control` / `environment_definition` / other):

### Red (failing test first)

- File and test name:
- Expected failure symptom (AssertionError message / fixture mismatch):

### Green (minimal implementation)

- Files touched:
- Explicitly unchanged surfaces:

### Refactor (only on green)

- Structural improvement (if any):

### Verification Record

| Check | Command / Action | Result |
|---|---|---|
| Directed test(s) | | |
| Lint / optional suite | | |

- **Behavior now guaranteed**:
- **Next smallest slice**:

---

## Filled Illustrative Example (Hypothetical; Replace When Doing Real Work)

### Slice Definition

- **Feature name**: Simulation exposes `slant_range_to_observation_target_km` on each `SimulationTimestepState`.
- **User-visible outcome**: Training and diagnostics can consume the same numeric slant-range the reward pathway uses—without recomputing in render or RL env proxies.
- **Smallest behavior to verify now**: For a deterministic tiny rollout fixture, timestep `k` exposes the new field and matches a hand-checked planar distance formula.
- **Non-goals for this slice**: No renderer changes beyond maybe reading existing series fields later; no change to Gym env reward proxies in this slice.
- **Module owner**: `simulation`

### Red

- **File**: `backend/simulation/tests/test_slant_range_exposed.py`
- **Test**: `test_timestep_state_includes_slant_range_for_known_geometry`
- **Failure expectation**: Missing attribute on `SimulationTimestepState`.

### Green

- Add field to [`SimulationTimestepState`](../../../backend/simulation/state_types.py).
- Populate in [`SimulationStepper.current_timestep_state`](../../../backend/simulation/stepper.py) using the same geometry already available to `RewardKernel` (reuse helper to avoid divergence).

### Refactor

- Extract shared planar distance helper if duplicate math appears across stepper and reward kernel—**only after** the new test stays green.

### Verification Record

- **Tests run**: scoped pytest module for simulation (as configured in repo).
- **Result**: PASS.
- **Guaranteed**: timestep API surface includes slant-range for controlled fixture.
- **Next slice**: Extend `SimulationStateSeries` arrays if episodic exporters need dense storage.
