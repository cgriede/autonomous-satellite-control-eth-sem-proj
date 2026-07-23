# Analysis card — Exp 6 modular encoder r2 (`ml_modular_encoder_r2`)

Source JSON: `results/modular_encoder_r2_summary.json`  
Pipeline: `docs/experiments/pipeline/4-documentation/06-modular-encoder-r2.md`  
Investigation: `docs/research/modular-encoder-r2-investigation.md`

## 1. Hypothesis

**H2r:** Structured encoding of the per-target **bearing** and **capture-mask** arrays (`Linear(50→8)` each) beats flat concat under a learnable SAC sparse protocol.  
**Not** image compression — camera lines unchanged.

## 2. Arms

| Arm | Encoder | Role |
|-----|---------|------|
| `sac_a0` | Flat `ControllerEncoder` | Control |
| `sac_a1` | `CompressedControllerEncoder` k=8 | Treatment |

## 3. Protocol

| Knob | Value |
|------|-------|
| Agent | SAC |
| Reward | sparse |
| Action | torque |
| dt | 1.5 / 1.5 |
| Warmup / train / eval | 5 / 50 / 2 |
| Seed | 7 |
| Completed | 2026-06-30T03:30:00Z (overnight exp6) |

## 4. Primary KPIs

| Arm | Warmup mean | Best train | Eval mean | learning_mode |
|-----|-------------|------------|-----------|---------------|
| sac_a0 | +393.2 | +11.2 | −3.9 | true |
| sac_a1 | +393.2 | +137.2 | +80.9 | true |

## 5. Secondary KPIs (eval)

| Arm | Shutter cmds | Meaningful frac |
|-----|--------------|-----------------|
| sac_a0 | 358 | 0.011 |
| sac_a1 | 298 | 0.034 |

## 6. Mechanism notes

- Exp 2 null was a short non-learnable slice; both r2 arms learn.
- A1 return gap is large; both arms still << baseline and still spam shutters.
- A1 last-ep `q_loss` ~852 — flag for stability; does not erase return gap.
- No MP4s in run dirs → no video claims.

## 7. Verdict

| Claim | Result |
|-------|--------|
| H2ra eval / learning | **Supported** |
| H2rb best train | **Supported** |
| H2rc secondary | **Supported** (weak) |
| **Overall** | **supported** (A1 vs A0; not baseline win) |

## 8. Follow-ups

- Optional: retest A0/A1 under Exp 9 reward + vector mode.
- No production promote ([D-027](../../../../docs/research/DECISIONS.md)).
- Semester report wiring is a separate step after pipeline closeout.
