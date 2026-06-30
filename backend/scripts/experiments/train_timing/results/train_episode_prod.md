# Train timing profile — one episode

- **Run at:** 2026-06-30T10:46:11.844512+00:00
- **DT profile:** dt_1.5s
- **Device:** NVIDIA GeForce RTX 5070
- **Sim steps:** 516
- **Controller stores:** 516
- **Train updates:** 516
- **Episode wall:** 38.572 s
- **Warmup wall (excluded):** 3.465 s
- **Steps/s:** 13.38
- **Per-step wall:** 74.75 ms
- **Unaccounted:** 0.189 s

## Knobs

- updates_per_step: 1
- train_every_n_steps: 1
- batch_size: 256
- num_samples_q / pi: 80 / 40

## Top consumers (% of episode wall)

| Rank | Category | Total (s) | Per step (ms) | % wall |
|------|----------|-----------|---------------|--------|
| 1 | Learner update (train) | 33.767 | 65.439 | 87.5% |
| 2 | Simulation step (integrate + shutter capture) | 3.091 | 5.990 | 8.0% |
| 3 | Policy inference (get_action) | 1.437 | 2.785 | 3.7% |
| 4 | Controller observation build | 0.082 | 0.159 | 0.2% |
| 5 | Replay buffer store | 0.007 | 0.013 | 0.0% |
| 6 | Per-step state copy (collect_states) | 0.000 | 0.000 | 0.0% |
| 7 | Warmup baseline controller tick | 0.000 | 0.000 | 0.0% |

## All categories

| Category | Total (s) | Per step (ms) | % wall |
|----------|-----------|---------------|--------|
| Learner update (train) | 33.767 | 65.439 | 87.5% |
| Simulation step (integrate + shutter capture) | 3.091 | 5.990 | 8.0% |
| Policy inference (get_action) | 1.437 | 2.785 | 3.7% |
| Controller observation build | 0.082 | 0.159 | 0.2% |
| Replay buffer store | 0.007 | 0.013 | 0.0% |
| Per-step state copy (collect_states) | 0.000 | 0.000 | 0.0% |
| Warmup baseline controller tick | 0.000 | 0.000 | 0.0% |
| Progress display / live feed | 0.000 | 0.000 | 0.0% |
