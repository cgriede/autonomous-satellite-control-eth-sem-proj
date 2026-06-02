# Video export experiments

Isolated hypothesis cycle for **MP4 export wall time** (matplotlib draw dominates; encode is ~3%).

Production `backend/render/*` stays read-only until promotion.

## Profile context

Prior `sim_timing --with-render` on `high_cloud` (~63 clouds):

| Phase | Wall time |
|-------|-----------|
| Sim loop | ~10 s |
| Export (`save_one_pass_video_30x`) | ~82 s |
| Per-frame draw | ~83 ms |
| Per-frame OpenCV write | ~2.5 ms |

## Frozen fixture

| Fixture | Source |
|---------|--------|
| `high_cloud_notebook` | `sensor_ray_batch/_frozen_baseline.build_high_cloud_setup()` |

Same coast episode as notebook `02-clouds.ipynb` export cell.

## Hypotheses

| ID | Branch | Change | Speed gate |
|----|--------|--------|------------|
| A | `a_frame_stride/` | `frame_stride=2` (half matplotlib draws) | ≥1.5× export speedup |
| B | `b_lite_layout/` | Hide telemetry / reward / torque / secondary cam strip | ≥1.2× export speedup |

Parity for export: **H.264 output** required; visual/layout differences documented per branch.

## Run commands (repo root, PowerShell)

```powershell
conda activate ASC; python backend/scripts/experiments/video_export/run_baseline.py
conda activate ASC; python backend/scripts/experiments/video_export/a_frame_stride/run_a1.py
conda activate ASC; python backend/scripts/experiments/video_export/b_lite_layout/run_b1.py
```

Each export run is ~80–90 s on the reference machine (862–950 frames @ ~10 fps draw).

## Layout

| Path | Purpose |
|------|---------|
| `_frozen_baseline.py` | High-cloud setup + sim config |
| `_runner_common.py` | Export bench, codec probe, JSON contract |
| `_export_fork.py` | Forked save loop (stride param) |
| `run_baseline.py` | Production export baseline |
| `a_frame_stride/` | Hypothesis A |
| `b_lite_layout/` | Hypothesis B |
| `results/` | baseline.json, analysis cards, preview MP4s |

## KPIs

- `export_wall_s` — full `render_from_series(EXPORT)` wall time
- `export_frames_per_s` — frames drawn / export_wall_s
- `n_frames_drawn` — matplotlib draw count
- `video.codec` — must include `h264` after re-encode

## Related

- [`sim_timing/README.md`](../sim_timing/README.md) — episode + optional `--with-render`
- Notebook playback: `backend/utils/notebook/video.py` (`ensure_notebook_playable_mp4`, `file://` URI)
