# Sim timing profile — high_cloud

- **Run at:** 2026-06-27T17:19:36.292551+00:00
- **Clouds:** 63
- **Steps:** 1292
- **Sim loop wall:** 3.587 s
- **Steps/s:** 360.18
- **Per-step wall:** 2.78 ms
- **Unaccounted in loop:** 0.008 s

## Top 7 time consumers

| Rank | Category | Total (s) | Per step (ms) | % of sim loop |
|------|----------|-----------|---------------|---------------|
| 1 | Visual: camera ray kernel | 1.766 | 1.367 | 49.2% |
| 2 | Reward / ML-side scoring | 0.618 | 0.478 | 17.2% |
| 3 | Stepper bookkeeping (residual per step) | 0.501 | 0.388 | 14.0% |
| 4 | Reaction wheel & attitude dynamics | 0.415 | 0.321 | 11.6% |
| 5 | Geodesy transforms (disk to geodetic) | 0.267 | 0.207 | 7.5% |
| 6 | Controller / policy (actuator command) | 0.007 | 0.005 | 0.2% |
| 7 | Orbit position lookup (precomputed ephemeris) | 0.006 | 0.005 | 0.2% |

## All categories

| Category | Total (s) | Per step (ms) | % of sim loop |
|----------|-----------|---------------|---------------|
| Visual: camera ray kernel | 1.766 | 1.367 | 49.2% |
| Reward / ML-side scoring | 0.618 | 0.478 | 17.2% |
| Stepper bookkeeping (residual per step) | 0.501 | 0.388 | 14.0% |
| Reaction wheel & attitude dynamics | 0.415 | 0.321 | 11.6% |
| Geodesy transforms (disk to geodetic) | 0.267 | 0.207 | 7.5% |
| Controller / policy (actuator command) | 0.007 | 0.005 | 0.2% |
| Orbit position lookup (precomputed ephemeris) | 0.006 | 0.005 | 0.2% |
| Environment: cloud arc / meteo encoding | 0.000 | 0.000 | 0.0% |
| Target footprint overlap & novelty | 0.000 | 0.000 | 0.0% |
| Render setup & frame draw | 0.000 | — | 0.0% |
| Video export / encode | 0.000 | — | 0.0% |
