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
