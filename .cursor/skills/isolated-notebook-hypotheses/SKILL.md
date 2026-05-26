---
name: isolated-notebook-hypotheses
description: >-
  Runs isolated logic-hypothesis experiments for LRF notebook pipelines by
  forking production code under hypotheses/, freezing tunables, capturing real
  evidence in JSON outputs, and synthesizing supported/falsified verdicts. Use
  when testing logic hypotheses rather than tunables, setting up forked notebook
  experiments, running one or more hypothesis branches, or deciding what
  instrumentation or logic is safe to promote.
disable-model-invocation: true
---

# Isolated Notebook Hypotheses

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
- Require machine-readable output in `results/<experiment_id>.json`.
- On Windows PowerShell, use `;` not `&&` when chaining `conda activate LRF` and `python ...`.

## Evidence-first rule

Before asking the user to judge a hypothesis, make sure the run already contains **real evidence**, not just aggregate KPIs.

### Implement this up front

If the hypothesis could fail in a way that needs inspection, add bounded debug capture **before** the treatment run:

- rejected candidate examples from the key OCR/filter buckets
- accepted examples from the new treatment path
- suspicious accepts on rows with `expected_level_count = 0` when labels exist
- a few “good” baseline accepts for contrast
- enough token/line context to explain why the line was accepted or rejected

Persist these under a dedicated JSON key such as:

```json
{
  "stats": {
    "debug_examples": {
      "reject_no_regex_examples": [...],
      "paired_accept_examples": [...],
      "accepted_on_zero_label_examples": [...]
    }
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
- required evidence payload
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
Return KPI table, verdict, files changed, JSON result paths, and 5-10 real examples.
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

Every hypothesis report must include **actual run data**:

1. KPI table
2. a short KPI summary with the **most decision-relevant numbers** (`baseline -> treatment`, direction, and why they matter)
3. verdict
4. real accepted/rejected examples from the result JSON
5. which patterns seem valid vs invalid
6. what to promote now
7. what to test next
8. whether stacking is justified

Also include these checks when relevant:

- **Path parity:** say whether the reported KPIs come from the same path the human reviewed (for example, pre-hardening runner output vs post-hardening notebook output).
- **Human-review mismatch:** if notebook / overlay review looks better or worse than the KPI/bin summary, explain the mismatch before giving the final verdict.
- **Closeout decision:** at the end of a hypothesis cycle, explicitly separate:
  - keep/promote
  - keep as idea only
  - delete/archive

Do **not** present only aggregate metrics if the user is likely to ask “what was actually parsed?”

## Post-run orchestrator review

After any hypothesis branch or subagent finishes, the parent/orchestrator must
do a quick artifact review before closing the slice:

1. read the branch's key changed files
2. read at least the main result JSON for the finished run
3. check that the claimed verdict matches the recorded KPIs and examples
4. return a **short findings report** to the user unless the user explicitly
   asked not to receive one

The short findings report should cover:

- what changed in the branch
- whether the control matched baseline
- whether the treatment improved, regressed, or stayed flat
- 3-5 real examples or pattern findings
- the closeout decision: promote / keep as idea / delete

Do not rely only on the subagent's prose summary when the artifacts are
available; review the actual files first.

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
- Launching branches before the fib-label contract is explicit
- Promoting logic without verifying the notebook uses the promoted production path
- Comparing pre-hardening KPIs to post-hardening notebook visuals without naming the mismatch

## Outputs

The orchestrator should return:

1. One combined KPI table across active hypotheses
2. A short KPI summary with the most important numbers
3. A short verdict per hypothesis
4. A compact “real examples” section with actual run data
5. What to promote now
6. What to test next
7. Whether stacking is justified
8. Whether notebook wiring / path parity still needs a follow-up before calling the cycle complete
