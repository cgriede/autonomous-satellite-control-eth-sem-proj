# Analysis — frame_stride

## 1. Hypothesis
Export frame_stride=2 on high_cloud notebook fixture

## 2. Frozen input
- Scenario: high_cloud_notebook
- Clouds: 1200

## 3. Control KPI
- export_wall_s: 78.2032395999413
- export_frames_per_s: 11.022561269963642
- n_frames_drawn: 862

## 4. Treatment KPI
- export_wall_s: 39.09772159997374
- export_frames_per_s: 11.049237201594124
- n_frames_drawn: 432

## 5. Delta
- export_speedup: 2.000199408039005
- relative_wall_reduction_pct: 50.00498470398011

## 6. Parity
- passed: True
- notes: H.264 output required; temporal subsampling by design (coarser motion)

## 7. Verdict
- supported

## 8. Closeout
promote
