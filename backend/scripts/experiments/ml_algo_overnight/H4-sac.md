# H4 — SAC fixed entropy

**Hypothesis ID:** `sac_entropy_fixed_alpha`  
**Script:** `_phases/h4_sac.py`  
**Agent:** `agents/sac_agent_fork.py`

## Treatment

Twin Q + Actor (reuses production `Actor`/`Critic`), fixed α = 0.2, sparse production reward.

## Rationale

Off-policy SAC tests whether MPO-specific issues (KL, dual η) block learning vs algorithm class.

## Primary KPI

`learning_mode` (KL check skipped for SAC).

## Compare

If H4 passes and H1 arms fail → consider deep SAC follow-up or deferred H3 V-MPO.
