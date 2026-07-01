---
name: hypothesis-experiment-cycle
description: >-
  Runs isolated logic-hypothesis experiments by forking production code under
  an experiment workspace with the minimal fork that gets the arm running
  (ponytail rule), freezing tunables, writing fixed-contract JSON results,
  filling per-hypothesis analysis cards, and deciding what to promote. Use when
  testing logic hypotheses (not tunables), setting up forked experiment branches
  under backend/scripts/experiments/ or backend/notebooks/.../hypotheses/,
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

## Research first

Before writing `<hypothesis>.md` or forking:

0. Read [`docs/research/PROJECT_KNOWLEDGE.md`](../../../docs/research/PROJECT_KNOWLEDGE.md), [`DECISIONS.md`](../../../docs/research/DECISIONS.md), and relevant `results/*.json` — **do not duplicate** arms or violate rejected scope.
1. Follow [`hypothesis-research-literature`](../hypothesis-research-literature/SKILL.md):
   - Search [`docs/research/LITERATURE_HIGHLIGHTS.md`](../../../docs/research/LITERATURE_HIGHLIGHTS.md) and local PDFs.
   - Download gaps to `docs/research/`; add section highlights.
   - Add **Literature basis** to the hypothesis doc and analysis card §1.
2. After closeout, update layers via [`document-research`](../document-research/SKILL.md) (DECISIONS + STATUS closeout + investigation note if conclusion is general).

If the team already researched the topic in-session, point to the existing highlights entry—do not re-download.

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
- **One pipeline training run per host** — `backend/scripts/experiments/pipeline_run_guard.py`; see [`experiment-knowledge-pipeline`](../experiment-knowledge-pipeline/SKILL.md). Do not launch a second slug while `.active_run.json` shows a live holder.
- Numbered pipeline experiments: append `docs/experiments/pipeline/{bin}/{NN}-{slug}.md` per phase via `/document-experiment-step`; after evaluation in chat, **proactively** `close-phase` — see learnings.md `pipeline-advance-after-run-evaluation` and [`experiment-knowledge-pipeline`](../experiment-knowledge-pipeline/SKILL.md).
- After Phase 2 runs with video export: optional [`video-frame-inspect`](../video-frame-inspect/SKILL.md) before Phase 3 verdict; Phase 4 requires [`visual-output-verification`](../visual-output-verification/SKILL.md) for report-facing artifacts.
- Windows PowerShell: `conda activate auto-sat; python ...` (use `;` not `&&`). See `python-runtime-environment`.

## Minimal fork (ponytail rule)

The global **ponytail rule** applies everywhere: smallest correct diff, no opportunistic refactors. In experiment folders it is **stricter** — the fork exists only to **run the hypothesis**, not to preview production architecture.

Follow [`implementation-discipline`](../implementation-discipline/SKILL.md) § smallest verifiable slice.

### Principle

> **One frozen question → one hook point → one fork surface → smoke → then train.**

If the arm runs without a file, do not add that file.

### Do (in order)

1. **Copy scaffold from a sibling slug** — `_runner_common.py`, `_run_guard.py`, `SUBAGENT_CHARTER.md`, phase pattern from e.g. [`ml_algo_overnight/`](../../../backend/scripts/experiments/ml_algo_overnight/). Do not reinvent JSON contract or lock files.
2. **State the single delta** in `<hypothesis>.md` before coding (one sentence: *what one thing changes*).
3. **Prefer runtime hook over vendoring** — `monkeypatch`, `dataclasses.replace`, injected callback, or a thin `_*_fork.py` imported only from the experiment entry script.
4. **One fork module per logical change** — e.g. `_reward_fork.py` only switches reward mode; do not fork the whole training stack for a threshold tweak.
5. **Smoke before full matrix** — `--smoke` or 1-ep dry run; fix imports/env in the **experiment folder** only.
6. **Charter first** — `SUBAGENT_CHARTER.md` lists protected vs editable paths before any `*_fork.py` is written.

**Pipeline Phase 1:** Run the Nike-vs-plan gate in [`experiment-knowledge-pipeline`](../experiment-knowledge-pipeline/SKILL.md) § Implement mode before the first fork edit — Nike mode requires user-visible justification; plan mode or upstream-bug suspicion requires **user** decision (see learnings.md `pipeline-implement-nike-vs-plan-gate`).

### Do not

- Refactor production-shaped code inside the experiment folder “for cleanliness”
- Vendoring entire production modules when a 10-line patch or replace hook suffices
- Adding agents, encoders, or runners not required for the stated hypothesis
- Bundling a second hypothesis in the same branch (“while we're here”)
- Building abstractions shared across arms before **two** arms need them
- Touching protected paths for convenience — stop and document in DECISIONS if prod fix is truly required

### Fork sizing checklist (before first real run)

```text
- [ ] Hypothesis doc names exactly ONE logical delta
- [ ] Can point to the single hook (file + function or replace field)
- [ ] No new file that duplicate production logic already reachable via import
- [ ] Scaffold copied from existing slug where possible
- [ ] Smoke passes with minimal LOC diff vs sibling experiment
- [ ] git diff paths ⊆ experiment folder (+ docs closeout if applicable)
```

### When the minimal fork is blocked

If the hypothesis **cannot** run without a production edit:

1. **Stop** — do not grow the experiment folder to work around it.
2. Record in [`DECISIONS.md`](../../../docs/research/DECISIONS.md) + STATUS notes.
3. Separate minimal prod fix (user-approved promote), then resume the experiment fork.

Promotion still ports the **minimal** proven diff — not the experiment scaffolding.

**Pipeline experiments:** closeout the pipeline doc (Phases 2–4 in `4-documentation/`, verdict + DECISIONS) **before** any production promote — see [`experiment-knowledge-pipeline`](../experiment-knowledge-pipeline/SKILL.md) § Promotion boundary and learnings.md `pipeline-closeout-before-promote`.

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
