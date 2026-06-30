# Shutter threshold investigation — MPO sparse credit assignment

**Canonical experiment record:** [01-shutter-threshold.md](../experiments/pipeline/4-documentation/01-shutter-threshold.md) (hypothesis verdict table + artifacts)

Research note closing **Exp 1** (`ml_shutter_threshold`): whether raising the shutter decision threshold **0.5 → 0.9** reduces MPO shutter spam and whether a **15 s capture-credit window** adds enough train signal for sparse MPO on the s01 overflight mission.

**Knowledge index:** [PROJECT_KNOWLEDGE.md](PROJECT_KNOWLEDGE.md) · **Decision IDs:** [D-009](DECISIONS.md), [D-010](DECISIONS.md), [D-011](DECISIONS.md)

**Related code:** `backend/scripts/experiments/ml_shutter_threshold/` · `backend/autonomous_control/action_adapter.py` · `backend/notebooks/s01/s01_utils/training_workflow.py`  
**Hypothesis doc:** [`H1-shutter-threshold.md`](../../backend/scripts/experiments/ml_shutter_threshold/H1-shutter-threshold.md)  
**Pipeline:** [STATUS_2026-06.md](../ml/experiments/STATUS_2026-06.md) · [01-shutter-threshold.md](../experiments/pipeline/4-documentation/01-shutter-threshold.md) · master plan [sac_vs_mpo_compare plan](../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md)

---

## Reasoning chain

1. **Question** — Overnight H1a MPO sparse showed ~**968 shutter cmds/ep** vs baseline ~**50** (`ml_algo_overnight`). Is spam a **threshold** artifact (policy outputs high `shutter_gym` but we fire too easily at 0.5), and can a **short dense credit window** after shutter make sparse learning tractable?

2. **Literature / prior art** — MPO is sensitive to reward sparsity and implementation recipe ([model-size-investigation.md](model-size-investigation.md)). No paper in our library prescribes shutter gating; this is **domain mechanics** (bool cmd from continuous dim). Prior internal probe: threshold **0.35** in `ml_learning_signal/b_bug_hunt` (not a full train compare).

3. **Hypothesis (H1)** — At fixed **dt 1.5 s / 1.5 s** (D-002), MPO sparse + 15 s window: **`mpo_t09` (0.9)** cuts cmds/ep vs **`mpo_t05` (0.5)** and improves `learning_mode` / returns.

4. **Evidence (our runs)** — Both arms trained 7 eps + 2 eval; warmup baseline healthy (+250–470). Policy saturates **`shutter_gym ≈ +1`** (`shutter_unit ≈ 1.0`), so 0.9 still fires ~**99.8%** of controller steps. Mean cmds/ep **516.0** vs **514.9** (−0.2%). No `learning_mode`; eval return **−101.6** both arms. Video inspection: shutter comb on reward plot early; torque penalty yields **non-constant** late-episode torque (learned structure, not mission success). KL/η blow up (η → 1800–3100).

5. **Conclusion** — **H1 not supported.** Threshold is not an effective lever while the policy saturates the shutter dimension. Capture window works **mechanically** (latent bursts mid-episode) but does not fix credit assignment. **Exp 1 closed**; pipeline unblocks **Exp 2** (encoder) and **Exp 3** (SAC vs MPO).

---

## 1. Mechanism (how threshold works)

Production path ([`action_adapter.py`](../../backend/autonomous_control/action_adapter.py)):

| Step | Rule |
|------|------|
| Policy dim 1 | `shutter_gym ∈ [-1, 1]` |
| Unit map | `shutter_unit = 0.5 × (clip(gym, −1, 1) + 1)` → **[0, 1]** |
| Fire | `shutter_unit > threshold` (default **0.5**; at **0.9** need **gym > 0.8**) |

Experiment forks (read-only prod):

- `_shutter_threshold_fork.py` — patches threshold for one arm
- `_capture_window_fork.py` — after accepted shutter, add **latent imaging credit** for **15 s** (~10 steps at dt 1.5 s)

### Reward contract (eval panel, dt 1.5 s run)

| Term | Setting |
|------|---------|
| Mode | **sparse** — applied capture at shutter only |
| Shutter waste | **−5** when shutter accepted but applied credit ≈ 0 |
| Torque effort | **−0.1 × (τ/τ_max)²** per step |
| Safe mode | off-nadir **> 45°** → brake, nadir recovery, **60 s** agent torque lockout |
| RW rate limit | \|ω_sat\| **> 3°/s** → block opposing torque |

Episode: **516** integration steps, **773.95 s**, altitude **~528.8 km**, **50** targets.

---

## 2. Diagnostics

| KPI | Interpretation |
|-----|----------------|
| `shutter_cmds_per_episode` | Count of `take_picture_cmd_steps` in `SimulationStateSeries` metadata |
| `shutter_meaningful_fraction` | Fraction of shutter steps with reward > ε (1.0) — **0.0** both arms |
| `learning_mode` | Overnight gate: improving train/eval signal — **false** both arms |
| `shutter_unit` samples | Collector at controller steps — t09: mean **0.999**, fire@0.9 **99.8%** |
| Video / plots | Pink vlines = shutter cmds; purple solid = applied RW torque; orange dashed = agent request |

**Invalid run (do not cite):** `ml_shutter_mpo_t05_11-12-19` — pre–dt-fix (**1936** steps/ep, prod 0.4 s effective). Valid t05: `ml_shutter_mpo_t05_14-04-49` (**517** max steps).

---

## Decisions taken

| ID | Status | Decision | Link |
|----|--------|----------|------|
| D-009 | rejected | Shutter threshold **0.5 → 0.9** as primary fix for MPO shutter spam | [DECISIONS.md](DECISIONS.md) |
| D-010 | rejected | **15 s capture-credit window** alone sufficient to unblock sparse MPO learning | [DECISIONS.md](DECISIONS.md) |
| D-011 | accepted | **Close Exp 1**; proceed pipeline to **Exp 2** (encoder) / **Exp 3** (SAC vs MPO) | [DECISIONS.md](DECISIONS.md) |

---

## Rejected or deferred (do not re-run without user reversal)

| Path | Status | Why | Revisit when |
|------|--------|-----|--------------|
| Intermediate thresholds (0.35, 0.7, …) on MPO | deferred | t09 already at extreme; policy saturates gym dim — sweep unlikely to help without action shaping | User requests action-space / penalty redesign |
| Re-run H1 at prod dt 0.4 s | rejected | Superseded by D-002 fixed 1.5 s profile | — |
| Threshold + **dense** reward (H6) in same experiment | deferred | Belongs to **Exp 3** SAC vs MPO compare, not Exp 1 | Exp 3 arms |
| Hard shutter cap / discrete action | deferred | Architectural change; not tested | If continuous shutter remains saturated after Exp 3 |

---

## Experiments already conducted

| Slug | Arm | Verdict | JSON / analysis | Run dir (valid) | Notes |
|------|-----|---------|-----------------|-----------------|-------|
| `ml_shutter_threshold` | `mpo_t05` | inconclusive | [`shutter_threshold_summary.json`](../../backend/scripts/experiments/ml_shutter_threshold/results/shutter_threshold_summary.json) · [`shutter_threshold_analysis.md`](../../backend/scripts/experiments/ml_shutter_threshold/shutter_threshold_analysis.md) | `backend/autonomous_control/runs/ml_shutter_mpo_t05_14-04-49` | threshold **0.5**; 516 cmds/ep; learning_mode **false** |
| `ml_shutter_threshold` | `mpo_t09` | inconclusive | same summary | `backend/autonomous_control/runs/9998217254656575_ml_shutter_mpo_t09_15-02-22` | threshold **0.9**; mean **514.9** cmds/ep; fire@0.9 **99.8%** |
| `ml_shutter_threshold` | smoke | passed | [`smoke.json`](../../backend/scripts/experiments/ml_shutter_threshold/results/smoke.json) | `ml_shutter_smoke` | CUDA + warmup + one `train()` |
| `ml_algo_overnight` | H1a mpo_sparse | inconclusive | `results/h1a_mpo_sparse.json` | — | Motivation: ~968 cmds/ep spam |

**H1 aggregate verdict:** **not supported** — see [01-shutter-threshold.md](../experiments/pipeline/4-documentation/01-shutter-threshold.md) for the hypothesis verdict table.

**Plots:** `backend/scripts/experiments/ml_shutter_threshold/results/plots/` (`shutter_unit_hist.png`, `shutter_cmds_per_episode.png`, `train_returns.png`, `fire_rate_vs_threshold.png`).

**Per-arm KPI cache:** `results/arm_kpis/mpo_t05.json`, `mpo_t09.json` · re-finalize: `python _finalize_summary.py`.

---

## Open questions

- Does **SAC** exhibit the same shutter saturation at sparse reward (Exp 3)?
- Does **dense** reward (H6 formula) change shutter statistics without saturating gym dim?
- Is **encoder structure** (Exp 2) required before any MPO sparse signal is learnable?
- Should shutter waste penalty (−5) or torque penalty weights be tuned — or is KL collapse the dominant failure mode?

---

## Gaps in local library

| Topic | Status | Action |
|-------|--------|--------|
| MPO + sparse event-driven rewards in continuous control | No direct paper | Cite Abdolmaleki 2018 + project runs |
| Shutter gating as RL action semantics | Internal only | Documented here |

---

## References

### Local

- [model-size-investigation.md](model-size-investigation.md) — MPO instability, defer width ablation (D-005)
- [LITERATURE_HIGHLIGHTS.md](LITERATURE_HIGHLIGHTS.md) — SRL / encoder motivation for next exps

### Project code & runs

- Charter: `backend/scripts/experiments/ml_shutter_threshold/SUBAGENT_CHARTER.md`
- Summary: `backend/scripts/experiments/ml_shutter_threshold/results/shutter_threshold_summary.json`
- dt profile: `backend/scripts/experiments/ml_shutter_threshold/results/dt_profile.json`
