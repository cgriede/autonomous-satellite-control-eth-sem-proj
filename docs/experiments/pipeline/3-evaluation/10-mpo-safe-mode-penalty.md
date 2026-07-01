---
experiment_id: 10
slug: ml_mpo_safe_mode_penalty
title: "Exp 10 — MPO safe-mode reward penalty (credit alignment)"
current_phase: 3
overall_verdict: pending
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_safe_mode_penalty/
predecessor: ml_mpo_decoupled_dual_torque
investigation: docs/research/mpo-learning-collapse-investigation.md
phases:
  "0": { status: done, documented_utc: "2026-06-30T20:00:00Z", completed_utc: "2026-06-30T21:00:36Z" }
  "1": { status: done, documented_utc: null, completed_utc: "2026-06-30T21:18:29Z"
  "2": { status: done, documented_utc: null, completed_utc: "2026-07-01T05:59:10Z"
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-022]---
# Exp 10 — MPO safe-mode reward penalty (`ml_mpo_safe_mode_penalty`)

**Agent:** MPO (fixed decoupled-KL dual) · **Action:** torque · **Reward:** sparse + **new** safe-mode penalty arm · **dt:** 1.5 s / 1.5 s  
**Predecessor:** [Exp 8](../4-documentation/08-mpo-decoupled-dual-fix.md) (dual fix works; safe-mode fires without reward signal)  
**Not in scope:** Exp 8 closeout, SAC vector (defer separate arm if MPO result is informative)
---
## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Does a per-step **safe-mode / AGENT_CUT penalty** on the reward plane reduce `safe_mode_activations`, improve agent-applied torque credit assignment, and improve mission KPIs vs Exp 8 (penalty **off**)?

**Motivation (operator, Exp 8 Phase 2):** Telemetry shows ~5–6 `safe_mode_activations` per episode while the agent still saturates torque; the safety layer replaces agent commands but **today’s `RewardConfig` has no term** for that — only torque-effort and shutter terms. The agent may not learn to stay inside safe envelope.

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H10a** | Safe-mode rate drops | Mean `safe_mode_activations`/ep **<** Exp 8 (~5–6) on train **and** eval | No decrease with penalty on |
| **H10b** | Learning preserved | `learning_mode=true`; train best return ≥ Exp 8 train best (+8.7) **or** eval improves vs Exp 8 (−81.1) | Collapse / frozen KL like pre-fix MPO |
| **H10c** | Applied capture not worse | Eval `shutter_meaningful_fraction` ≥ Exp 8 (≈0); latent→applied gap not wider on video | More torque saturation + fewer applied dots |
| **H10d** | Torque saturation eases | Train/eval `torque_saturated_fraction` < Exp 8 (~0.95) | Still ~1.0 with penalty on |

**Overall:** **supported** if H10b and (H10a or H10d) and H10c not regressed; **partial** if H10a/H10d improve but eval still poor; **not_supported** if penalty on is worse on all of H10a–H10d.

**Arms:**

| Arm | `enable_safe_mode_penalty` | Runs? |
|-----|---------------------------|-------|
| **safe_mode_penalty_on** | **true** | **Yes** (treatment) |
| penalty_off (Exp 8) | false | **No** — read-only `9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19` |

**Frozen protocol** (match Exp 8 except reward flag):

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 (rebuild) |
| train | 50 |
| eval | 2 |
| reward | sparse; shutter/budget flags = Exp 8 defaults |
| action mode | torque |
| MPO hparams | same as Exp 8 |
| videos | 3 train + 2 eval |

**Penalty design (Phase 1 — experiment fork first, D-003):**

| Field | Proposed default | Notes |
|-------|------------------|-------|
| `enable_safe_mode_penalty` | `false` (prod); `true` (treatment arm) | New `RewardConfig` flag |
| `k_safe_mode_penalty` | TBD (start ~1.0–5.0 per penalized step) | Pint-consistent scalar; tune in smoke if gradient too weak/strong |
| Penalized steps | Step has `AGENT_CUT` **or** attitude safety applied safe-mode torque (`IN_SAFE_MODE` / `SAFE_MODE_TAKEOVER` interval) | Requires per-step boolean on canonical series or reward recompute hook |

**Out of scope:** turning off attitude safety; dense reward; vector mode; hparam grid (separate screen); promoting flag to production until Phase 4.

**Gate:** `pipeline_run_guard.check_pipeline_run_clear(slug="ml_mpo_safe_mode_penalty")` before Phase 2. Soft preference: run after Exp 8 Phase 2 review recorded (comparator already exists).

### 0.2 Thought process (Why)

| Prior | Implication |
|-------|-------------|
| Exp 8: dual fix **supported** (KL/η stable); eval poor; safe-mode fires every ep | Algorithm learns; **reward plane** may be missing credit for safety overrides |
| No safe-mode term in `reward.py` today | Hypothesis is additive — not revisiting Exp 8 dual fix |
| Torque-effort penalty alone did not prevent saturation + safe-mode | Effort penalizes magnitude, not “command was cut” |
| Exp 9 SAC reward split | Parallel reward-plane thread on SAC; **this** exp is MPO torque only |

**Reject / defer:**

| Path | Why |
|------|-----|
| Bundle into Exp 8 closeout | Operator explicitly deferred to new experiment |
| SAC safe-mode arm in same slug | Different action semantics; add only if H10 supported on MPO |
| Penalize only episode-level safe-mode count | Step credit assignment needs per-step signal |

#### 0.2.1 Shoulders of giants

- [mpo-learning-collapse-investigation.md](../../research/mpo-learning-collapse-investigation.md) §8 — safe-mode reward gap listed as deferral after Exp 8.
- Exp 8 pipeline + operator notes — plateau ~ep 5, safe HUD vs telemetry, sparse applied shutters.

### 0.3 Preliminary implementation remarks (How)

**Scaffold:** copy `ml_mpo_decoupled_dual_torque/` → `ml_mpo_safe_mode_penalty/`; single reward delta.

| Component | Planned path |
|-----------|--------------|
| Entry | `run_mpo_safe_mode_penalty.py` |
| Runner | `_penalty_runner.py` — arm `safe_mode_penalty_on` |
| Reward delta | `_penalty_frozen.py` — `reward_safe_mode_penalty_on()` |
| Simulation hook | Per-step `safe_mode_active` (or `agent_cut`) in `SimulationStateSeries` + `compute_reward` term |
| Baseline embed | Exp 8 run in `config.json` → `experiment.baseline_comparison` |
| Results | `results/mpo_safe_mode_penalty.json`, `results/smoke.json` |
| Hypothesis card | `H10-mpo-safe-mode-penalty.md` |

**Engineering notes:**

1. `AttitudeSafetyController` emits `AGENT_CUT` and safe-mode takeover events (`stepper.attitude_safety_events`); episode telemetry already logs `safe_mode_activations` via `safe_mode_takeover_count()`.
2. Reward kernel needs **per-step** knowledge (not episode aggregate). Extend `finalize_series()` / `_recompute_reward_at` pattern used for shutter overrides.
3. Warmup fingerprint must include `enable_safe_mode_penalty` + `k_safe_mode_penalty`.
4. On **supported**, update `docs/presentation/machine-learning.md` reward slide before production promotion (Phase 4).

**Smoke:** one warmup + one train step; assert penalty flag in config; finite KL; log penalized step count > 0 on a forced-safe-mode probe episode if available.

---

## Phase 1 — Built

### 1.1 Build plan (What)

| Component | Path |
|-----------|------|
| Entry | `run_mpo_safe_mode_penalty.py` |
| Runner | `_penalty_runner.py` — arm `safe_mode_penalty_on` |
| Reward delta | `_safe_mode_reward_fork.py` — per-step penalty on `AGENT_CUT` / safe-mode events |
| Frozen knobs | `_penalty_frozen.py`, `profile.json` (`k_safe_mode_penalty=2.0`) |
| dt / mutex | `_sim_constants_fork.py`, `_run_guard.py` |
| Results | `results/mpo_safe_mode_penalty.json`, `results/smoke.json` |
| Hypothesis card | `H10-mpo-safe-mode-penalty.md` |

**Single delta:** enable safe-mode penalty on sparse MPO torque (Exp 8 protocol otherwise frozen).

### 1.2 Build implementation (How we forked)

Forked `ml_mpo_decoupled_dual_torque/`; patches `SimulationStepper._populate_camera_and_reward` for penalized steps. Warmup fingerprint includes `enable_safe_mode_penalty`, `k_safe_mode_penalty`.

**Smoke (2026-06-30):** passed — `results/smoke.json`; `kl=0`, finite dual vars; `enable_safe_mode_penalty=true`, `k=2.0`.

### 1.3 Run instructions (How to execute)

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_safe_mode_penalty
python run_mpo_safe_mode_penalty.py --smoke --allow-cpu
python run_mpo_safe_mode_penalty.py --show-progress
```

**Mutex:** global `pipeline_run_guard` — one pipeline training job at a time ([D-012](../../research/DECISIONS.md)).

**Comparator (read-only):** Exp 8 `9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19`.

---

## Phase 2 — Run

### 2.1 Run scope (What)

| Arm | Agent | Action | Reward | Train | Eval | Seed | dt |
|-----|-------|--------|--------|-------|------|------|-----|
| **safe_mode_penalty_on** | MPO (fixed dual) | torque | sparse + safe-mode penalty | 50 | 2 | 7 | 1.5 s / 1.5 s |

**Command:**

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_safe_mode_penalty
python run_mpo_safe_mode_penalty.py --show-progress
```

**Expected artifacts:** `results/mpo_safe_mode_penalty.json`, `run_dir/config.json`, `summary_metrics.json`, `videos/`, `plots/`, `artifacts_manifest.json`

### 2.2 Run monitoring (Why)

- **Queue position:** 1 of 4 in overnight batch (`run_pipeline_overnight_batch.py`).
- **Mutex:** no parallel pipeline slugs; offer `long-run-watch` if blocked.

### 2.3 Run log & artifacts (How)

*(Fill after run completes — run dirs, KPI JSON, video table.)*
