# Sim timing profile — high_cloud

- **Run at:** 2026-06-02T19:39:53.641364+00:00
- **Clouds:** 63
- **Steps:** 1937
- **Sim loop wall:** 10.259 s
- **Steps/s:** 188.80
- **Per-step wall:** 5.30 ms
- **Unaccounted in loop:** 0.011 s

## Top 7 time consumers

| Rank | Category | Total (s) | Per step (ms) | % of sim loop |
|------|----------|-----------|---------------|---------------|
| 1 | Video export / encode | 81.995 | — | 799.2% |
| 2 | Visual: camera ray kernel | 7.498 | 3.871 | 73.1% |
| 3 | Reward / ML-side scoring | 1.011 | 0.522 | 9.9% |
| 4 | Geodesy transforms (disk to geodetic) | 0.803 | 0.414 | 7.8% |
| 5 | Reaction wheel & attitude dynamics | 0.676 | 0.349 | 6.6% |
| 6 | Render setup & frame draw | 0.319 | — | 3.1% |
| 7 | Stepper bookkeeping (residual per step) | 0.244 | 0.126 | 2.4% |

## All categories

| Category | Total (s) | Per step (ms) | % of sim loop |
|----------|-----------|---------------|---------------|
| Video export / encode | 81.995 | — | 799.2% |
| Visual: camera ray kernel | 7.498 | 3.871 | 73.1% |
| Reward / ML-side scoring | 1.011 | 0.522 | 9.9% |
| Geodesy transforms (disk to geodetic) | 0.803 | 0.414 | 7.8% |
| Reaction wheel & attitude dynamics | 0.676 | 0.349 | 6.6% |
| Render setup & frame draw | 0.319 | — | 3.1% |
| Stepper bookkeeping (residual per step) | 0.244 | 0.126 | 2.4% |
| Orbit position lookup (precomputed ephemeris) | 0.013 | 0.007 | 0.1% |
| Controller / policy (actuator command) | 0.002 | 0.001 | 0.0% |
| Environment: cloud arc / meteo encoding | 0.000 | 0.000 | 0.0% |
| Target footprint overlap & novelty | 0.000 | 0.000 | 0.0% |
