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

## Workflow

1. **Activate ASC** (`conda activate ASC`).
2. **Run the extractor** (from repo root):

```bash
python .cursor/tools/video_frame_inspect/extract_frames.py PATH/to/video.mp4 --count 8
```

3. **Read** `.cursor/video_frame_inspect/data/<run_id>/manifest.json`.
4. **Read** selected `frame_*.png` files listed in the manifest (vision).
5. State findings from the images; do not ask the user to describe frames unless extraction failed.

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
- If OpenCV cannot open the file, check path and that `opencv-python` is installed in ASC.
