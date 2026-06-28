# H6 — MPO dense latent + 10× shutter

**Hypothesis ID:** `mpo_dense_latent_10x_shutter`  
**Script:** `_phases/h6_mpo_dense_latent.py`  
**Fork:** `_reward_fork.py`

## Problem

Prior ml_learning_signal runs showed ~0.14% positive buffer transitions — credit assignment starved under sparse applied-only reward.

## Treatment

| Term | Production | H6 fork |
|------|------------|---------|
| Latent capture | computed, not in total | added to `total` every step |
| Applied shutter | k = 100 | 10× → effective k = 1000 |
| Latent scale | k = 100 | unchanged |

## Warmup cache

**Must rebuild** (`rebuild_warmup_bundle_cache=True`) — fingerprint includes `reward_mode: dense_latent_10x_applied`.

## Diagnostics

- `mean_positive_reward_steps`
- `train_return_integral`
- Compare vs H1a/H1b on same dt profile

## Verdict

`supported` if `learning_mode` even without beating baseline ~89.
