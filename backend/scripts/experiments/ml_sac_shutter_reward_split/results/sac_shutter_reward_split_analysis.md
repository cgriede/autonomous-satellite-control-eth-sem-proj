# Analysis — ml_sac_shutter_reward_split (Exp 9 SAC)

**Pipeline closeout:** [09-sac-shutter-reward-split.md](../../../../docs/experiments/pipeline/4-documentation/09-sac-shutter-reward-split.md)  
**Source JSON:** `results/sac_shutter_reward_split.json`  
**Baseline (read-only):** Exp 7 `9998217172220712_ml_sac_vector_budget_13-56-17` (both penalties on)

## Hypothesis

SAC vector sparse with **waste penalty off** and **budget-exhausted penalty on** matches or beats Exp 7 KPIs.

## Verdict table

| Claim | Criterion | waste_off | Exp 7 | **Verdict** |
|-------|-----------|-----------|-------|-------------|
| **H9a** | Eval ≥ Exp 7 | eval mean | **+106.4** | +10.6 | **Supported** |
| **H9b** | Learning preserved | `learning_mode` | **true** | true | **Supported** |
| **H9c** | Budget spam controlled | post-budget cmds | **75** | — | **Supported** |
| **H9d** | Meaningful captures | train frac ≥ 0.22 | **0.286** | 0.220 | **Supported** |

**Overall: supported** (charter); operator behavioral bar partial (representation not richer on video).

## Arms (summary JSON)

```json
{
  "waste_off_budget_on": {
    "learning_mode": true,
    "eval_return_mean": 106.36,
    "post_budget_shutter_cmds_total": 75,
    "run_dir": "9998217165798903_ml_sac_shutter_split_15-43-20"
  },
  "baseline_exp7": {
    "eval_return_mean": 10.58,
    "train_meaningful_fraction": 0.220
  }
}
```

## Promotion

Align nb08 default `enable_shutter_waste_penalty=False` with production `RewardConfig` — Exp 9 evidence.
