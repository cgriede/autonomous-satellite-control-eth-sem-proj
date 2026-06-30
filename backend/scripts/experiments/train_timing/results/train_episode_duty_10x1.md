# Train timing profile — one episode

- **Run at:** 2026-06-30T11:06:05.999136+00:00
- **DT profile:** dt_1.5s
- **Device:** NVIDIA GeForce RTX 5070
- **Sim steps:** 516
- **Controller stores:** 516
- **Train updates:** 51
- **Episode wall:** 8.856 s
- **Warmup wall (excluded):** 3.874 s
- **Steps/s:** 58.26
- **Per-step wall:** 17.16 ms
- **Unaccounted:** 0.108 s

## Knobs

- updates_per_step: 1
- train_every_n_steps: 10
- batch_size: 256
- num_samples_q / pi: 80 / 40

## Top consumers (% of episode wall)

| Rank | Category | Total (s) | Per step (ms) | % wall |
|------|----------|-----------|---------------|--------|
| 1 | Learner update (train) | 3.677 | 7.126 | 41.5% |
| 2 | Simulation step (integrate + shutter capture) | 3.275 | 6.347 | 37.0% |
| 3 | Policy inference (get_action) | 1.697 | 3.289 | 19.2% |
| 4 | Controller observation build | 0.092 | 0.179 | 1.0% |
| 5 | Replay buffer store | 0.007 | 0.013 | 0.1% |
| 6 | Per-step state copy (collect_states) | 0.000 | 0.000 | 0.0% |
| 7 | Warmup baseline controller tick | 0.000 | 0.000 | 0.0% |

## All categories

| Category | Total (s) | Per step (ms) | % wall |
|----------|-----------|---------------|--------|
| Learner update (train) | 3.677 | 7.126 | 41.5% |
| Simulation step (integrate + shutter capture) | 3.275 | 6.347 | 37.0% |
| Policy inference (get_action) | 1.697 | 3.289 | 19.2% |
| Controller observation build | 0.092 | 0.179 | 1.0% |
| Replay buffer store | 0.007 | 0.013 | 0.1% |
| Per-step state copy (collect_states) | 0.000 | 0.000 | 0.0% |
| Warmup baseline controller tick | 0.000 | 0.000 | 0.0% |
| Progress display / live feed | 0.000 | 0.000 | 0.0% |
