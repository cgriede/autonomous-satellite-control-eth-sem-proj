# Hypothesis analysis: tensor_clouds

## 1. Question

Does replacing the per-cloud Python loop in `_batch_cloud_hits_t_best` with a vectorized `(n_clouds × n_rays)` tensor pass improve line-kernel speed at high cloud counts without changing observation codes?

## 2. Frozen input

| Field | Value |
|-------|-------|
| Scenario | high_cloud_notebook + low_cloud guardrail |
| Seed / fixture | seed=42, `fixtures/high_cloud_seed42.pkl` (63 clouds) |
| Key tunables | production bin counts, accelerated backend |
| N (items/clouds/charts/rows) | 63 high / 5 low clouds |

## 3. KPI table

| Arm | line_s_per_call @ 63 clouds | low_cloud micro total_s | parity mismatches |
|-----|----------------------------|-------------------------|-------------------|
| Control (baseline) | 0.00229 s | 0.348 s | — |
| Treatment (D1 tensor) | 0.00078 s | 0.306 s | 0 |
| Delta | **2.94× faster** | **0.88× (12% faster)** | 0 |

## 4. Evidence (real examples)

- Low fixture parity: ref/cand ASCII both `EEEE...` (100 bins), mismatches=0.
- High fixture parity: ref/cand ASCII both `EEEE...` (100 bins), mismatches=0.
- `low_regression_factor=0.88` — faster at 5 clouds, no regression.
- RuntimeWarning on all-NaN slice when no cloud hit (harmless; same NaN semantics as production).

## 5. Interpretation

- **Primary KPI:** production 0.00229 s → tensor 0.00078 s per line call (2.94×); direction = better; within noise = no.
- **Guardrails:** parity exact on low and high fixtures; low-cloud guardrail improved not regressed.
- **Why:** `(C, N)` broadcast eliminates Python loop over clouds and repeated batch temporaries.

## 6. Verdict

**supported** — 2.94× line speedup exceeds 2× bar with zero parity mismatches.

## 7. Closeout

| Action | Item |
|--------|------|
| Promote now | **Done** — promoted to `backend/simulation/camera_2d.py` |
| Keep as idea | — |
| Delete / archive | fork optional for regression |
| Test next | — |
| Stack with | fuse_cameras (also promoted) |

## 8. Path parity / caveats

Patch applied to `camera_2d._batch_cloud_hits_t_best` module attribute; production promotion replaces function body in `camera_2d.py`. `np.nanmin` all-NaN warning on rays with no cloud arc hit — consider `where=` guard on promote.
