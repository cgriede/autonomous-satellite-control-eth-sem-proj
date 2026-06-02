# Subagent charter — cloud kernel speed

## Protected paths (read-only during experiments)

- `backend/simulation/camera_2d.py` (until promotion)
- `backend/notebooks/s01/**`
- `backend/render/**`

## Editable paths

| Branch | May edit |
|--------|----------|
| baseline | `_runner_common.py`, `run_baseline.py`, `results/` |
| A1 | `a_vectorized_line/camera_2d_fork.py`, `a_vectorized_line/run_a1.py`, `a_vectorized_line/results/` |
| B1 | `b_fov_cull/camera_2d_fork.py`, `b_fov_cull/cloud_cull.py`, `b_fov_cull/run_b1.py`, `b_fov_cull/results/` |
| promote | `backend/simulation/camera_2d.py`, `backend/utils/geometry/orbit_disk_wgs84.py`, tests, benchmark script |

## Deliverables

- `results/baseline.json`, `a_vectorized_line/results/a1.json`, `b_fov_cull/results/b1.json`
- Verdict per phase: supported / falsified / inconclusive
- Minimal production diff on promotion

## Constraints

- One logical change per branch
- Max 3 full runs after baseline per branch
- No destructive git operations
