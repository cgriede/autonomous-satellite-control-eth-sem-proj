# Sim timing profile — low_cloud

- **Run at:** 2026-06-02T18:25:42.017360+00:00
- **Clouds:** 5
- **Steps:** 976
- **Sim loop wall:** 2.467 s
- **Steps/s:** 395.58
- **Per-step wall:** 2.53 ms
- **Unaccounted in loop:** 0.006 s

## Top 7 time consumers

| Rank | Category | Total (s) | Per step (ms) | % of sim loop |
|------|----------|-----------|---------------|---------------|
| 1 | Visual: camera ray kernel | 1.104 | 1.132 | 44.8% |
| 2 | Reward / ML-side scoring | 0.531 | 0.544 | 21.5% |
| 3 | Reaction wheel & attitude dynamics | 0.326 | 0.334 | 13.2% |
| 4 | Geodesy transforms (disk to geodetic) | 0.321 | 0.328 | 13.0% |
| 5 | Stepper bookkeeping (residual per step) | 0.174 | 0.178 | 7.0% |
| 6 | Orbit position lookup (precomputed ephemeris) | 0.006 | 0.006 | 0.2% |
| 7 | Controller / policy (actuator command) | 0.001 | 0.001 | 0.0% |

## All categories

| Category | Total (s) | Per step (ms) | % of sim loop |
|----------|-----------|---------------|---------------|
| Visual: camera ray kernel | 1.104 | 1.132 | 44.8% |
| Reward / ML-side scoring | 0.531 | 0.544 | 21.5% |
| Reaction wheel & attitude dynamics | 0.326 | 0.334 | 13.2% |
| Geodesy transforms (disk to geodetic) | 0.321 | 0.328 | 13.0% |
| Stepper bookkeeping (residual per step) | 0.174 | 0.178 | 7.0% |
| Orbit position lookup (precomputed ephemeris) | 0.006 | 0.006 | 0.2% |
| Controller / policy (actuator command) | 0.001 | 0.001 | 0.0% |
| Environment: cloud arc / meteo encoding | 0.000 | 0.000 | 0.0% |
| Target footprint overlap & novelty | 0.000 | 0.000 | 0.0% |
| Render setup & frame draw | 0.000 | — | 0.0% |
| Video export / encode | 0.000 | — | 0.0% |
