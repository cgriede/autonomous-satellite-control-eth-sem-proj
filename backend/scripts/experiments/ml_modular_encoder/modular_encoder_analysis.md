# Analysis — modular_encoder_sac

**Pipeline:** [02-modular-encoder.md](../../../docs/experiments/pipeline/4-documentation/02-modular-encoder.md)  
Source JSON: `modular_encoder_summary.json`

## Hypothesis

Vector compressors on bearing/mask (A1) beat flat concat (A0) for SAC sparse.

## Verdict table

| Claim | Criterion | sac_a0 | sac_a1 | Verdict |
|-------|-----------|--------|--------|---------|
| H1a | `learning_mode` or eval ↑ | false, −78.9 | false, −86.5 | **Rejected** |
| H1b | A1 best train > A0 | −72.4 | −75.1 | **Rejected** |
| H1c | Secondary KPIs | meaningful=0 | meaningful=0 | **Rejected** |

**Overall: `not_supported`** — no meaningful encoder impact in v1; A1 worse than A0.

## Arms (summary)

| Arm | `learning_mode` | eval mean | best train | q_loss (ep7) | shutter/ep train |
|-----|-----------------|-----------|------------|--------------|------------------|
| sac_a0 flat | false | −78.9 | −72.4 | 1420 | ~236 |
| sac_a1 compress | false | −86.5 | −75.1 | 3190 | ~210 |

## Deferred high interest ([D-015](../../../docs/research/DECISIONS.md))

**If we ever get a learning model** (`learning_mode=true`, stable critic, meaningful capture credit), **vector compressors on ordered target bearing/mask slots could be highly helpful** — the v1 slice could not test that fairly (sparse 7-ep, q_loss blow-up, zero `shutter_meaningful_fraction`).

Signals worth revisiting in a learnable regime (Exp 6):

- Structured **50+50** scalar fields vs flat 105-D concat.
- A1 **lower eval shutter rate** with different torque profile — may matter once actions carry credit.

**Not** the current bottleneck; **do** keep Exp 6 on the backlog after Exp 3/5.

## Follow-up

Exp 3 (SAC vs MPO); Exp 6 encoder r2 after Exp 5. No split-head encoder in v1.
