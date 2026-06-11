---
name: hypothesis-experiment-cycle
description: >-
  Runs isolated logic-hypothesis experiments by forking production code under
  an experiment workspace, freezing tunables, writing fixed-contract JSON
  results, filling per-hypothesis analysis cards, and deciding what to promote.
  Use when testing logic hypotheses (not tunables), setting up forked experiment
  branches under backend/scripts/experiments/ or backend/notebooks/.../hypotheses/,
  closing a cycle with supported/falsified verdict, or promoting performance
  fixes (pair with performance-optimization for profiling gates).
disable-model-invocation: true
---

# Hypothesis Experiment Cycle

Generalized workflow for logic-hypothesis testing and promotion. Replaces the notebook-only framing of `isolated-notebook-hypotheses`.

## Use When

- Testing **logic hypotheses**, not parameter sweeps (use `notebook-hparam-sweep` for tunables).
- Production code must stay **read-only** during the experiment phase.
- One or more parallel branches with a **shared baseline**.

## Workspace locations

| Domain | Default path |
|--------|--------------|
| Simulation / backend | `backend/scripts/experiments/<slug>/` |
| Notebook pipelines | `backend/notebooks/<nb>/hypotheses/<slug>/` |

Example: [`backend/scripts/experiments/sensor_ray_batch/`](../../../backend/scripts/experiments/sensor_ray_batch/) (fused ray batch + tensor cloud hits).

## Default layout

```text
<slug>/
  README.md
  <hypothesis>.md          # one per hypothesis
  SUBAGENT_CHARTER.md
  _frozen_baseline.py
  _runner_common.py        # write_hypothesis_result()
  run_baseline.py
  results/baseline.json
  a_<branch>/
    *_fork.py
    run_*.py
    results/
```

## Guardrails

- Do **not** edit production modules during experiments.
- One logical change per branch; max **3** runs after shared baseline.
- Fixed JSON result contract + **per-hypothesis analysis card** (sections 1–8).
- Windows PowerShell: `conda activate ASC; python ...` (use `;` not `&&`). See `python-runtime-environment`.

## Fixed result contract

See `isolated-notebook-hypotheses/SKILL.md` §Fixed result contract — same schema (`experiment_id`, `frozen_input`, `control`, `treatment`, `delta`, `parity`, `debug_examples`, `verdict`, `closeout`).

Shared helper must expose `write_hypothesis_result(...)`.

## Analysis card

After each branch run, persist `results/<hypothesis_id>_analysis.md` using the 8-section template in the legacy skill. Verdict in card must match JSON unless documented override.

## Promotion

Promote only after parity + speed gates pass. Port minimal diff to production, run tests, re-run baseline. Promote lower-level changes first when stacking (e.g. `camera_2d` before `sensor_kernel`).

### Performance-driven promotion

When the promote target is **throughput or latency** (sim `steps/s`, training rollouts, render/export wall time), follow [`performance-optimization`](../performance-optimization/SKILL.md) in addition to the logic-hypothesis gates below.

**Required before merge:**

1. **Profile on the painful fixture** — run `backend/scripts/experiments/sim_timing/run_profile.py` (or the experiment slug for that domain) on the scenario that motivated the change (e.g. `high_cloud`, not only `low_cloud`).
2. **Document category shift** — treatment must move the expected bin (`environment_clouds`, `sensor_camera_rays`, etc.); note `steps_per_s` and top-7 `%` in the analysis card or PR text.
3. **Parity unchanged** — observation codes, rewards, or other semantics per the fixed contract; speed without parity is rejected.
4. **Speed gate** — state an explicit bar in the hypothesis doc (e.g. ≥1.5× micro KPI, ≥1.2× episode `steps_per_s`); treatment must meet it on the frozen fixture.
5. **Re-profile after promote** — one post-promotion `run_profile.py` (or baseline runner) on the same fixture to confirm production paths picked up the win (watch stale `from X import Y` in production if the fork only patched a module attribute).

**Not required** when performance is “good enough” by user-stated budget (batch jobs, rare scripts, notebooks run a few times a day). Ask for the budget; skip heavy profiling if already met.

**Avoid** promoting GPU/Cython/Numba until episode profiling shows the bottleneck; algorithmic fixes (precompute, cull, batch timesteps) often win first—see performance-optimization §Technology choice.

## Reference cycle (sensor_ray_batch)

| Hypothesis | Fork | Primary KPI | Result |
|------------|------|-------------|--------|
| fuse_cameras | `sensor_kernel_fork.py` | 1.5× micro total_s | supported |
| tensor_clouds | `camera_2d_fork.py` | 2× line @ high clouds | supported |

Full charter: [`sensor_ray_batch/SUBAGENT_CHARTER.md`](../../../backend/scripts/experiments/sensor_ray_batch/SUBAGENT_CHARTER.md).

Timing profiler (profile before/after performance promotes): [`sim_timing/README.md`](../../../backend/scripts/experiments/sim_timing/README.md) — see `performance-optimization` skill.
