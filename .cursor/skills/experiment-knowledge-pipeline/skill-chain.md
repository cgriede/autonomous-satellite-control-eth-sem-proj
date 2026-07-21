# Experiment pipeline — skill chain

How numbered pipeline experiments wire into existing experimentation skills.  
**Orchestrator:** [`SKILL.md`](SKILL.md) · **Templates:** [`reference.md`](reference.md)

## Chain overview

```text
/init-experiment
    ↓
Phase 0 ── hypothesis-research-literature, isolated-notebook-hypotheses (planning contract)
    ↓ /document-experiment-step → append ## Phase 0
Phase 1 ── hypothesis-experiment-cycle (fork, smoke, JSON contract, charter)
    ↓
Phase 2 ── hypothesis-experiment-cycle (run arms) + long-run-watch + video export + visual-output-verification + video-frame-inspect (hard evidence)
    ↓
Phase 3 ── hypothesis-experiment-cycle (analysis card) + document-research + video-frame-inspect (if video claims)
    ↓
Phase 4 ── document-research + visual-output-verification + video-frame-inspect (human-facing archive)
    ↓ /close-experiment-step → 4-documentation/
```

**Legacy pointer:** [`isolated-notebook-hypotheses`](../isolated-notebook-hypotheses/SKILL.md) — same fixed JSON contract and 8-section analysis card; notebook path under `hypotheses/`. Pipeline ML runs use [`hypothesis-experiment-cycle`](../hypothesis-experiment-cycle/SKILL.md) under `backend/scripts/experiments/<slug>/`.

---

## Per-phase skill map

| Phase | Primary skills | Supporting skills |
|-------|----------------|-------------------|
| **0** | [`hypothesis-research-literature`](../hypothesis-research-literature/SKILL.md) | [`isolated-notebook-hypotheses`](../isolated-notebook-hypotheses/SKILL.md) § Before launching branches (README, `<hypothesis>.md`, SUBAGENT_CHARTER, label contract) |
| **1** | [`hypothesis-experiment-cycle`](../hypothesis-experiment-cycle/SKILL.md) | `isolated-notebook-hypotheses` § Fixed result contract, evidence-first rule, fork checklist |
| **2** | [`hypothesis-experiment-cycle`](../hypothesis-experiment-cycle/SKILL.md) | [`long-run-watch`](../long-run-watch/SKILL.md), [`visual-output-verification`](../visual-output-verification/SKILL.md), [`video-frame-inspect`](../video-frame-inspect/SKILL.md) |
| **3** | [`document-research`](../document-research/SKILL.md) | `hypothesis-experiment-cycle` + `isolated-notebook-hypotheses` § Per-hypothesis analysis card (§1–8), `video-frame-inspect` when verdict uses video |
| **4** | [`document-research`](../document-research/SKILL.md) | `visual-output-verification`, `video-frame-inspect`, [`minimal-feature-review`](../minimal-feature-review/SKILL.md) § human confirm before ship |

---

## Per-subsection: what to run

### Phase 0

| Subsection | Skills / artifacts |
|------------|-------------------|
| **0.1 Experiment scope** | Pipeline only; align with `<hypothesis>.md` falsification criteria (`isolated-notebook-hypotheses`) |
| **0.2 Thought process** | `document-research` mindset — reasoning chain, rejected/deferred paths |
| **0.2.1 Shoulders of giants** | `hypothesis-research-literature` → `LITERATURE_HIGHLIGHTS`, local PDFs |
| **0.3 Preliminary implementation remarks** | `hypothesis-experiment-cycle` § ponytail rule — hook point, sibling scaffold, smoke plan |

### Phase 1

| Subsection | Skills / artifacts |
|------------|-------------------|
| **1.1 Build plan** | `isolated-notebook-hypotheses` § Before launching branches + `hypothesis-experiment-cycle` layout |
| **1.2 Build implementation** | `hypothesis-experiment-cycle` minimal fork; `write_hypothesis_result` / smoke JSON |
| **1.3 Run instructions** | SUBAGENT_CHARTER run commands; `pipeline_run_guard`; list **expected artifacts** (JSON, analysis card, optional videos) |

### Phase 2

| Subsection | Skills / artifacts |
|------------|-------------------|
| **2.1 Run scope** | Frozen knobs from `_frozen_baseline.py`; arms from `<hypothesis>.md` |
| **2.2 Run monitoring** | `long-run-watch` for multi-hour jobs; mutex via `pipeline_run_guard` |
| **2.3 Run log & artifacts** | Per-arm `results/*.json`, `run_dir`, `artifacts_manifest` if training workflow exports videos/plots |

**After KPI JSON exists — visual hard evidence (required when behavior is in scope or training exported video):**

1. Confirm video/plot paths under `run_dir/videos/`, `artifacts_manifest.json`, or `results/plots/`.
2. [`video-frame-inspect`](../video-frame-inspect/SKILL.md) — extract PNGs from `.mp4`; Read frames; reconcile pointing/shutters/capture with KPIs **before** Phase 3 verdict language.
3. [`visual-output-verification`](../visual-output-verification/SKILL.md) — agent pre-check on frames/plots.

Record **full artifact paths**, `video-frame-inspect` manifest path, and 3–5 frame observations in **2.3**. KPI JSON alone is insufficient for behavioral claims. User confirms MP4/plots before Phase 4 ship.

### Phase 3

| Subsection | Skills / artifacts |
|------------|-------------------|
| **3.1 Claims & success criteria** | From Phase 0.1; one row per claim in verdict table |
| **3.2 Evidence summary** | Quantitative: JSON + analysis card §3–5. Qualitative: `video-frame-inspect` findings cited in prose |
| **3.3 Verdict table** | Match `isolated-notebook-hypotheses` verdict vocabulary (`supported` / `falsified` / `inconclusive`) |

**Required fork artifacts before close Phase 3:**

- `results/<experiment_id>_summary.json` (or slug-specific summary)
- `results/<hypothesis_id>_analysis.md` — 8-section card (`isolated-notebook-hypotheses` template)
- Link paths in Phase 3.2 / 3.3

Then [`document-research`](../document-research/SKILL.md) may draft investigation note — **after** pipeline Phase 3 block is appended.

### Phase 4 (human-facing)

| Subsection | Skills / artifacts |
|------------|-------------------|
| **4.1 Promotion & integration** | `hypothesis-experiment-cycle` § Promotion — minimal diff only; DECISIONS rows |
| **4.2 Closeout rationale** | `document-research` — why + optional follow-up experiment |
| **4.3 Knowledge persistence** | Full persistence checklist below |

**4.3 persistence checklist (How):**

| Layer | Path / action |
|-------|----------------|
| Pipeline record | `docs/experiments/pipeline/4-documentation/{NN}-{slug}.md` |
| Investigation | `docs/research/*-investigation.md` |
| Decisions | `docs/research/DECISIONS.md` |
| STATUS | `docs/ml/experiments/STATUS_*.md` |
| Fork analysis | `backend/scripts/experiments/<slug>/*_analysis.md` |
| Report archive | **Curated** videos/plots for the semester report — copy selected assets into `docs/report/semester-project/figures/` and tag sections in `FIGURES_TODO.md`; list provenance paths (e.g. `run_dir/videos/eval_best.mp4`, `results/plots/`). Do **not** dump the full experiment tree into the report folder (learnings.md `report-figure-curate-not-dump`). Vision-check caption↔process and hash/return-curve integrity before wiring (`report-figure-caption-process-match`, `report-figure-artifact-integrity`) |
| Visual gate | `visual-output-verification` on report-facing frames; `video-frame-inspect` manifest paths in 4.3 |
| Human sign-off | User confirms artifacts before calling experiment closed ([`minimal-feature-review`](../minimal-feature-review/SKILL.md)) |

Do **not** mark Phase 4 done from code inspection alone when the experiment produced video or plots.

---

## Fixed contracts (shared across skills)

From `isolated-notebook-hypotheses` / `hypothesis-experiment-cycle` — every pipeline fork should produce:

1. **JSON** — `write_hypothesis_result(...)` shape (`frozen_input`, `control`/`treatment`, `delta`, `verdict`, …)
2. **Analysis card** — `results/<hypothesis_id>_analysis.md` sections 1–8
3. **SUBAGENT_CHARTER** — protected vs editable paths
4. **Smoke** — before Phase 2 full matrix

Pipeline Phase blocks **summarize and link** these; they do not replace fork-local files.

---

## Known platform debt

| Issue | Affects | Action |
|-------|---------|--------|
| **Training-run video export** ([D-013](../../../docs/research/DECISIONS.md)) | All pipeline Phases 2–4 | **Science:** videos are behavioral hard evidence — keep workflow defaults unless user opts into trim ([`experiment-visual-evidence`](../../rules/experiment-visual-evidence.mdc)). **Perf:** frontend/render agent improves MP4 encode (`training_workflow`, `training_run_artifacts`, `backend/render/`). Document export mode + paths in Phase 2.3. |

---

## Anti-patterns

- Closing Phase 2 without listing video/plot paths when `background_artifacts` or workflow exported them
- Phase 3 verdict from KPI JSON only while user-visible behavior was never frame-checked
- Phase 4.3 that says “videos exist” without paths + `video-frame-inspect` manifest
- Rewriting prior `## Phase N` blocks when appending documentation
- Using `isolated-notebook-hypotheses` notebook `hypotheses/` layout for ML pipeline slugs (use `backend/scripts/experiments/`)
