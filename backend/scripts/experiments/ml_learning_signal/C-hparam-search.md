# Hypothesis C — hyperparameters

**Statement:** Default MPO hyperparameters (dropout 0.15, LR pi 1.5e-4, ELU init) prevent learning; tuned values unlock increasing train returns within 3 episodes.

**Runs (max 3):**

1. Lower dropout + higher pi LR: `actor_dropout=0.0`, `learning_rate_pi=4.5e-4`
2. Higher Q LR + lower KL targets: `learning_rate_q=1e-3`, `target_kl_mu=0.05`
3. Best combo from 1–2 or orthogonal: init via wider actor `num_units_actor=128`

**Frozen:** seed, features, warmup cache, 3 train episodes.

**Success bar:** `strong_lead=true` on any of the 3 runs.
