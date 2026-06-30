# ml_modular_encoder_r2 — Exp 6

**Pipeline:** [06-modular-encoder-r2.md](../../../../docs/experiments/pipeline/0-initialized/06-modular-encoder-r2.md)  
**Predecessor:** [ml_modular_encoder/](../ml_modular_encoder/) (Exp 2 v1)

## Hypothesis (H2r)

Re-test SAC **flat vs vector-compress encoder** (A0 vs A1) under a **learnable protocol** aligned with Exp 3 + Exp 5 closeout — not the v1 sparse 7-ep slice.

## Arms (unchanged from v1)

| Arm | Encoder | Agent |
|-----|---------|-------|
| `sac_a0` | Production `ControllerEncoder` (flat concat) | Overnight `SACAgent` fork |
| `sac_a1` | `CompressedControllerEncoder` — passthrough globals + `Linear(50→k)` on bearing/mask | `SACModularAgent` |

Default `k` (`--vector-embed-dim`): **8**.

## Entry point

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_modular_encoder_r2
python .\run_modular_encoder_r2.py --smoke --allow-cpu --arms sac_a1
python .\run_modular_encoder_r2.py --show-progress --arms sac_a0,sac_a1
```

## r2 profile (`profile.json`) — PLACEHOLDER

| Knob | Placeholder | Gate |
|------|-------------|------|
| `reward_mode` | `sparse` | **Exp 3** SAC path closeout — may switch to `dense` if Exp 5 M/L learns |
| `train_episodes` | 50 | Match learnable slice from Exp 3/5 if different |
| `learning_rate_pi` | 4.5e-4 | Raised LRs from hparam grid |
| `learning_rate_q` | 1e-3 | Raised LRs from hparam grid |
| `actor_dropout` | 0.0 | Raised LRs from hparam grid |

**Do not run Phase 2 until:**

1. Exp 3 closeout — SAC vs MPO verdict + reward mode for SAC path  
2. **Exp 5 closeout** (`ml_mpo_model_size`) — MPO width ablation; unblocks r2  
3. Update `profile.json` `reward_mode` / `ref_run_id` and document in DECISIONS  

## Blocked by

**Exp 5** (`ml_mpo_model_size`) per charter — Phase 1 build is OK; full runs wait for closeout.

## Results

- Summary: `results/modular_encoder_r2_summary.json`
- Analysis: `modular_encoder_r2_analysis.md`
- Per-arm log: `results/modular_encoder_r2.log`
- Smoke: `results/smoke.json`

## Not overengineered

- Fork of v1 with profile-driven workflow + raised LRs; encoder arms unchanged.
- A2 split heads **deferred** unless A1 hits `learning_mode`.
- Local `_reward_fork` for sparse/dense switch at Phase 2.
- Profile knobs in `profile.json` via `_profile_baseline.py` (avoid `_frozen_baseline` name clash with overnight).
