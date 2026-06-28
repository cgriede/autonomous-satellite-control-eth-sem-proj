# Deferred overnight phases

Trimmed from the initial hypothesis queue to fit GPU budget (~3–4.5 h). Revisit after morning readout of H0–H4.

## H2 — PPO on-policy

**Why deferred:** Overlap with deferred V-MPO; warmup/buffer edge cases; SAC tests “not MPO” more directly.

**Morning trigger:** Nothing hits `learning_mode` — run PPO as sanity check before hybrid methods.

**Sketch:** `agents/ppo_agent_fork.py` + `_phases/h2_ppo.py`; clear replay buffer after warmup; same Actor encoder.

## H3 — V-MPO

**Why deferred:** Largest build (3.5–5 h); on-policy trust region covered later if H4/H6 show learning.

**Morning trigger:** H4 `learning_mode` → deep V-MPO follow-up.

**Sketch:** Minimal on-policy V + KL trust region; reuse vision encoder.

## H5 — P-DQN (1810.06394)

**Why deferred:** Hybrid discrete shutter head (2.5–3.5 h); plan/control split is phase 2.

**Morning trigger:** Sparse reward confirmed as blocker but continuous shutter exploration inadequate.

**Sketch:** `agents/pdqn_agent_fork.py` — torque continuous + discrete shutter branch.

## Implementation note

When promoting a deferred phase, add a `_phases/hN_*.py` function and register it in `run_overnight.py` `PHASE_ORDER` — do not create top-level schedulable scripts.
