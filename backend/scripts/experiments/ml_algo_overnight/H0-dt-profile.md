# H0 — dt / controller profile sweep

**Hypothesis ID:** `dt_profile`  
**Script:** `_phases/h0_dt.py` (via `run_overnight.py`)

## Goal

Pick the coarsest simulation timestep that preserves baseline-overflight capture parity, maximizing wall-clock throughput for the overnight budget.

## Candidates

| sim_dt (s) | controller_interval (s) | label |
|------------|-------------------------|-------|
| 0.4 | 1.0 | ref_0.4s (production reference) |
| 0.8 | 0.8 | dt_0.8s |
| 1.0 | 1.0 | dt_1.0s |
| 1.5 | 1.5 | dt_1.5s |

## Gates

1. **Parity:** 1 warmup episode — `n_shutter_cmds > 0`, return ≥ 50% of reference return
2. **Speed:** 1 MPO train episode — `wall_s`, `steps_per_s`

## Selection

- Largest `sim_dt_s` among parity-passing candidates (tie-break: lower `wall_s`)
- Speed ratio ≥ 2× reference → `train_episodes = 10`, else `7`
- No passing candidate → `aborted: true`, queue stops

## Output

`results/dt_profile.json` consumed by H1a, H1b, H6, H4.
