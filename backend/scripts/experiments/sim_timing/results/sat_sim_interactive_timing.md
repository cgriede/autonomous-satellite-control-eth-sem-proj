# Sim timing profile — sat_sim_interactive

- **Run at:** 2026-06-02T18:38:57.129121+00:00
- **Clouds:** 2
- **Steps:** 976
- **Sim loop wall:** 1.792 s
- **Steps/s:** 544.76
- **Per-step wall:** 1.84 ms
- **Unaccounted in loop:** 0.006 s

## Top 7 time consumers

| Rank | Category | Total (s) | Per step (ms) | % of sim loop |
|------|----------|-----------|---------------|---------------|
| 1 | Visual: camera ray kernel | 0.622 | 0.637 | 34.7% |
| 2 | Reward / ML-side scoring | 0.456 | 0.467 | 25.5% |
| 3 | Reaction wheel & attitude dynamics | 0.314 | 0.321 | 17.5% |
| 4 | Geodesy transforms (disk to geodetic) | 0.258 | 0.264 | 14.4% |
| 5 | Stepper bookkeeping (residual per step) | 0.127 | 0.131 | 7.1% |
| 6 | Orbit position lookup (precomputed ephemeris) | 0.006 | 0.007 | 0.4% |
| 7 | Controller / policy (actuator command) | 0.003 | 0.003 | 0.2% |

## All categories

| Category | Total (s) | Per step (ms) | % of sim loop |
|----------|-----------|---------------|---------------|
| Visual: camera ray kernel | 0.622 | 0.637 | 34.7% |
| Reward / ML-side scoring | 0.456 | 0.467 | 25.5% |
| Reaction wheel & attitude dynamics | 0.314 | 0.321 | 17.5% |
| Geodesy transforms (disk to geodetic) | 0.258 | 0.264 | 14.4% |
| Stepper bookkeeping (residual per step) | 0.127 | 0.131 | 7.1% |
| Orbit position lookup (precomputed ephemeris) | 0.006 | 0.007 | 0.4% |
| Controller / policy (actuator command) | 0.003 | 0.003 | 0.2% |
| Environment: cloud arc / meteo encoding | 0.000 | 0.000 | 0.0% |
| Target footprint overlap & novelty | 0.000 | 0.000 | 0.0% |
| Render setup & frame draw | 0.000 | — | 0.0% |
| Video export / encode | 0.000 | — | 0.0% |
