---
name: create-update-presentation
description: >-
  Create or update a PowerPoint deck via slides_manifest.json and
  .cursor/tools/presentation/. Read the current deck, research the repo for
  facts, apply user-guided improvements (slide picks, clarifications, evidence),
  then rebuild .pptx. Use when the user says create-update-presentation,
  update the presentation, improve slides, add evidence to the deck, or asks
  questions meant to land in tomorrow's slides.
---

# Create / Update Presentation

Iterative deck workflow: **read manifest → user guidance → research → patch via CLI → build**.

Tools live in [`.cursor/tools/presentation/`](../../tools/presentation/) — see [build-tool](../build-tool/SKILL.md). **Never** edit `.pptx` by hand in chat; edit `slides_manifest.json` through the tool, then `build`.

## Default deck (this repo)

| Artifact | Path |
|----------|------|
| Manifest (source of truth) | `docs/presentation/final/with-cursor/slides_manifest.json` |
| Output | `docs/presentation/final/with-cursor/work_review_with_cursor.pptx` |
| Diagrams | `docs/presentation/final/with-cursor/diagrams/` |
| Technical record (cite, don't duplicate blindly) | `docs/presentation/*.md` |

Override with `--manifest` / `--output` on the CLI when the user names another deck.

## Preflight (mandatory)

```powershell
conda activate auto-sat
python .cursor/tools/presentation/presentation_pptx.py check
python .cursor/tools/presentation/presentation_pptx.py list
```

Read `slides_manifest.json` for slide ids the user cares about. If check fails, run `init --force` only when bootstrapping a **new** deck — not when updating an existing one.

## Workflow

### 1. Anchor on user guidance

What did the user ask to improve? Examples:

- Clarify a slide topic ("explain SafetyController on M12")
- Add experiment results / numbers from a run folder
- Embed video evidence (paths + frame stills on backup slides)
- Fix wording, scope, or hypothesis status
- New slides or diagram updates

If scope is broad, use **AskQuestion** with slide-id options (A/B/C per slide) — same pattern as initial deck planning. If narrow, go straight to research.

**Do not invent numbers.** Pull from code, `docs/presentation/`, experiment pipeline docs, `summary_metrics.json`, `run_log.md`, or runs under `backend/autonomous_control/runs/`.

### 2. Read current presentation state

1. `list` — see all slide ids, sections (`main` / `admin` / `backup`), status.
2. Read manifest JSON for target slides (`title`, `bullets`, `notes`, `image`).
3. Optional: user has `.pptx` open — treat manifest as authoritative; pptx is build output.

### 3. Research (evidence-first)

| Claim type | Search |
|------------|--------|
| Constants, reward, ML | `docs/presentation/machine-learning.md`, `technical-constants.md`, `environment-hyperparameters.md` |
| Experiment verdicts | `docs/experiments/pipeline/`, `docs/ml/STATUS_*.md`, `backend/scripts/experiments/*/results/` |
| Behavior / pointing | [video-frame-inspect](../video-frame-inspect/SKILL.md) on run MP4s |
| Architecture | `docs/project-charter.md`, code cited in existing slides |

For behavioral slides (M17, backup B01–B02): extract frames, inspect, then `append` concrete findings to bullets — cite manifest path and run id.

### 4. Patch manifest (tools only)

```powershell
# Replace bullets
python .cursor/tools/presentation/presentation_pptx.py set --id M12 --bullets "Line one|Line two|Line three"

# Add without wiping
python .cursor/tools/presentation/presentation_pptx.py append --id M17 --bullets "eval_best.mp4: cloud avoidance at t=10.75s"

# Title / notes / status
python .cursor/tools/presentation/presentation_pptx.py set --id M16 --title "Exp 4 — vector OBC results" --status draft

# Flowcharts changed
python .cursor/tools/presentation/presentation_pptx.py diagrams
```

Edit `.mmd` under `diagrams/` when structure changes; then `diagrams` + `build`.

Mathematical or definition changes: also update matching `docs/presentation/` slideshow per [math-physics-technical-docs](../../rules/math-physics-technical-docs.mdc).

### 5. Build and verify

```powershell
python .cursor/tools/presentation/presentation_pptx.py check
python .cursor/tools/presentation/presentation_pptx.py build
```

Confirm `Wrote ...work_review_with_cursor.pptx`. Tell the user which slide ids changed and the full path to the pptx.

### 6. Close the loop

Short summary:

- Slides updated (ids + one line each)
- Sources cited (file paths, run ids)
- What still needs **user** action (admin placeholders A01–A02, embed video in PowerPoint UI, diagram polish)

Do not commit unless asked.

## Slide id conventions (default deck)

| Prefix | Section |
|--------|---------|
| `M##` | Main narrative |
| `A##` | Admin placeholders — user fills |
| `B##` | Backup / appendix — extra videos, plots, cross-maps |

## When to extend the tool

If you need the same mutation repeatedly (e.g. `set-row` for backlog), extend `.cursor/tools/presentation/presentation_pptx.py` per [build-tool](../build-tool/SKILL.md) — do not run one-off Python in chat.

## Related

- Tool catalog: [build-tool](../build-tool/SKILL.md)
- CLI detail: [reference.md](reference.md)
- Video evidence: [video-frame-inspect](../video-frame-inspect/SKILL.md)
- Visual claims: [experiment-visual-evidence](../../rules/experiment-visual-evidence.mdc)
