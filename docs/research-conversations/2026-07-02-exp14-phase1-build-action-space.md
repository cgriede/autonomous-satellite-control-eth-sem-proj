# Exp 14 Phase 1 build — action space design Q&A

**Date:** 2026-07-02  
**Experiment:** `ml_mpo_multienv_target_select` (Exp 14)  
**Phase:** 1 Built  
**Related:** [Phase 0 discrete categorical action discussion](./2026-07-02-exp14-discrete-categorical-action-gpt55.md)

---

## Summary

Phase 1 scaffold implements a **factored 52-dim applied action** for off-policy MPO:

| Slice | Field | Type | Execute semantics |
|-------|-------|------|-------------------|
| 0–49 | target | one-hot | sampled / greedy target index |
| 50 | move_gym | (−1,+1) | > 0 → PD via `ObcPointingResolver`; ≤ 0 → zero RW torque |
| 51 | shutter_gym | (−1,+1) | > 0 → fire shutter |

Single source of truth: `backend/scripts/experiments/ml_mpo_multienv_target_select/_action_constants.py`.

---

## Decision: applied action vs predicted distribution

**Question:** Should replay store softmax probs or the executed action?

**Answer:** **Applied action (one-hot + gym bools).** Standard off-policy RL:

- **Q-step:** `Q(s, a)` must match the action that generated reward.
- **M-step:** `log π_target(t_idx)` with `t_idx = argmax(one_hot)` is exact.

Warmup baseline is the degenerate case (Dirac one-hot at `active_target_index`).

---

## Decision: factorized vs single Categorical(52)

**Answer:** **Factorized** — `Categorical(50)` + 2 Gaussian→tanh bool heads.

- Target latch maps to navball anchor → `theta_target_to_u` → OBC PD.
- Move/shutter keep Exp 8 decoupled KL on stacked 2-D Gaussian.
- Target head gets **entropy bonus only** (`entropy_coef * H[π_target]`).

Not a single `Categorical(52)`.

---

## Execution chain (softmax → sample → one-hot → actuator)

```
target_logits → softmax → sample/argmax → target_idx
    → one_hot(50) stored in buffer
    → anchor[target_idx] → target_boresight_angle_rad → theta_target_to_u → resolve_u_to_torque_nm
move_z, shutter_z → tanh → threshold at 0 for bool decode
```

Verification: `python run.py --verify` (checks A–G in plan).

---

## Index discipline

All modules import `TARGET_SLICE`, `MOVE_IDX=50`, `SHUTTER_IDX=51` from `_action_constants.py`.  
Check D in `--verify` catches MOVE/SHUTTER swap regressions.

---

## Score vs reward

| Metric | Definition | Use |
|--------|------------|-----|
| **score_ep** | Σ(quality × coverage) via `applied_capture_reward_series(k_capture=1.0)` | KPI / verdict |
| **episode_return** | Sparse capture credit + torque effort (fork reward) | Training signal |

Stage B checkpoint tracks best **eval score_mean**, not best return.

---

## MPO gradient notes (fork)

- E-step: sample `num_samples_pi` factored 52-dim actions; flatten for Q.
- M-step: `FactoredActor.log_prob()` sums target categorical + tanh-Jacobian on move/shutter only.
- KL: decoupled on stacked move+shutter Normal (unchanged from Exp 8).
- `entropy_coef` is fork-local per screen arm (not in production `MPOConfig`).

---

## Implementation artifacts (Phase 1)

| File | Role |
|------|------|
| `_action_constants.py` | 52-dim encode/decode |
| `_factorized_actor.py` | Categorical + 2 Normal heads |
| `_factorized_mpo_agent.py` | Factored MPO train loop |
| `_episode_loop_fork.py` | Custom warmup/train/eval (replaces `EpisodeRunner`) |
| `_mission_score.py` | score_ep KPI |
| `_env_setup_fork.py` | clouds 20–40, sat_z_offset, multi-env seeds |
| `run.py` | `--verify`, `--smoke`, `--screen`, `--full`, `--eval-baseline` |

**Smoke (2026-07-02):** `results/smoke.json` — verify A–G pass; 1 warmup + 2 train + eval; finite `score_ep`.

---

## Open items (unchanged from plan)

- `sat_z_offset` range ±5° — confirm for Stage B diversity.
- Full α/β/γ/δ/ε shaping deferred; fork uses sparse capture + small torque effort.
- Human code review gate before `--screen` / `--full`.
