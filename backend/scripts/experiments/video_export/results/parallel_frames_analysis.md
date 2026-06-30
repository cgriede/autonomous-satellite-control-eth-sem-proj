# Analysis — parallel_frames

## 1. Hypothesis
Parallel frame export with 8 CPU workers + NVENC lane

## 2. Frozen input
- Scenario: training_sparse
- Clouds: ?

## 3. Control KPI
- export_wall_s: 30.965749299997697
- export_frames_per_s: 9.300598451852139
- n_frames_drawn: 288

## 4. Treatment KPI
- export_wall_s: 17.643345099990256
- export_frames_per_s: 16.323435174442007
- n_frames_drawn: 288

## 5. Delta
- export_speedup: 1.7550951434949147
- relative_wall_reduction_pct: None

## 6. Parity
- passed: True
- notes: H.264 required

## 7. Verdict
- supported

## 8. Closeout
promote
