# Video export experiments

Isolated hypothesis cycle for **MP4 export wall time** (matplotlib draw dominates; encode is ~3%).

Production `backend/render/*` includes parallel export (`video_export_parallel.py`, default 8 workers).

## Frozen fixtures (no sim in iteration)

| Fixture ID | File | Role |
|------------|------|------|
| `gate` | `fixtures/gate_minimal.pkl.gz` | CI smoke (~5 sim steps) |
| `training_sparse` | `fixtures/training_sparse_episode.pkl.gz` | ML-primary benchmark |
| `high_cloud` | `fixtures/high_cloud_notebook.pkl.gz` | Regression / many-cloud |

**Bake once** (only entry point that runs simulation):

```powershell
conda activate auto-sat
python backend/scripts/experiments/video_export/bake_series_fixtures.py --all
```

**Bench loop** (pickle load + export only):

```powershell
conda activate auto-sat
python backend/scripts/experiments/video_export/run_bench.py --fixture gate
python backend/scripts/experiments/video_export/run_bench.py --fixture training_sparse
python backend/scripts/experiments/video_export/run_bench.py --fixture high_cloud --repeat 3
```

Parallel export patch:

```powershell
python backend/scripts/experiments/video_export/run_bench.py --fixture training_sparse --workers 8 --export-patch c_parallel_frames._export_fork:patched_save
```

## Hypotheses

| ID | Branch | Change |
|----|--------|--------|
| A | `a_frame_stride/` | `frame_stride=2` |
| B | `b_lite_layout/` | Lite dashboard panels |
| C | `c_parallel_frames/` | Parallel CPU draw + NVENC encode lane |
| D | `d_export_resolution/` | Explicit 1280×720 export |

## Baseline + hypothesis runners

```powershell
python backend/scripts/experiments/video_export/run_baseline.py
python backend/scripts/experiments/video_export/a_frame_stride/run_a1.py
python backend/scripts/experiments/video_export/b_lite_layout/run_b1.py
python backend/scripts/experiments/video_export/c_parallel_frames/run_c1.py
python backend/scripts/experiments/video_export/d_export_resolution/run_d1.py
python backend/scripts/experiments/video_export/run_training_episode_video_gate.py
```

## KPIs

- `export_wall_s` — full `render_from_series(EXPORT)` wall time
- `export_frames_per_s` — frames drawn / export_wall_s
- `n_frames_drawn` — matplotlib draw count
- `peak_rss_mb` — process high-water mark (when available)
- `video.width` / `video.height` — ffprobe (target 1280×720)
- `video.codec` — must include `h264`

## Export resolution

- `RENDER.export_pixel_width` = 1280, `RENDER.export_pixel_height` = 720
- `RENDER.export_workers` = 8 (parallel CPU draw; env `VIDEO_EXPORT_WORKERS` override)
- Manifest: `fixtures/manifest.json` (SHA256 per fixture)

## Tests

```powershell
conda activate auto-sat
cd backend
python -m pytest tests/test_video_export_fixtures.py -q
```
