---
name: experiment-knowledge-pipeline
description: >-
  Orchestrates ML pipeline experiments: five phases (0–4), each documented as one
  append-only block (What / Why / How subsections) in docs/experiments/pipeline/{bin}/{NN}-{slug}.md.
  Use /init-experiment, /start-experiment-step, /document-experiment-step (append phase),
  /close-experiment-step (advance phase + bin move). Chains hypothesis-research-literature,
  hypothesis-experiment-cycle, long-run-watch, document-research, isolated-notebook-hypotheses,
  visual-output-verification, video-frame-inspect. Global run mutex via pipeline_run_guard.
disable-model-invocation: false
---

# Experiment Knowledge Pipeline

**One experiment = one markdown file** under [`docs/experiments/pipeline/{bin}/`](../../../docs/experiments/pipeline/).  
**One slug = one atomic hypothesis** — do not mix independent directions (e.g. cadence + hyperparams) in one charter; see learnings.md `atomic-one-hypothesis-per-pipeline-slug`.  
**Index only:** [`README.md`](../../../docs/experiments/pipeline/README.md).

## Core doc rule (mandatory)

**Append only — never rewrite a closed phase.**

- Each **phase** is one top-level block: `## Phase N — …` with **three numbered subsections** (What / Why / How).
- `/document-experiment-step` **appends** the block for the **current** phase only.
- Prior `## Phase 0` … `## Phase N-1` blocks are **read-only** after `/close-experiment-step`.
- Do **not** pre-fill future phases or backfill multiple phases in one write (unless user explicitly requests a migration).

Read [`reference.md`](reference.md) for subsection templates and [`skill-chain.md`](skill-chain.md) for **which child skill to invoke per phase**.

## Skill chain (summary)

```text
Phase 0 → hypothesis-research-literature + planning contract (isolated-notebook-hypotheses)
Phase 1 → hypothesis-experiment-cycle (fork, smoke, JSON + analysis card scaffold)
Phase 2 → hypothesis-experiment-cycle + long-run-watch; spot-check visuals (video-frame-inspect)
Phase 3 → analysis card + document-research; video-frame-inspect if verdict uses video evidence
Phase 4 → document-research + visual-output-verification + report archive (human sign-off)
```

Full per-subsection map: [`skill-chain.md`](skill-chain.md).

## Phases and bins

| Phase | Bin folder | Top-level heading | When it closes |
|-------|------------|-------------------|----------------|
| **0** | `0-initialized/` | `## Phase 0 — Initialized` | Scope + rationale + feasibility frozen |
| **1** | `1-built/` | `## Phase 1 — Built` | Fork scaffolded; smoke passes |
| **2** | `2-run/` | `## Phase 2 — Run` | All arms executed; KPIs recorded |
| **3** | `3-evaluation/` | `## Phase 3 — Evaluation` | Verdict table complete |
| **4** | `4-documentation/` | `## Phase 4 — Documentation` | Promotion + persistence recorded |

`current_phase` in frontmatter is **0–4**. Bin must match `current_phase` (see [`reference.md`](reference.md) § Bin resolver).

## Commands

| Command | Action |
|---------|--------|
| `/init-experiment` | Create `0-initialized/{NN}-{slug}.md` with frontmatter + title only (**no phase body**); if scope has two independent tracks → **AskQuestion** to split into two slugs before Phase 0.1 |
| `/start-experiment-step` | Work on **current phase** — delegate to child skill; set `phases.<N>.status: in_progress` |
| `/document-experiment-step` | **Append** `## Phase N` + all mandatory subsections for current phase |
| `/close-experiment-step` | Verify phase block exists → `phases.<N>.status: done` → advance `current_phase` → **`pipeline_doc.py close-phase`** (bin move + README Doc link) → update README Phase/Verdict |

**Order:** finish work → `/document-experiment-step` → `/close-experiment-step`. Do not close without documenting.

**Proactive close (no slash command required):** When a run is complete and you deliver **evaluation / verdict / operator review** in chat, treat that as the close trigger — append missing `## Phase 2` and/or `## Phase 3` blocks, then run `pipeline_doc.py close-phase` for each completed phase. Never leave the doc in `2-run/` while discussing Phase 3 verdicts (see learnings.md `pipeline-advance-after-run-evaluation`).

## Phase → child skill map

| Phase | Primary skills | Also use |
|-------|----------------|----------|
| **0** | [`hypothesis-research-literature`](../hypothesis-research-literature/SKILL.md) | [`isolated-notebook-hypotheses`](../isolated-notebook-hypotheses/SKILL.md) § Before launching branches |
| **1** | [`hypothesis-experiment-cycle`](../hypothesis-experiment-cycle/SKILL.md) | `isolated-notebook-hypotheses` § Fixed result contract, evidence-first; **[`review-experiment-build`](../review-experiment-build/SKILL.md) after smoke** for complex experiments (new actor architecture, custom action space, custom episode loop, off-policy buffer rewiring) — catches zero-gradient and Jacobian bugs before compute spend; when smoke is single-episode only, `--verify` must bind stage-runner symbols (`screen-runner-smoke-wiring`)
| **2** | `hypothesis-experiment-cycle` | [`long-run-watch`](../long-run-watch/SKILL.md), [`visual-output-verification`](../visual-output-verification/SKILL.md), [`video-frame-inspect`](../video-frame-inspect/SKILL.md) — confirm completion JSON before treating live terminal as the canonical run (see learnings.md `check-completion-json-before-live-terminal`) |
| **3** | [`document-research`](../document-research/SKILL.md) | `hypothesis-experiment-cycle` + analysis card §1–8; `video-frame-inspect` if video informs verdict |
| **4** | `document-research` | `visual-output-verification`, `video-frame-inspect`, [`minimal-feature-review`](../minimal-feature-review/SKILL.md) (human confirm) |

## Workflow: start phase

```text
1. Locate docs/experiments/pipeline/*/{NN}-{slug}.md; read current_phase + phases.* in frontmatter
2. Confirm file is in the bin matching current_phase — run `python .cursor/tools/pipeline/pipeline_doc.py check`; fix with `sync-bin --slug <slug>` if needed.
3. Read PROJECT_KNOWLEDGE + DECISIONS + STATUS — respect blocked_by
4. Read skill-chain.md for current phase — invoke listed child skills
5. If current_phase == 2 → pipeline mutex check before launching training; if `profile.json` enables `export_episode_reward_plots` / `train_episode_videos`, launch commands must include **`--export-artifacts`** unless user opted **`--trim-artifacts`** (see learnings.md `phase2-export-artifacts-not-trim-default`)
6. Run phase checklist (reference.md)
7. Set phases.<N>.status: in_progress
8. Do NOT append the phase block until /document-experiment-step
9. Do NOT advance current_phase until /close-experiment-step
10. Semantic bugs (action space, warmup contract): **define fix in doc/chat first** — do not edit fork code until user agrees (see learnings.md `define-fix-before-implement-experiment`).
11. **Phase 0 atomic scope gate:** If Phase 0.1 names **two independent tracks** (different knobs, claims, or overnight queues — e.g. cadence + hparam screen), use **AskQuestion** — default is **split** into two `/init-experiment` slugs; only continue single-slug if user explicitly accepts sequential dependency **and** Phase 0.3 lists a runner step for every track (see learnings.md `atomic-one-hypothesis-per-pipeline-slug`).
12. **Phase 1 implement gate (Nike vs plan):** run before first fork edit — see § Implement mode below; never ask "do we need a build plan?" when signals already decide.
```

## Implement mode: Nike vs plan (Phase 1)

**Do not** routinely ask the user whether a dedicated build plan is needed — **run this gate** from the pipeline doc + user message. Phase **0.3** is the charter-level plan; Phase **1.1** records what was built at `/document-experiment-step` (not a separate plan doc).

### Nike mode — build now

Proceed when **all** hold:

| Signal | Check |
|--------|--------|
| Hook known | Phase 0.3 names hook point + smoke |
| Sibling exists | Copy scaffold from a prior slug (ponytail rule) |
| Single delta | One logical change; hypothesis doc states it in one sentence |
| User approved | `/start-experiment-step`, "fine to build", or Phase 0 closed with build intent |
| Fork-only | No production edit required ([D-003](../../../docs/research/DECISIONS.md)) |
| No contract risk | Not action-space / warmup / comparator-semantics bug (see `define-fix-before-implement-experiment`) |

**Required before first fork edit:** Tell the user you are in **Nike mode** and give **2–4 bullets** justifying why (e.g. "Phase 0.3 complete; Exp 8 sibling; one reward hook; smoke path known"). Do **not** silently start coding.

### Plan mode — stop; user must decide

**Never** agent-only decide. **Ask the user** (short build sketch or options) before coding when **any**:

- Phase 0.3 thin or hook / penalty design / knobs still **TBD**
- Multiple hooks or arms with different code surfaces
- No sibling scaffold; runner layout unclear
- Production edit may be required to run the hypothesis
- **Semantic or upstream bug suspected** — warmup vs train mismatch, invalid comparator run, workaround would mask prod/sim defect
- Cross-cutting change (sim + env + agent) beyond one hook

See also [`architecture-planning`](../architecture-planning/SKILL.md) for large non-pipeline design; pipeline Phase 1 usually does not need it when Nike criteria pass.

### Upstream bug suspicion

If the fork would **work around** a likely production/sim bug instead of testing the hypothesis → **stop and ask the user**: fix upstream first, defer the arm, or document an explicit workaround in DECISIONS. Do not silently paper over.

See learnings.md `pipeline-implement-nike-vs-plan-gate`.

## Workflow: document phase

```text
1. Confirm current_phase = N and phases.N not already documented (status != done)
2. Run any child skills not yet done for this phase (skill-chain.md) — e.g. analysis card before Phase 3 append
3. Append ## Phase N — … plus every mandatory ### subsection (reference.md)
3b. Phase 1: must include `### 1.3 Run instructions` — smoke + screen/full + eval commands, mutex, `results/` artifacts
4. Fill only this phase — leave earlier phases untouched
5. Phase 2: include video/plot paths in 2.3 if exported; note video-frame-inspect manifest if run
6. Phase 4: 4.3 must list report-archive paths + persistence layers (skill-chain.md checklist)
7. Optional: Follow-up experiment if inconclusive (0.3, 3.3, 4.2)
8. Set phases.<N>.documented_utc in frontmatter (status stays in_progress until close)
```

## Workflow: close phase

```text
1. Verify ## Phase N block exists and subsections are non-empty
1b. Phase 1 close: **require** `### 1.3 Run instructions (How to execute)` with copy-paste commands + artifact paths — README alone is insufficient (see learnings.md `phase1-run-instructions-required`)
2. phases.<N>: status=done, completed_utc
3. current_phase ← N+1 (or stay at 4 when finished)
4. Run `python .cursor/tools/pipeline/pipeline_doc.py close-phase --slug <slug>` (moves bin, updates README Doc link, fixes experiment README paths)
5. Update pipeline README **Phase** / **Verdict** columns manually if needed
6. Grep repo for any remaining stale paths
7. Phase 2 close: clear run_lock_holder
8. Phase 3 close: overall_verdict set in frontmatter
9. Phase 4 close: document-research + user visual sign-off per skill-chain.md
```

## Compute mutex (Phase 2 only)

**One ML pipeline training job per host** ([D-012](../../../docs/research/DECISIONS.md)).

| Mechanism | Path |
|-----------|------|
| Lock | `backend/scripts/experiments/.pipeline_run.lock` |
| Mirror | `docs/experiments/pipeline/.active_run.json` |
| Module | `backend/scripts/experiments/pipeline_run_guard.py` |

Before Phase 2 training: `check_pipeline_run_clear(slug)`. Each `_run_guard.py` calls `acquire_pipeline_run_lock`.

## Promotion boundary

Phase **4.1** records what (if anything) merges to production kernels. No production edits during Phases 0–3 without user-approved promote ([D-003](../../../docs/research/DECISIONS.md)).

**After a successful run or user “promote” request:** complete pipeline closeout first — append Phases 2–4, move doc to `4-documentation/`, set `overall_verdict`, update README + DECISIONS — **then** implement production promotion as a separate change. Never skip straight from KPI/video review to `reward.py` / `simulation/` edits (see learnings.md `pipeline-closeout-before-promote`).

## Discussing run results (chat + review)

When reporting pipeline run outcomes (overnight recap, arm comparison, Phase 2/3 prep), pair KPIs with **clickable video paths** — see learnings.md `pipeline-discuss-runs-include-video-paths` and [experiment-visual-evidence](../../rules/experiment-visual-evidence.mdc).

Per arm (from `run_dir/artifacts_manifest.json` or `config.json` → `artifact_paths`):

1. **Eval first:** `videos/eval_best.mp4`, then each `eval_ep_*_rank*.mp4` (verdict-relevant).
2. **Train highlights:** top-ranked `train_ep_*_rank*.mp4` from the manifest.
3. **Manifest:** full path to `artifacts_manifest.json` for closeout / frame inspect.

Agent may run [`video-frame-inspect`](../video-frame-inspect/SKILL.md) as pre-check; user watches MP4 for behavioral sign-off.

## Related skills

| Skill | Role in pipeline |
|-------|------------------|
| [`skill-chain.md`](skill-chain.md) | Full per-phase / per-subsection skill map |
| [`hypothesis-experiment-cycle`](../hypothesis-experiment-cycle/SKILL.md) | Phases 1–3 fork + run |
| [`isolated-notebook-hypotheses`](../isolated-notebook-hypotheses/SKILL.md) | JSON contract + analysis card template (legacy name; still authoritative) |
| [`visual-output-verification`](../visual-output-verification/SKILL.md) | Phases 2–4 visual gate |
| [`video-frame-inspect`](../video-frame-inspect/SKILL.md) | MP4 → PNG for agent + report citations |

## Related docs

- [STATUS board](../../../docs/ml/experiments/STATUS_2026-06.md)
- [DECISIONS](../../../docs/research/DECISIONS.md)
- [`python-runtime-environment`](../python-runtime-environment/SKILL.md) — `conda activate auto-sat`
