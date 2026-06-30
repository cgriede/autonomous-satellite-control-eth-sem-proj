# H3 — SAC sparse vs MPO dense (`ml_sac_mpo_compare`)

**Hypothesis ID:** `sac_mpo_compare`  
**Pipeline:** [03-sac-mpo-compare.md](../../../../docs/experiments/pipeline/1-built/03-sac-mpo-compare.md)  
**Plan:** [sac_vs_mpo_compare plan](../../../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md) § Track 3

## One-sentence hypothesis

At fixed **dt 1.5 s / 1.5 s**, **SAC + sparse** sustains learning while **MPO + dense** (H6 imaging credit) achieves `learning_mode=true` or beats the prior H6 −243 floor.

## Single logical delta

Algorithm × reward pairing on the **same** production encoder and dt profile — not encoder structure (Exp 2) or shutter knobs (Exp 1).

## Arms

| Arm | Agent | Reward | Baseline |
|-----|-------|--------|----------|
| `compare_sac` | SAC | sparse | overnight H4 |
| `compare_mpo` | MPO | dense | overnight H6 |

## Primary KPIs

- `learning_mode`
- Best train return vs ep 0; `early_aborted` / `train_episodes_completed`
- `positive_reward_steps` (debug episodes)
- MPO: `kl_mean_last`

## Frozen knobs

- dt 1.5/1.5, seed 7, 5 warmup, up to **20** train eps, **10**-ep patience
- `rebuild_warmup_bundle_cache=True` per arm

## Literature basis

See pipeline doc §0.2.1; [model-size-investigation.md](../../../../docs/research/model-size-investigation.md).
