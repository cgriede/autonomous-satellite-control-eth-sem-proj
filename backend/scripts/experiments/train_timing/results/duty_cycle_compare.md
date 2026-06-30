# Learn duty-cycle comparison

- **Run at:** 2026-06-30T11:04:50.559598+00:00

Knobs: `train_every_n_steps` = collect stores before learn gate; `updates_per_step` = train() calls per gate. Matched duty `N×N` keeps ~same total train updates as baseline.

| Variant | collect | burst | wall (s) | steps/s | train updates | train % | sim % | get_action % |
|---------|---------|-------|----------|---------|---------------|---------|-------|--------------|
| baseline_1x1 | 1 | 1 | 40.03 | 12.89 (1.00×) | 516 | 85.5% | 9.6% | 4.1% |

