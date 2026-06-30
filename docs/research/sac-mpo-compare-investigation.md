# SAC vs MPO compare (Exp 3) — investigation closeout

**Pipeline:** [Exp 3](../experiments/pipeline/4-documentation/03-sac-mpo-compare.md)

## Run summary (2026-06-29 23:06 UTC)

| Arm | learning_mode | Eval | vs H6 (−243) |
|-----|---------------|------|--------------|
| SAC sparse | true | −22.17 | — |
| MPO dense | false | −51.6 | +79% floor, no learning |

## Verdict

**supported** — SAC learns at dt 1.5 s; MPO dense does not sustain learning; algorithm × reward pairing matters ([D-017](DECISIONS.md)).

## Artifacts

- `backend/scripts/experiments/ml_sac_mpo_compare/results/compare_sac_mpo.json`
- SAC eval: `.../9998217225628033_ml_compare_compare_sac_23-06-11/videos/eval_ep_0_rank1.mp4`
- MPO eval: `.../9998217224670341_ml_compare_compare_mpo_23-22-09/videos/eval_ep_0_rank1.mp4`

## Follow-up

MPO debug: vector action space (Exp 4 Ref2), η/KL recipe, shutter shaping — not width (Exp 5).
