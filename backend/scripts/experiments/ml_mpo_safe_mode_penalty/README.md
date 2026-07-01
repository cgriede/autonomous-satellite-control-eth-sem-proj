# ml_mpo_safe_mode_penalty — Exp 10 MPO safe-mode reward penalty

**Pipeline:** [10-mpo-safe-mode-penalty.md](../../../../docs/experiments/pipeline/3-evaluation/10-mpo-safe-mode-penalty.md)

## Hypothesis

Exp 8 MPO learns with the dual fix but still hits safe-mode (~5–6 activations/ep) while saturating torque. Production reward has **no penalty** when `AGENT_CUT` or safe-mode torque overrides the agent. This experiment adds a per-step safe-mode penalty on the reward plane to align credit assignment with applied control.

## Arms

| Arm | `enable_safe_mode_penalty` | Run? |
|-----|---------------------------|------|
| **safe_mode_penalty_on** | **true** | **Yes** (treatment) |
| penalty_off (Exp 8) | false | **No** — `9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19` |

## Status

**Phase 2** — ready for overnight run (queue slot 1).

## Run

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_safe_mode_penalty
python run_mpo_safe_mode_penalty.py --smoke --allow-cpu
python run_mpo_safe_mode_penalty.py --show-progress
```

## Hook

- `_safe_mode_reward_fork.py` patches `SimulationStepper._populate_camera_and_reward` to subtract `k_safe_mode_penalty` when attitude-safety events include `AGENT_CUT`, `SAFE_MODE_TAKEOVER`, or `SAFE_MODE_INTERVAL_*` at the issue step.
- Warmup fingerprint extra keys: `enable_safe_mode_penalty`, `k_safe_mode_penalty`.
