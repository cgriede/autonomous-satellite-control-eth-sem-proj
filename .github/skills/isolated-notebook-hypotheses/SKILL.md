---
name: isolated-notebook-hypotheses
description: >-
  DEPRECATED alias — use hypothesis-experiment-cycle skill instead. Runs isolated
  logic-hypothesis experiments by forking production code, freezing tunables,
  writing fixed-contract JSON, and filling analysis cards before promotion.
disable-model-invocation: true
---

# Isolated Notebook Hypotheses

> **Superseded by [`hypothesis-experiment-cycle`](../hypothesis-experiment-cycle/SKILL.md)** — same workflow, generalized for `backend/scripts/experiments/<slug>/` and notebook hypotheses folders.

## Use When

- The user wants to test **logic hypotheses**, not just tune parameters.
- Production extraction should stay **frozen** while experiments run in forked workspaces.
- The work should live under `backend/notebooks/.../hypotheses/`.
- The user wants either:
  - one focused hypothesis experiment, or
  - multiple hypothesis branches run in parallel and compared afterward.

Use `notebook-hparam-sweep` first if the problem is still mostly about tunables.

## Default pattern

Treat production extraction as **read-only** during the experiment phase.

Create a workspace like:

```text
hypotheses/
  README.md
  <hypothesis>.md
  SUBAGENT_CHARTER.md
  _frozen_baseline.py
  _runner_common.py
  <slug>/
    fib_extraction_<slug>.py
    run_<slug>.py
    results/
```

If multiple branches are active, add one folder per branch:

```text
hypotheses/
  a_<slug>/
  b_<slug>/
```

If a branch needs parser or regex changes, fork the helper too, e.g. `fib_ocr_patterns_<slug>.py`.

## Guardrails

- Do **not** let experiments edit production `fib_extraction.py` during the experiment phase.
- Do **not** let two branches edit the same fork file.
- Keep the notebook and `v2_config.py` read-only unless the user explicitly asks for promotion or notebook wiring.
- Use a **frozen baseline** tunable set in `_frozen_baseline.py`.
- For multi-branch cycles, run the **shared baseline once in the parent/orchestrator path** unless the user explicitly wants per-branch baselines.
- Keep each experiment to **one logical code change** and **at most 3 full runs** after the baseline.
- Require machine-readable output in `results/<experiment_id>.json` using the **fixed result contract** below.
- After each run, fill the **per-hypothesis analysis card** from that JSON before closing the slice.
- On Windows PowerShell, use `;` not `&&` when chaining `conda activate ASC` and `python ...`.

## Evidence-first rule

Before asking the user to judge a hypothesis, make sure the run already contains **real evidence**, not just aggregate KPIs.

### Implement this up front

If the hypothesis could fail in a way that needs inspection, add bounded debug capture **before** the treatment run:

- rejected candidate examples from the key OCR/filter buckets
- accepted examples from the new treatment path
- suspicious accepts on rows with `expected_level_count = 0` when labels exist
- a few “good” baseline accepts for contrast
- enough token/line context to explain why the line was accepted or rejected

Persist these under `debug_examples` in the fixed result contract:

```json
{
  "debug_examples": {
    "reject_no_regex_examples": [],
    "paired_accept_examples": [],
    "accepted_on_zero_label_examples": []
  }
}
```

If the experiment result cannot answer “show me real examples,” the run is incomplete.

## Contract-first rule

Before launching branches, define the **target label contract** clearly enough that branch agents do not improvise policy mid-run.

At minimum, say what counts as:

- in-scope fib labels
- support / resistance labels
- wave labels
- price anchors
- metadata / header / UI text

If a branch is allowed to reason about one of these classes, say so explicitly. Otherwise treat it as out of scope.

## Before launching branches

Write these docs first:

1. `README.md`
   - frozen baseline
   - dataset/date
   - target fib-label contract (what is in scope vs out of scope)
   - shared KPIs
   - workspace layout
   - exact run commands
   - who owns the shared baseline run vs branch treatment runs

2. `<hypothesis>.md`
   - statement
   - falsification criteria
   - implementation phases (`X0`, `X1`, ...)
   - allowed / forbidden tunables
   - success bar
   - evidence plan: what real examples must be captured

3. `SUBAGENT_CHARTER.md`
   - exact editable paths per branch
   - protected paths
   - exact branch ownership (what this branch is allowed to change and what another branch owns)
   - run commands
   - deliverables
   - no destructive git / delete outside scope

## Planning boundary

Use planning proportional to the slice:

- **Long user-guided planning**: normal plan workflow, visible and tracked as part of the broader dev process.
- **Short autonomous experiment setup / cleanup slices**: lightweight local plans are fine; do **not** add them to the main dev-workflow list by default.
- **Tiny follow-ups**: often no formal plan file is needed.

Do not force multiple distinct experiment/cleanup/promote slices into one big evolving plan if separate short plans would be easier to reason about.

## Runner pattern

Use small runner modules that:

- load the dataset with the same notebook pipeline helpers
- call the forked extractor
- compute metrics with shared `fib_v2_metrics`
- write JSON to `results/`
- persist the evidence payload needed for later human inspection

Keep a shared helper (`_runner_common.py`) for:

- dataset loading
- baseline tunables
- timing
- metrics aggregation
- JSON writing

For multi-branch work, the orchestrator should also own:

- one shared baseline result
- one shared summary of baseline KPI numbers
- one clear mapping of branch key -> editable paths -> treatment intent

## Branch workflow

Use this order unless the user explicitly wants something else:

1. shared `baseline` in the parent/orchestrator path
2. `X0` instrumentation / control if needed
3. `X1` first real intervention

For single-hypothesis work, skip the parallel branch setup and keep the same evidence/report rules.

For parallel work, branches should normally start from implementation immediately and compare against the already-published shared baseline instead of each rerunning the same baseline.

## Fixed result contract

Every runner **must** write JSON that matches this shape so the orchestrator can analyze without re-deriving context. Put domain-specific numbers under `kpis` and `debug_examples`; keep the top-level keys stable.

```json
{
  "experiment_id": "b1_fov_cull",
  "hypothesis_id": "fov_cull_speed",
  "phase": "X1",
  "run_at_utc": "2026-06-02T12:00:00Z",
  "frozen_input": {
    "description": "One sentence: what was held constant",
    "scenario": "s01 coast / chart date / dataset id",
    "seed": 42,
    "tunables": {},
    "n_items": null
  },
  "control": {
    "label": "baseline",
    "variant": "production | X0 | shared_baseline",
    "kpis": {},
    "result_path": "results/baseline.json"
  },
  "treatment": {
    "label": "X1",
    "variant": "what changed in one phrase",
    "kpis": {},
    "result_path": "results/X1.json"
  },
  "delta": {
    "primary_kpi": "name of the decision KPI",
    "baseline_value": null,
    "treatment_value": null,
    "direction": "better | worse | flat",
    "relative_change_pct": null,
    "within_noise": true
  },
  "parity": {
    "required": true,
    "passed": true,
    "notes": ""
  },
  "instrumentation": {
    "hooks_valid": true,
    "notes": "e.g. patched import binding, not module attribute"
  },
  "debug_examples": {},
  "files_changed": [],
  "verdict": "supported | falsified | inconclusive",
  "closeout": "promote | keep_as_idea | delete"
}
```

### Runner obligations

- **`frozen_input`**: record the exact frozen dataset / cloud list / chart / tunable set so A/B comparisons reuse the same input (never regenerate stochastic fixtures between control and treatment unless that is the hypothesis).
- **`control` / `treatment`**: always present for logic hypotheses; for a lone baseline run, set `treatment` to `null` and `phase` to `baseline`.
- **`delta`**: precompute baseline → treatment on the **one primary KPI** named in `<hypothesis>.md`; mark `within_noise` when jitter dominates (typical: <5% on wall-clock runs).
- **`instrumentation`**: if telemetry reads 0 but logic clearly ran, set `hooks_valid: false` and name the bad hook (e.g. monkeypatched module but not the import site in the consumer).
- **`debug_examples`**: bounded real evidence (see Evidence-first rule); empty `{}` only when the hypothesis is purely timing and parity passed.
- **`verdict` / `closeout`**: branch sets a **hint**; orchestrator confirms or overrides after artifact review.

Shared helper `_runner_common.py` should expose `write_hypothesis_result(...)` that fills this contract and writes `results/<experiment_id>.json`.

### Fair A/B comparisons

When comparing ON/OFF or baseline/treatment:

1. Freeze stochastic inputs once (`FROZEN_*` tuple, saved fixture, or `frozen_input` blob).
2. Run control then treatment (or interleave if thermal bias matters); max **3** full runs after baseline.
3. Write **one** comparison JSON (e.g. `frozen_cull_comparison.json`) with both arms under `control.kpis` / `treatment.kpis`, not two incomparable files.

## Per-hypothesis analysis card (required)

After reading the result JSON and changed files, the orchestrator **must** produce one analysis card **per hypothesis** using this fixed template. Copy it verbatim, fill every section, and persist as `results/<hypothesis_id>_analysis.md` **and** return it to the user.

```markdown
# Hypothesis analysis: <hypothesis_id>

## 1. Question
<one sentence from <hypothesis>.md>

## 2. Frozen input
| Field | Value |
|-------|-------|
| Scenario | |
| Seed / fixture | |
| Key tunables | |
| N (items/clouds/charts/rows) | |

## 3. KPI table
| Arm | <primary_kpi> | <guardrail_kpi> | <progress_kpi_if_any> |
|-----|---------------|-----------------|------------------------|
| Control (<label>) | | | |
| Treatment (<label>) | | | |
| Delta | | | |

## 4. Evidence (real examples)
- <3–10 bullets or short blocks pulled from debug_examples JSON — not paraphrased>
- If timing-only: state parity outcome and instrumentation validity.

## 5. Interpretation
- **Primary KPI:** baseline → treatment = <values>; direction = <better/worse/flat>; within noise = <yes/no>.
- **Guardrails:** <wrong_data_rate, parity, etc. — pass/fail>.
- **Why:** <2–4 sentences tying evidence to outcome>.

## 6. Verdict
**<supported | falsified | inconclusive>** — <one-line justification>.

## 7. Closeout
| Action | Item |
|--------|------|
| Promote now | |
| Keep as idea | |
| Delete / archive | |
| Test next | |
| Stack with | <other hypothesis or "none"> |

## 8. Path parity / caveats
<notebook vs runner path, bad telemetry, confounded runs, or "none">
```

Do **not** close a hypothesis slice until every section is filled. If a field is unknown, write `TBD` and fix the runner before claiming a verdict.

### Multi-hypothesis cycles

When several branches ran in parallel:

1. Write one card per `hypothesis_id`.
2. Add a **combined summary** table (all primary KPIs, all verdicts) at the top of the user reply.
3. Cross-check cards against JSON — verdict in the card must match `verdict` in JSON unless the orchestrator documents an override in §8.

## Branch prompt template

Each branch prompt should include:

- exact hypothesis doc to follow
- exact folder it may edit
- exact files it must not edit
- whether baseline is shared-orchestrator-owned or branch-owned
- ordered steps: shared `baseline` reference -> `X0` -> `X1`
- max 3 runs after baseline
- required KPI table
- required verdict: `supported`, `falsified`, or `inconclusive`
- required evidence payload in `debug_examples`
- output must follow the **fixed result contract**; orchestrator fills the **analysis card** afterward
- promotion note for production
- exact label-scope contract the branch must respect

Example:

```text
You are the OCR hypothesis branch.
Work ONLY under hypotheses/b_ocr_pairing/.
Read README.md, B-ocr-pairing.md, SUBAGENT_CHARTER.md.
Run baseline, then B0 instrumentation if needed, then B1.
Persist real accepted/rejected examples into results/B1.json.
Do not edit production fib_extraction.py.
Return KPI table, verdict, files changed, JSON result paths, 5-10 real examples, and path to results/<hypothesis_id>_analysis.md once the orchestrator writes it.
```

## KPI expectations

Use both:

- **progress KPIs**: `ocr_levels_pct_of_optimal`, `span_levels_pct_of_optimal`, `zones_pct_of_optimal`, `level_both_recall_annotated`
- **strict KPI**: `correct_enough_count_annotated`
- **guardrails**: `wrong_data_rate_annotated`, `precision_floor_any_extra_zones`

Interpretation:

- `X0 ~= baseline` -> good control
- `X1 ~= baseline` -> treatment falsified
- `X1 worse than baseline` -> do not stack or promote
- `X1 better than baseline` -> candidate for promotion or a later stack

## Report requirements

The user-facing report **is** the per-hypothesis analysis card(s) from the section above. Do not substitute a free-form summary.

Additionally:

- **Combined summary** (multi-branch only): one table of all `hypothesis_id`, primary KPI delta, verdict.
- **Real examples**: §4 of each card must cite JSON `debug_examples` (or state timing-only + parity).
- **Path parity / caveats**: always fill §8 when notebook, runner, or telemetry paths differ.

Do **not** present only aggregate metrics if the user is likely to ask “what was actually parsed?”

## Post-run orchestrator review

After any hypothesis branch or subagent finishes, the parent/orchestrator must do a quick artifact review **before** closing the slice:

1. read the branch's key changed files
2. read at least the main result JSON for the finished run
3. check that the claimed verdict matches the recorded KPIs and examples
4. **write and return the per-hypothesis analysis card** (persist `results/<hypothesis_id>_analysis.md`)

Skip the card only if the user explicitly asked not to receive a findings report.

The card replaces the old informal “short findings report” — same content, fixed sections 1–8.

## Promotion rules

Promote only after the orchestrator reviews all active branches or the single active branch.

Safe to promote first:

- instrumentation
- counters
- reject-bucket summaries
- funnel summaries
- evidence logging that helps future hypothesis work

Do **not** promote:

- failed treatments
- inconclusive tuning changes
- fork-only experiment switches

When promoting:

1. port the minimal diff into production
2. if the promoted logic is expected to be runnable from the notebook, update the notebook entrypoint/import path in the same slice
3. delete generated fork runners/results if no longer needed
4. keep useful hypothesis docs and reports
5. run one real validation pass on production code
6. run a small representative smoke set on known benchmark charts before cleanup/commit
7. verify path parity:
   - notebook import path uses the promoted production module
   - notebook metrics and validation reflect the same post-hardening / pre-hardening state the human will review

If the notebook mutates `v2_rows` after extraction (for example via hardening), do not leave summary stats in a stale earlier state.

## Common anti-patterns

- Launching parallel branches against the same production file
- Letting every subagent rerun the same baseline setup work
- Mixing two hypotheses in one experiment branch
- Re-sweeping all tunables inside a logic-hypothesis branch
- Treating a failed `X1` as stackable
- Reporting only summary KPIs without real examples
- Realizing after the run that the JSON does not contain enough evidence for human review
- Skipping the analysis card or leaving sections blank / “TBD” at closeout
- JSON that omits `frozen_input` so the next run cannot reproduce the comparison
- Instrumentation hooks that patch the wrong import site (`hooks_valid: false` undetected)
- Launching branches before the fib-label contract is explicit
- Promoting logic without verifying the notebook uses the promoted production path
- Comparing pre-hardening KPIs to post-hardening notebook visuals without naming the mismatch

## Outputs

The orchestrator should return:

1. **Combined summary table** (multi-branch) or single card header (solo)
2. **One filled analysis card per `hypothesis_id`** (sections 1–8)
3. Paths to `results/<experiment_id>.json` and `results/<hypothesis_id>_analysis.md`
4. Whether notebook wiring / path parity still needs a follow-up before calling the cycle complete

Verdict, closeout, promote/test-next, and stacking decisions live in §6–§7 of each card — do not duplicate them in a separate prose list unless the user asked for a shorter recap.
