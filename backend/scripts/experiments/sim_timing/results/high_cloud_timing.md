# Sim timing profile — high_cloud

- **Run at:** 2026-06-27T13:47:37.472983+00:00
- **Clouds:** 63
- **Steps:** 1292
- **Sim loop wall:** 3.436 s
- **Steps/s:** 376.04
- **Per-step wall:** 2.66 ms
- **Unaccounted in loop:** 0.005 s

## Top 7 time consumers

| Rank | Category | Total (s) | Per step (ms) | % of sim loop |
|------|----------|-----------|---------------|---------------|
| 1 | Visual: camera ray kernel | 1.736 | 1.344 | 50.5% |
| 2 | Reward / ML-side scoring | 0.608 | 0.470 | 17.7% |
| 3 | Stepper bookkeeping (residual per step) | 0.413 | 0.320 | 12.0% |
| 4 | Reaction wheel & attitude dynamics | 0.410 | 0.318 | 11.9% |
| 5 | Geodesy transforms (disk to geodetic) | 0.252 | 0.195 | 7.3% |
| 6 | Orbit position lookup (precomputed ephemeris) | 0.006 | 0.005 | 0.2% |
| 7 | Controller / policy (actuator command) | 0.005 | 0.004 | 0.1% |

## All categories

| Category | Total (s) | Per step (ms) | % of sim loop |
|----------|-----------|---------------|---------------|
| Visual: camera ray kernel | 1.736 | 1.344 | 50.5% |
| Reward / ML-side scoring | 0.608 | 0.470 | 17.7% |
| Stepper bookkeeping (residual per step) | 0.413 | 0.320 | 12.0% |
| Reaction wheel & attitude dynamics | 0.410 | 0.318 | 11.9% |
| Geodesy transforms (disk to geodetic) | 0.252 | 0.195 | 7.3% |
| Orbit position lookup (precomputed ephemeris) | 0.006 | 0.005 | 0.2% |
| Controller / policy (actuator command) | 0.005 | 0.004 | 0.1% |
| Environment: cloud arc / meteo encoding | 0.000 | 0.000 | 0.0% |
| Target footprint overlap & novelty | 0.000 | 0.000 | 0.0% |
| Render setup & frame draw | 0.000 | — | 0.0% |
| Video export / encode | 0.000 | — | 0.0% |
