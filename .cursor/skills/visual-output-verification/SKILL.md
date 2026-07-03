---
name: visual-output-verification
description: Verify generated visual artifacts with OCR or computer-vision inspection before declaring a visual task done. Use when a change affects plots, figures, renders, screenshots, videos, or UI screens.
---

# Visual Output Verification

Use this skill whenever the task changes what a human will see.

## Verification loop

1. Run the code and produce a concrete artifact such as an image, screenshot, frame export, or video.
2. Inspect that artifact with OCR or computer-vision tooling before finishing.
   - **Videos (`.mp4`)**: agents cannot read MP4 directly. Run [video-frame-inspect](../video-frame-inspect/SKILL.md) to export PNGs, then Read those images.
3. Confirm required labels, annotations, symbols, or UI text are present and readable.
4. Check contrast and visibility; avoid hard-to-read combinations such as bright text on bright backgrounds.
5. If anything is missing or unclear, iterate and verify again.

## Done criterion

Do not mark the task complete based only on code inspection when the requested outcome is visual.

**User approval:** Agent-side OCR/CV or regenerated MP4 is pre-check only. The **user** must confirm the artefact before commit or ship — see [minimal-feature-review](../minimal-feature-review/SKILL.md) Phase 5 and learnings.md `human-confirm-before-review-ship`.

## ML experiment pipeline

Always-applied rule: [experiment-visual-evidence](../../rules/experiment-visual-evidence.mdc) — KPI JSON for quick estimates; **video + frame inspect for behavioral claims**.

When working a numbered pipeline experiment ([`experiment-knowledge-pipeline`](../experiment-knowledge-pipeline/SKILL.md)):

| Phase | Use |
|-------|-----|
| **2** | **Required** when training exported video/plots or behavior is in scope — record paths + manifest in Phase **2.3**; if run used default trim, report **artifact gap** and do not claim behavioral evidence (see learnings.md `phase2-export-artifacts-not-trim-default`) |
| **3** | **Required** before qualitative claims in Phase **3.2** / verdict table |
| **4** | **Required** for report-archive artifacts in Phase **4.3** — user sign-off before `/close-experiment-step` |

**Chat / run review:** When discussing pipeline results before closeout, list full MP4 paths per arm (eval first) — see experiment-knowledge-pipeline SKILL.md § Discussing run results; learnings.md `pipeline-discuss-runs-include-video-paths`.

Pair with [`video-frame-inspect`](../video-frame-inspect/SKILL.md) for `.mp4`. Full map: [`skill-chain.md`](../experiment-knowledge-pipeline/skill-chain.md).
