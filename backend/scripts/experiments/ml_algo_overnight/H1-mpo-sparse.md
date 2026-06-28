# H1 — MPO sparse reward (H1a + H1b)

**Hypothesis IDs:** `mpo_sparse` (H1a), `mpo_sparse_stable_eta` (H1b)  
**Script:** `_phases/h1_mpo_sparse.py`

## H1a — production MPO

Standard `MPOAgent` with production sparse reward (latent computed but not in `total`).

## H1b — fixed η

Same as H1a but `configure_stable_eta_mpo`: freeze `log_eta`, η optimizer LR = 0.

Tests whether dual temperature optimization caused KL/η blow-up in prior runs.

## Primary KPI

`learning_mode` — non-zero improving train returns + finite KL.

## Compare

If H1b passes and H1a fails → η dual was the blocker.
