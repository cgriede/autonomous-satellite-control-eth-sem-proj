---
experiment_id: 15
slug: ml_mpo_episode_seed_diversity
title: "Exp 15 — Per-episode seed diversity + paired baseline"
current_phase: 3
overall_verdict: pending
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_episode_seed_diversity/
predecessor: ml_mpo_multienv_target_select
phases:
  "0": { status: done, documented_utc: "2026-07-10T12:40:00Z", completed_utc: "2026-07-10T12:53:29Z" }
  "1": { status: done, documented_utc: "2026-07-10T12:54:00Z", completed_utc: "2026-07-10T12:53:29Z" }
  "2": { status: done, documented_utc: "2026-07-10T13:30:00Z", completed_utc: "2026-07-10T13:29:29Z"
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-026]---
# Exp 15 — Per-episode seed diversity + paired baseline (`ml_mpo_episode_seed_diversity`)

**Agent:** MPO (Exp 14 factored target + move + shutter; PD OBC) · **dt:** 1.5 s / 1.5 s (frozen)  
**Predecessor:** [Exp 14](../2-run/14-mpo-multienv-target-select.md) (multi-env target select + mission score)  
**Follow-up (deferred):** cloud-condition diversity expansion (wider / richer cloud knobs) — **not** this slug

---
## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Does **re-seeding the environment every episode** (reproducible `derive_seed` per episode index) improve training diversity and generalization vs Exp 14’s **fixed seed per env block**, when we **always pair** the deterministic PD baseline and the learned agent on the **same** cloud/mission draw?

**Single atomic delta (this slug only):**

| Axis | Exp 14 default | Exp 15 |
|------|----------------|--------|
| Env draw cadence | 1 setup × **30** train eps (Stage B) | **1 new setup per episode** |
| Seed source | `derive_seed(base, "exp14_*", env_index)` | `derive_seed(base, "exp15_ep_*", episode_index)` |
| Baseline vs train | Baseline is a **separate** post-train eval step | **Paired every scenario:** baseline + agent on identical `mission_seed` / `cloud_seed` |
| Cloud knob bounds | Exp 14 `(20, 40)` count etc. | **Frozen** — same as Exp 14 (no cloud-diversity track here) |

**Hypothesis**

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H15a** | Per-episode reseeding improves held-out `score_mean` vs Exp 14 Stage B winner on the **same** 5-seed eval cohort | Treatment `score_mean` ≥ Exp 14 best `score_mean` **and** `Δscore_mean` vs paired baseline ≥ Exp 14’s `Δscore_mean` (or ≥ +10% absolute if Exp 14 comparator missing) | `score_mean` ≤ Exp 14 / no gain vs paired baseline |
| **H15b** | Pairing baseline per scenario removes “lucky cloud” misreads | Per-seed bar chart: treatment vs baseline on identical seeds; verdict uses `mean(Δscore_ep)` not best single seed | Verdict relies on unmatched seeds or single-env cherry-pick |
| **H15c** | Easy fork — no new action/reward architecture | Smoke passes with Exp 14 actor/reward/OBC unchanged; only env-loop + paired baseline wiring differs | Requires action-space or reward redesign to run |

**Arms (minimal):**

| Arm | Protocol |
|-----|----------|
| **ep_seed** (treatment) | Train with per-episode `build_*_setup(mission_seed, cloud_seed)`; each train/eval scenario also logs deterministic baseline score on that setup |
| **Comparator** | Exp 14 Stage B winner KPIs on matched 5-seed eval (if available); else paired baseline-only floor |

**Frozen knobs (inherit Exp 14 unless noted):**

| Knob | Value |
|------|-------|
| `sim_dt_s` / `controller_interval_s` | 1.5 s / 1.5 s |
| Action space | Categorical(50) + move + shutter |
| Low-level | PD OBC when `move=True`; coast otherwise |
| Reward / mission score | Exp 14 fork formulas |
| Cloud number / placement bounds | **Exp 14 values** (no expansion) |
| Warmup | Short fixed-seed warmup OK (5 ep) then per-episode train seeds — document exact counts in Phase 1 |
| Train budget | Match Exp 14 Stage B order of magnitude (~350 train ep) unless smoke shows rebuild cost forces trim |
| Eval | **5 held-out episode seeds**; always run baseline + treatment on each |

**Out of scope (explicit split — atomic gate):**

| Deferred track | Why not here |
|----------------|--------------|
| **Richer / wider cloud conditions** | Independent knob surface (`cloud_number_bounds`, thickness, corridor density, …). Charter as **Exp 16** after H15 verdict. |
| New reward terms / action dims | Exp 14 already owns those |
| Production promote during 0–3 | [D-003](../../../research/DECISIONS.md) |

**Gate:** `pipeline_run_guard` before Phase 2. Soft preference: after Exp 14 mutex / eval artifacts exist for H15a comparator ([D-012](../../../research/DECISIONS.md)).

### 0.2 Thought process (Why)

**Why now:** Exp 14 already samples **10 env blocks**, but within each block the agent sees the **same** orbit/cloud draw for 30 train episodes — low within-block diversity; easy to overfit one occlusion pattern. Operator ask: `for n in episodes: seed = random()` — the smallest diversity lever that does not touch cloud physics.

**Why pair baseline every scenario:** Mission score is cloud-luck sensitive. Comparing treatment on seed A to baseline on seed B confounds policy skill with weather. Running **both** on each draw makes `Δscore_ep` the fair unit; aggregate `mean(Δscore_ep)` is the verdict metric.

**Why not also expand cloud bounds in this slug:** Two independent tracks (episode reseeding vs cloud-parameter diversity). Per pipeline atomic rule → **split**. Cloud diversity is the **next logical** experiment after this one lands.

**What we reject / defer:**

| Item | Disposition |
|------|-------------|
| True non-reproducible `random()` without `derive_seed` | Rejected — keep reproducible episode seeds |
| Expanding `EXP14_CLOUD_NUMBER_BOUNDS` here | Deferred → Exp 16 |
| Replacing Exp 14 action/reward | Rejected — reuse |
| Parallel training with other pipeline slugs | Forbidden [D-012](../../../research/DECISIONS.md) |

#### 0.2.1 Shoulders of giants

| Source | Relevance |
|--------|-----------|
| [Exp 14 multi-env](../2-run/14-mpo-multienv-target-select.md) | Sibling scaffold: `build_exp14_env_setup`, mission score, factored MPO, paired 5-seed eval idea |
| `autonomous_control.config.randomness.derive_seed` | Reproducible sub-seeds (`base::namespace::index`) |
| `s01_utils.baseline_overflight` / `cloud_formation_generator` | Deterministic baseline + seeded clouds |
| Domain randomization literature (general) | Episode-level env randomization → better generalization than fixed-scene RL |

### 0.3 Preliminary implementation remarks (How)

**Feasibility:** **High / Nike-eligible after Phase 0 close.** Single logical delta on the env loop.

**Sibling to copy:** `backend/scripts/experiments/ml_mpo_multienv_target_select/` → new folder `ml_mpo_episode_seed_diversity/`.

**Hook points (Phase 1):**

1. Replace Stage B `for env_i … setup = build(env_i); for ep in 30` with `for ep_i … setup = build_from_episode_seed(ep_i)`.
2. Add `run_baseline_on_setup(setup)` beside each train/eval episode (or batch paired eval only — prefer **eval always paired**; train-time baseline optional for logging cost).
3. Keep Exp 14 cloud bounds / actor / reward / OBC untouched.
4. Smoke: 1 warmup + 2 train episodes with distinct seeds; assert `mission_seed`/`cloud_seed` differ across episodes; assert baseline + agent scores both logged for eval seeds.

**Recommended train-time baseline policy (cheap default):**

- **Eval / verdict:** always paired baseline + treatment (mandatory).
- **Train:** skip full baseline rollout every episode (cost ×2); log seeds only. Optional `--pair-baseline-train` flag if operator wants online Δscore curves.

**Risks:**

| Risk | Mitigation |
|------|------------|
| Setup rebuild cost per episode | Profile smoke wall time; if >2× Exp 14, trim train ep count in Phase 1.3 |
| Exp 14 comparator missing / incomplete | Fall back to H15b paired-Δ only; mark H15a inconclusive |
| Accidental cloud-bound edits | Code review gate: no changes to `EXP14_CLOUD_*` constants in this fork |

**Follow-up experiment (already identified):** **Exp 16 — cloud-condition diversity** (widen / enrich cloud sampling knobs; keep Exp 15 episode-seed protocol if H15 supported).

---

## Phase 1 — Built

### 1.1 Build plan (What)

- **Single delta:** per-episode `derive_seed` env redraw + paired PD baseline on every train/eval scenario.
- **Sibling copy:** Exp 14 factored MPO / reward / OBC / mission score unchanged.
- **Arm:** `hp_explore` (Exp 14 screen winner hparams); no new hparam screen.
- **JSON:** `results/smoke.json`, `results/full_summary.json` (`train_rows` with baseline/agent/delta per ep).

### 1.2 Build implementation (How we forked)

| Path | Role |
|------|------|
| `_env_setup_fork.py` | `episode_seeds` / `build_exp15_episode_setup` (`EXP15_BASE_SEED=15000`) |
| `_paired_baseline.py` | `run_baseline_score_on_setup` |
| `_episode_seed_runner.py` | Full loop: warmup fixed → train ep with new seed + baseline → paired eval |
| `_eval_harness.py` | Always paired baseline+treatment on identical eval seeds |
| `run.py` | `--verify` / `--smoke` / `--full` / `--eval-comparison` |

**Smoke** (`results/smoke.json`, 2026-07-10): `passed=true`; distinct seeds; paired baseline scores logged (agent score 0 on 2 train eps — expected pre-learning).

**Deviation from Phase 0.3 cheap default:** train-time baseline is **on by default** (operator request); `--no-pair-baseline-train` to disable. Default train budget **50** (not 350) because paired baseline ≈2× wall time.

### 1.3 Run instructions (How to execute)

| Step | Command | Stage | Output |
|------|---------|-------|--------|
| 0 | `python run.py --check-mutex` | mutex | fail if lock held |
| 1 | `python run.py --verify` | verify | `results/verify.json` |
| 2 | `python run.py --smoke --show-progress` | smoke | `results/smoke.json` |
| 3 | `python run.py --full --show-progress --train-episodes 50` | full | `results/full_summary.json` + checkpoint |
| 4 | `python run.py --eval-comparison --show-progress` | eval | `results/eval_comparison.json` |

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_episode_seed_diversity
python run.py --full --show-progress --train-episodes 50
```

Mutex auto-acquired on `--full`. Artifacts under `results/`.

---

## Phase 2 — Run

### 2.1 Run scope (What)

- Arm: `hp_explore` (Exp 14 screen winner hparams)
- Protocol: 5 fixed-seed warmup + **50** train episodes (new seed each) with **paired baseline every train ep** + 5 held-out paired eval
- dt 1.5/1.5; cloud bounds frozen Exp 14

### 2.2 Run monitoring (Why)

- Single mutex holder `ml_mpo_episode_seed_diversity` / `episode_seed_full`
- No parallel pipeline jobs

### 2.3 Run log & artifacts (How)

| Item | Value |
|------|-------|
| Wall | **2118 s** (~35 min) |
| Summary | `backend/scripts/experiments/ml_mpo_episode_seed_diversity/results/full_summary.json` |
| Checkpoint | `…/results/checkpoints/hp_explore/episode_seed_final.pt` |
| Train `delta_score_mean` | **−3.56** (agent score **0.0** all 50 train eps) |
| Eval baseline `score_mean` | **4.16** |
| Eval treatment `score_mean` | **0.36** |
| Eval `delta_score_mean` | **−3.81** |

Per-seed eval deltas: −3.46, −4.05, −2.45, −4.35, −4.72.

**Note:** Episode reseeding + pairing worked (distinct seeds, baseline scores vary ~1.5–5). Learning did **not** — train agent mission score stayed 0; treatment far below paired baseline. No MP4 export in this run (`--export-artifacts` not wired on Exp 15 full path).
