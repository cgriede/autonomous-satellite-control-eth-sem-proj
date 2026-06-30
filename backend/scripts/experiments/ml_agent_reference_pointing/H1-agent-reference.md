# H1 — Agent-reference pointing (`ml_agent_reference_pointing`)

**Hypothesis ID:** `agent_reference_pointing`  
**Pipeline:** [04-agent-reference-pointing.md](../../../../docs/experiments/pipeline/1-built/04-agent-reference-pointing.md)  
**Plan:** [sac_vs_mpo_compare plan](../../../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md) § Track 4

## One-sentence hypothesis

SAC sparse commanding a **nadir-relative orientation reference** (`dim0 = u ∈ [-1,1]`) through OBC PD tracking improves mission learning vs direct reaction-wheel torque, with fewer safe-mode takeovers.

## Single logical delta

**Action interface** — `attitude_request_mode`: `torque` (Ref0 control) vs `vector` (Ref1 treatment). Shutter dim1 unchanged.

## Claims (H4)

| ID | Claim | Success | Falsified if |
|----|-------|---------|--------------|
| **H4a** | Ref1 `learning_mode` true while Ref0 false, or Ref1 eval return ↑ ≥ 10% vs Ref0 | Met | Both flat; Ref0 ≥ Ref1 |
| **H4b** | Ref1 `safe_mode_takeover_count` ≪ Ref0 on eval | Met | Vector arm still triggers torque-path safe mode |
| **H4c** | Ref1 improves shutter/capture KPIs at equal return | Met | No behavioral KPI gap |

## Arms

| Arm | Mode | Agent | Reward |
|-----|------|-------|--------|
| Ref0 | `torque` | SAC sparse | sparse |
| Ref1 | `vector` | SAC sparse | sparse |
| Ref2 | `vector` | MPO dense | dense (optional) |

## Vector semantics (v1 — frozen)

- `f_n = max_safe · u` where `max_safe = OFF_NADIR_HARD_LIMIT_DEG` (**45°**, shared with torque-path hard limit)
- `θ_req = wrap_pi(θ_nadir + f_n)`; `u = 0` → nadir
- Off-envelope (≥ 45° off-nadir at `θ_req`) → **hold-last** valid `θ_req`; log `hold_last_count`
- `τ = body_pointing_torque_nm(θ_used, …)`; PD clips `|τ| ≤ τ_max`
- Baseline warmup: `θ_target` → `u` → same resolver (no torque passthrough)
- No torque-path `AttitudeSafetyController` on vector steps (experiment fork)

## Invalid runs (do not use for verdict)

- Pipeline overnight exp4 ref1 after torque-passthrough crash fix
- `results/agent_reference.json` from pre-hold-last implementation
- Ref1 warmup bundle caches keyed before vector baseline `u` semantics

## Frozen knobs

- dt 1.5/1.5, seed 7, warmup 5, train **50**, eval 2
- SAC LRs: pi=4.5e-4, q=1e-3, actor_dropout=0
- `rebuild_warmup_bundle_cache=True` per arm; no checkpoint reuse across modes

## Primary KPIs

- `learning_mode`, eval return mean
- `hold_last_count` / `reference_clamp_count`, `safe_mode_takeover_count`
- Capture / shutter behavioral KPIs (Phase 2+ with video evidence)

## Open ambiguities (orchestrator)

1. **Vector reward:** torque-effort penalty disabled in vector mode only (`_reward_fork.py`).
2. **Ref2:** optional behind `--include-ref2`.
