# Target Pointing: Baseline model, bugs

**Source:** `Target Pointing Baseline model, bugs.pdf`  
**Date on document:** Wednesday, 24 June 2026  
**Transcription run:** `hand_transcriptions/00__Target Pointing Baseline model, bugs.json`  
**Status:** **Fixed** (2026-06-24)

## Summary

Baseline target-pointing bug report. Nadir approach looks correct. On first target-pointing engagement the satellite slewed toward approximately the **10th target** along the track instead of the first/closest target.

**Resolution:** fixed — first engage now uses `active_target_index` 0 and `policy.active_anchor()` when switching OBC to target mode (`baseline_overflight.py`).

**Still open (from notes):** green-circled nadir footprint areas flagged as suspicious for missing clouds.

## Page 1

### Typed captions

1. **On approach: nadir pointing, ok**
2. **First target pointing: moves to ~10th target not to the first / closest**

### Handwriting

- **No clouds in green areas, suspicious** (top screenshot)
- **Expected this** (middle screenshot, arrow to farther target)

### Figure notes

**Top screenshot** — nadir approach; two green circles on the blue sensor footprint; annotator expects clouds in those regions.

**Middle screenshot** — `sequential_target_baseline` at frame ~672; altitude ~548 km; z off-nadir ~−42.6°; active target 0; green arrow points to a red target dot far along the ground track rather than the nearest target.
