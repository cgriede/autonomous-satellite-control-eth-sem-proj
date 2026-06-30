# Train timing profile — one episode

- **Run at:** 2026-06-30T11:06:04.455800+00:00
- **DT profile:** dt_1.5s
- **Device:** NVIDIA GeForce RTX 5070
- **Sim steps:** 516
- **Controller stores:** 516
- **Train updates:** 5
- **Episode wall:** 7.213 s
- **Warmup wall (excluded):** 3.927 s
- **Steps/s:** 71.54
- **Per-step wall:** 13.98 ms
- **Unaccounted:** 0.118 s

## Knobs

- updates_per_step: 1
- train_every_n_steps: 100
- batch_size: 256
- num_samples_q / pi: 80 / 40

## Top consumers (% of episode wall)

| Rank | Category | Total (s) | Per step (ms) | % wall |
|------|----------|-----------|---------------|--------|
| 1 | Simulation step (integrate + shutter capture) | 3.641 | 7.055 | 50.5% |
| 2 | Policy inference (get_action) | 2.626 | 5.089 | 36.4% |
| 3 | Learner update (train) | 0.725 | 1.405 | 10.0% |
| 4 | Controller observation build | 0.096 | 0.187 | 1.3% |
| 5 | Replay buffer store | 0.007 | 0.014 | 0.1% |
| 6 | Per-step state copy (collect_states) | 0.000 | 0.000 | 0.0% |
| 7 | Warmup baseline controller tick | 0.000 | 0.000 | 0.0% |

## All categories

| Category | Total (s) | Per step (ms) | % wall |
|----------|-----------|---------------|--------|
| Simulation step (integrate + shutter capture) | 3.641 | 7.055 | 50.5% |
| Policy inference (get_action) | 2.626 | 5.089 | 36.4% |
| Learner update (train) | 0.725 | 1.405 | 10.0% |
| Controller observation build | 0.096 | 0.187 | 1.3% |
| Replay buffer store | 0.007 | 0.014 | 0.1% |
| Per-step state copy (collect_states) | 0.000 | 0.000 | 0.0% |
| Warmup baseline controller tick | 0.000 | 0.000 | 0.0% |
| Progress display / live feed | 0.000 | 0.000 | 0.0% |
