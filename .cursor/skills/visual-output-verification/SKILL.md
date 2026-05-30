---
name: visual-output-verification
description: Verify generated visual artifacts with OCR or computer-vision inspection before declaring a visual task done. Use when a change affects plots, figures, renders, screenshots, videos, or UI screens.
---

# Visual Output Verification

Use this skill whenever the task changes what a human will see.

## Verification loop

1. Run the code and produce a concrete artifact such as an image, screenshot, frame export, or video.
2. Inspect that artifact with OCR or computer-vision tooling before finishing.
3. Confirm required labels, annotations, symbols, or UI text are present and readable.
4. Check contrast and visibility; avoid hard-to-read combinations such as bright text on bright backgrounds.
5. If anything is missing or unclear, iterate and verify again.

## Done criterion

Do not mark the task complete based only on code inspection when the requested outcome is visual.
