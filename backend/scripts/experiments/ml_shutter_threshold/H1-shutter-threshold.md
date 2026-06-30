# H1 — MPO shutter threshold 0.5 vs 0.9

## Hypothesis

Raising the shutter decision threshold from **0.5 → 0.9** reduces MPO shutter command spam (~968/ep overnight) and improves learning when combined with a **15 s** sparse capture-credit window.

## Arms

| Arm | Threshold | Agent | Reward |
|-----|-----------|-------|--------|
| `mpo_t05` | 0.5 | MPO | sparse + capture window |
| `mpo_t09` | 0.9 | MPO | sparse + capture window |

## KPIs

- `shutter_cmds_per_episode` (primary)
- `learning_mode`, train/eval returns
- `positive_reward_steps`

## Literature basis

See overnight findings: MPO shutter spam vs baseline 50; prior threshold probe at 0.35 in `ml_learning_signal/b_bug_hunt`.

**Closeout (2026-06-29):** [01-shutter-threshold.md](../../../../docs/experiments/pipeline/4-documentation/01-shutter-threshold.md) — H1 **not supported**; D-009, D-010, D-011. Reasoning: [shutter-threshold-investigation.md](../../../../docs/research/shutter-threshold-investigation.md).
