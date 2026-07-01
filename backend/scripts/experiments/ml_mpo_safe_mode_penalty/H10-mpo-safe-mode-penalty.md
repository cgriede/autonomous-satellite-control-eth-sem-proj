# H10 — MPO safe-mode reward penalty

**Experiment:** Exp 10 · `ml_mpo_safe_mode_penalty`  
**Predecessor:** Exp 8 (`ml_mpo_decoupled_dual_torque`)

## Problem

Sparse MPO torque (Exp 8) shows:

- Stable KL / η (dual fix works).
- High torque saturation (~0.95).
- Repeated safe-mode activations per episode (telemetry `safe_mode_activations` 5–6).
- Almost no applied capture reward on eval (mistiming / bad shutters).

The attitude safety layer can zero or replace agent torque (`AGENT_CUT`, safe-mode takeover), but **`compute_reward` does not penalize those steps**. The agent optimizes torque-effort and shutter terms only.

## Hypothesis

> Adding a per-step penalty when safe-mode torque is applied or the agent command is cut will reduce safe-mode activations, lower saturation, and improve eval capture behavior without breaking MPO learning.

## Claims

| ID | Claim |
|----|-------|
| H10a | Lower `safe_mode_activations`/ep vs Exp 8 |
| H10b | `learning_mode=true`; train or eval return not worse than Exp 8 |
| H10c | Applied / meaningful shutters not worse (video + KPI) |
| H10d | Lower `torque_saturated_fraction` |

## Comparator

Read-only Exp 8 canonical run:

`backend/autonomous_control/runs/9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19`

## Implementation sketch (Phase 1)

1. `RewardConfig.enable_safe_mode_penalty` + `k_safe_mode_penalty`.
2. Per-step flag on simulation series (from `attitude_safety_events` / `in_safe_mode`).
3. `safe_mode_penalty(signals, cfg)` in `reward.py` (experiment fork path first).
4. Fork runner from `ml_mpo_decoupled_dual_torque/`.

## Out of scope

- Exp 8 Phase 3 closeout edits.
- SAC vector safe-mode arm (follow-on if H10 supported).
