# Hypothesis: batched observation-line raytracing + FOV cloud cull

## Statement

Replacing per-bin Python loops in `simulate_camera_observation_line_1d` with batched NumPy
ray evaluation (Tier A), plus O(n_clouds) FOV culling (Tier D), will cut per-step sensor
cost enough for full coast episodes with 5–6+ clouds without changing observation semantics.

## Falsification

- Any observation-line code mismatch vs `kernel_backend=python`
- Line benchmark speedup < 5× at 6 clouds (A1)
- Full coast episode speedup < 2× vs baseline (A1)
- B1 cull changes parity vs A1 without cull

## Phases

| Phase | Change |
|-------|--------|
| baseline | Production kernels, timing JSON |
| A1 | `_angle_in_arc_batch`, `_batch_first_hit_earth_or_clouds`, accelerated observation line |
| B1 | Conservative FOV cull before cloud merge loop |

## Success bar

- A1: exact parity, ≥5× line benchmark at 6 clouds, ≥2× coast episode
- B1: exact parity vs A1, `clouds_culled > 0`, net time ≤ A1

## Evidence plan

JSON must include timing breakdown, parity mismatch count, 5–10 ASCII observation lines,
and sample `cloud_blocked_fraction` values.
