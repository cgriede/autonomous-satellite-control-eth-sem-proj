# Hypothesis A — fundamental limit

**Statement:** The current sparse capture-only reward + binary shutter threshold + Gaussian exploration cannot produce reliable non-zero train returns in 3 episodes even with a warm replay buffer of successful baseline captures.

**Falsification:** Any branch run with `strong_lead=true` on frozen fixture falsifies this.

**Evidence plan:**

- Shutter fire rate during train vs warmup
- Distribution of policy shutter dim vs threshold 0.5
- Reward sparsity (positive reward steps per episode)
- KL / eta blow-up during train (policy collapse)
- Whether Q targets ever see positive capture transitions from on-policy rollouts

**Allowed changes:** diagnostics in `a_fundamental_limit/` only; no production edits.

**Success bar for "supported":** concrete mechanism explaining ≥80% of zero-reward train episodes with numbers from baseline JSON.
