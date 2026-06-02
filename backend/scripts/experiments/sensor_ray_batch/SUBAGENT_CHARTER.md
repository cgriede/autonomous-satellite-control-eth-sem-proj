# Subagent charter — sensor ray batch

## Protected paths (read-only during experiments)

- `backend/simulation/camera_2d.py` (until promotion)
- `backend/simulation/sensor_kernel.py` (until promotion)
- `backend/notebooks/s01/**`
- `backend/render/**`

## Editable paths

| Branch | May edit |
|--------|----------|
| orchestrator | `_runner_common.py`, `_frozen_baseline.py`, `run_baseline.py`, `results/` |
| C fuse | `c_fuse_cameras/sensor_kernel_fork.py`, `c_fuse_cameras/run_c1.py`, `c_fuse_cameras/results/` |
| D tensor | `d_tensor_clouds/camera_2d_fork.py`, `d_tensor_clouds/run_d1.py`, `d_tensor_clouds/results/` |
| promote | production modules + tests |

## Deliverables

- `results/baseline.json`, `c_fuse_cameras/results/c1.json`, `d_tensor_clouds/results/d1.json`
- `results/fuse_cameras_analysis.md`, `results/tensor_clouds_analysis.md`
- Verdict per hypothesis: supported / falsified / inconclusive

## Constraints

- One logical change per branch
- Max 3 full runs after baseline per branch
- No destructive git operations
- Do not edit the same fork file from two branches
