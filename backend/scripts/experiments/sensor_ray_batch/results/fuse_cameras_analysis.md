# Hypothesis analysis: fuse_cameras

## 1. Question

Does replacing three separate ray-march passes in `SensorKernel.evaluate` with one fused `_batch_first_hit_earth_or_clouds` call (~396 rays) improve per-step sensor cost without changing observation semantics?

## 2. Frozen input

| Field | Value |
|-------|-------|
| Scenario | s01 coast dual-camera |
| Seed / fixture | seed=0, low_cloud_dual (5 clouds) |
| Key tunables | 96 strip samples, 100 primary bins, 200 secondary bins |
| N (items/clouds/charts/rows) | 5 clouds, 1924 frames |

## 3. KPI table

| Arm | micro_sensor_evaluate.total_s (200 iters) | steps_per_s (episode) | parity mismatches |
|-----|-------------------------------------------|------------------------|-------------------|
| Control (baseline) | 0.385 s | 259.2 | — |
| Treatment (C1 fused) | 0.240 s | 304.8 | 0 |
| Delta | **1.61× faster** | **1.18× faster** | 0 |

## 4. Evidence (real examples)

- Parity: 8 snapshot cases, `total_mismatches=0`; ref/cand primary ASCII identical (e.g. all `-` for off-Earth snapshots).
- Episode frame 427 secondary: `-----------EEEEEEEEEXXEEEE...ECCCCCCCCCEEEEE...` — identical ref vs treatment.
- Episode frame 854 secondary: cloud bins `C` at `...EEEEEECEEEEEECCCEEEEE...` — identical ref vs treatment.
- `cloud_blocked_fraction=0.0` throughout primary; secondary cloud fractions match (e.g. 0.075 at frame 427).

## 5. Interpretation

- **Primary KPI:** 0.385 s → 0.240 s (1.61×); direction = better; within noise = no.
- **Guardrails:** parity exact; episode steps/s improved 259 → 305.
- **Why:** One fused cloud×earth batch replaces three separate `_batch_first_hit_earth_or_clouds` calls per timestep while footprint geometry uses cheap earth-only rays.

## 6. Verdict

**supported** — 1.61× micro speedup exceeds 1.5× bar with zero parity mismatches.

## 7. Closeout

| Action | Item |
|--------|------|
| Promote now | **Done** — promoted to `backend/simulation/sensor_kernel.py` |
| Keep as idea | — |
| Delete / archive | fork optional for regression |
| Test next | — |
| Stack with | tensor_clouds (also promoted) |

## 8. Path parity / caveats

Runner patches `SensorKernel.evaluate` directly; production promotion must wire fused path into `sensor_kernel.py`. Footprint and center-hit still use production `camera_2d` helpers (not fused).
