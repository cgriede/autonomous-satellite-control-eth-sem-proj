# Subagent charter — video export

## Protected paths (read-only during experiments)

- `backend/render/**` (until promotion)
- `backend/simulation/**`
- `backend/notebooks/**`

## Editable paths

| Branch | May edit |
|--------|----------|
| orchestrator | `_runner_common.py`, `_export_fork.py`, `_frozen_baseline.py`, `run_baseline.py`, `results/` |
| A frame stride | `a_frame_stride/render_export_fork.py`, `a_frame_stride/run_a1.py`, `a_frame_stride/results/` |
| B lite layout | `b_lite_layout/render_export_fork.py`, `b_lite_layout/run_b1.py`, `b_lite_layout/results/` |
| notebook display | `backend/utils/notebook/video.py` (playback fix, not export logic) |

## Deliverables

- `results/baseline.json`
- `a_frame_stride/results/a1.json`, `b_lite_layout/results/b1.json`
- `results/frame_stride_analysis.md`, `results/lite_layout_analysis.md`
- Verdict per hypothesis: supported / falsified / inconclusive

## Constraints

- One logical change per branch
- Max 3 full runs after baseline per branch
- Re-use frozen sim series within a run script (sim once, export once per treatment)
- Speed gates: A ≥1.5×, B ≥1.2× on `export_wall_s`
