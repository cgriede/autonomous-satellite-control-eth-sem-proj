# Video frame inspect (agent tool)

Extract PNG snapshots from MP4 exports so the agent can **read images** (vision) without playing video in chat.

## Output location

```
.cursor/video_frame_inspect/data/<run_id>/
  manifest.json
  frame_000000_t0.00s.png
  frame_000512_t25.60s_sim1148.png
```

`data/` is gitignored.

## Requirements

- Conda env **ASC**
- `opencv-python` (repo `requirements.txt`)

## Examples

```bash
conda activate ASC

# Six evenly spaced frames (default if no selectors)
python .cursor/tools/video_frame_inspect/extract_frames.py backend/notebooks/s01/artifacts/07-baseline-overflight.mp4

# Explicit video frame indices
python .cursor/tools/video_frame_inspect/extract_frames.py video.mp4 --frames 0,200,400

# Percentages along the timeline
python .cursor/tools/video_frame_inspect/extract_frames.py video.mp4 --percent 0,50,100

# Map simulation step indices → video frames (render EXPORT pipeline)
python .cursor/tools/video_frame_inspect/extract_frames.py video.mp4 \
  --sim-steps 0,1148,2522 \
  --sim-n-steps 2523 \
  --sim-total-s 65.4
```

Then read `manifest.json` and open specific `.png` files with the agent **Read** tool.

## Sim-step mapping

Uses the same time stride as `render/render_main.py::save_one_pass_video_30x`:

- `dt_sim_s = (animation_interval_ms / 1000) * export_speed_multiplier`
- Defaults: 50 ms × 30 = 1.5 s sim-time per video frame

Pass `--sim-total-s` from `rollout.series.metadata.sim_total_s` (or last `t_s` value).
