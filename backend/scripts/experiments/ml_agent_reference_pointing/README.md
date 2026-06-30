# ml_agent_reference_pointing — Exp 4 agent-reference pointing

**Pipeline:** [04-agent-reference-pointing.md](../../../../docs/experiments/pipeline/0-initialized/04-agent-reference-pointing.md)

## Hypothesis

SAC sparse with **`attitude_request_mode=vector`** (Ref1) learns better than direct torque control (Ref0) because the action space is smaller and safety is enforced on the orientation request, not via torque-path safe-mode arbitration. See [H1-agent-reference.md](H1-agent-reference.md).

## Status

**Phase 1 scaffold only.** Full training is **blocked until [Exp 3](../ml_sac_mpo_compare/README.md) closeout** — protocol defaults below are placeholders aligned with the SAC hparam grid, not yet frozen by compare verdict.

## Protocol defaults (placeholder)

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 |
| train | **50** |
| eval | 2 |
| SAC `learning_rate_pi` | 4.5e-4 |
| SAC `learning_rate_q` | 1e-3 |
| SAC `actor_dropout` | 0 |

## Arms

| Arm | `attitude_request_mode` | Agent | Reward |
|-----|-------------------------|-------|--------|
| **Ref0** | `torque` | SAC | sparse |
| **Ref1** | `vector` | SAC | sparse |
| **Ref2** (optional) | `vector` | MPO | dense |

## Run

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_agent_reference_pointing
python .\run_agent_reference.py --smoke --allow-cpu
python .\run_agent_reference.py --arms ref0,ref1 --show-progress
python .\run_agent_reference.py --arms ref0,ref1,ref2 --include-ref2 --show-progress
```

Smoke: Ref0 one warmup + one train step; `results/smoke.json` and run_dir `config.json` must list `experiment.attitude_request_mode`.

## Mutex

One pipeline training job per machine — global `pipeline_run_guard` ([D-012](../../../../docs/research/DECISIONS.md)).

## Artifacts

| Artifact | Path |
|----------|------|
| Smoke | `results/smoke.json` |
| Summary | `results/agent_reference.json` |
| Analysis | `agent_reference_analysis.md` |
