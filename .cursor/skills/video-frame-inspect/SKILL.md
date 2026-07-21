---
name: video-frame-inspect
description: >-
  Extract PNG frames from MP4 videos for agent vision inspection. Use when you
  need to verify video content, debug renders, or analyze baseline/training
  exports without asking the user to describe frames.
---

# Video Frame Inspect

Agents cannot read `.mp4` binaries directly. Use this tool to export PNGs, then inspect them with the **Read** tool (vision).

## When to use

- Verifying render/export behavior (pointing, targets, telemetry overlays)
- Reconciling video appearance with simulation step indices
- Any task where `visual-output-verification` applies but the artifact is video
- **Pipeline Phase 2–4:** eval/train MP4 under `backend/autonomous_control/runs/<run_id>/videos/` — cite manifest in pipeline doc §2.3 / §4.3 ([`skill-chain.md`](../experiment-knowledge-pipeline/skill-chain.md)). Rule: [experiment-visual-evidence](../../rules/experiment-visual-evidence.mdc).
- **Pipeline chat review:** user watches MP4; agent lists full paths per [`experiment-knowledge-pipeline`](../experiment-knowledge-pipeline/SKILL.md) § Discussing run results — frame inspect is agent pre-check only.
- **Report figure freeze:** after inspect, curate selected frames into `docs/report/semester-project/figures/` — do not commit the full run dump (learnings.md `report-figure-curate-not-dump`).
- **Report panel pick:** when choosing frames for a multi-panel figure, confirm each candidate’s telem (off-nadir, safe-mode count, take-picture markers, torque request vs applied) matches that panel’s caption process — not merely “near the event” (learnings.md `report-figure-caption-process-match`).

## Workflow

1. **Activate env** (`conda activate auto-sat`).
2. **Run the extractor** (from repo root):

```bash
python .cursor/tools/video_frame_inspect/extract_frames.py PATH/to/video.mp4 --count 8
```

3. **Read** `.cursor/video_frame_inspect/data/<run_id>/manifest.json`.
4. **Read** selected `frame_*.png` files listed in the manifest (vision).
5. State findings from the images; do not ask the user to describe frames unless extraction failed.
6. **For report freeze:** if selecting among candidates, crop/read telem when needed; reject wrong-phase neighbors; keep subcaption names aligned with Methods vocabulary.

## Selectors

| Flag | Purpose |
|------|---------|
| `--count N` | N evenly spaced frames (default 6 if nothing else set) |
| `--frames 0,100,200` | Explicit video frame indices |
| `--percent 0,25,50,75,100` | Positions along timeline (%) |
| `--sim-steps 0,1148,2522` | Map rollout step → video frame (needs `--sim-n-steps`, `--sim-total-s`) |

For notebook rollouts:

```bash
python .cursor/tools/video_frame_inspect/extract_frames.py backend/notebooks/s01/artifacts/07-baseline-overflight.mp4 \
  --sim-steps 0,358,1148,1167,2522 \
  --sim-n-steps 2523 \
  --sim-total-s <from rollout.series.metadata.sim_total_s>
```

## Output contract

- Script: `.cursor/tools/video_frame_inspect/extract_frames.py`
- Data: `.cursor/video_frame_inspect/data/<run_id>/` (gitignored)
- Each run writes `manifest.json` with paths, frame indices, times, optional `sim_step`

## Notes

- User may watch full videos locally; frame PNGs are **for the agent only**.
- Sim-step mapping follows render `EXPORT` defaults (`animation_interval_ms=50`, `export_speed_multiplier=30`). Override flags if export used different constants.
- If OpenCV cannot open the file, check path and that `opencv-python` is installed in `auto-sat` (`conda activate auto-sat`).
