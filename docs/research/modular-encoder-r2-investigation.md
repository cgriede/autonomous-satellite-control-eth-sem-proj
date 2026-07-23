# Modular encoder r2 (Exp 6) — investigation note

**Slug:** `ml_modular_encoder_r2` · **Closed:** 2026-07-23 · **Verdict:** **supported** (A1 vs A0 return gap)  
**Pipeline:** [06-modular-encoder-r2.md](../experiments/pipeline/4-documentation/06-modular-encoder-r2.md)  
**Predecessor:** Exp 2 [02-modular-encoder.md](../experiments/pipeline/4-documentation/02-modular-encoder.md) (`not_supported` in 7-ep slice)

## Research question

Does **structured encoding of the per-target bearing and capture-mask arrays** improve SAC learning versus flattening those arrays into one MLP — once a learnable training protocol exists?

This is **not** image compression. Camera observation lines / CNNs are unchanged. The only delta is how the two length-50 numeric target lists enter the policy network (`Linear(50 → 8)` each vs flat concat).

## Reasoning chain

1. **Exp 2 (v1)** tested the same encoder delta in a 7-ep SAC sparse slice. Both arms failed to learn (`learning_mode=false`, critic blow-up). Conclusion: encoder not helpful *in that slice* — but the slice may have been non-learnable.
2. **D-015** deferred high interest: retest when `learning_mode` exists elsewhere.
3. **Exp 3** showed SAC sparse can learn at dt 1.5 s. That unblocked a fair encoder retest.
4. **Overnight pipeline** (2026-06-30) ran Exp 6 after Exp 5; both A0/A1 finished with `learning_mode=true`.
5. **D-021** archived the charter the same day as low priority vs Exp 7 (budget penalty). Compute had already completed; science closeout was skipped until now.
6. **This closeout** restores the record: A1 eval +80.9 vs A0 −3.9; best train +137.2 vs +11.2. Hypothesis **supported** for A1 vs A0. Not a baseline win; shutter spam remains.

## Literature vs our runs

| Literature motivation | Our evidence |
|----------------------|--------------|
| Group / entity embeddings for structured tabular fields | A1 beats A0 on return under matched 50-ep SAC sparse |
| Structure before raw width (Exp 5 width ruled out) | Encoder structure helps when learning exists; width did not unblock MPO |
| Vision / image bottlenecks | **Out of scope** — not tested |

## Decisions taken

| ID | Decision |
|----|----------|
| [D-015](DECISIONS.md) | Deferred interest until learnable regime — **resolved by Exp 6 run** |
| [D-021](DECISIONS.md) | Interim archive vs Exp 7 priority — **superseded for closeout** |
| [D-027](DECISIONS.md) | Exp 6 **supported**; no production promote; report wiring separate |

## Rejected / deferred

| Path | Status | Why |
|------|--------|-----|
| Treat Exp 2 null as final | rejected | Protocol-limited |
| Promote compressor to production | deferred / no | Still spam; below baseline; torque-era stack |
| Video-based behavioral claims | not used | No MP4s in run dirs |
| Split-head / wider encoder | stop rule | Not needed given Supported A1 vs A0 |

## Experiments already conducted

| Slug | Arm | Eval | learning_mode | JSON |
|------|-----|------|---------------|------|
| `ml_modular_encoder` (Exp 2) | sac_a0 / sac_a1 | −78.9 / −86.5 | false / false | `ml_modular_encoder/results/modular_encoder_summary.json` |
| `ml_modular_encoder_r2` (Exp 6) | sac_a0 / sac_a1 | −3.9 / +80.9 | true / true | `ml_modular_encoder_r2/results/modular_encoder_r2_summary.json` |

## Open questions

- Does the A1 advantage survive **vector mode + budget penalty** (Exp 7/9 stack)?
- Is elevated A1 `q_loss` a stability risk at longer horizons?
- Should production ever default to target-array embeddings if selective shuttering is already solved by reward?

## Artifact note

Plots: `…/plots/returns_by_episode.png` on both Exp 6 run dirs.  
Videos: **missing** — do not cite MP4s for this experiment.
