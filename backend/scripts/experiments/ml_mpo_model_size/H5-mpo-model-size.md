# H5 — MPO model size (width ablation)

**Experiment:** `ml_mpo_model_size`  
**Decision context:** [D-005](../../../../docs/research/DECISIONS.md) deferred width-first; [D-006](../../../../docs/research/DECISIONS.md) encoder before width — Exp 2 closeout unblocks this scaffold.

## Single logical delta

Replace production `MPOConfig` head widths only — **`num_units_actor` / `num_units_critic` / `num_layers_*`** at agent construction. Encoder (`ControllerEncoder`) and vision CNN path **unchanged**.

## Arms

| ID | Size | Actor / Critic | Layers (actor / critic) | Hypothesis ID |
|----|------|----------------|-------------------------|---------------|
| `mpo_s` | S | 90 / 140 | 1 / 2 | `mpo_width_s` |
| `mpo_m` | M | 140 / 256 | 2 / 2 | `mpo_width_m` |
| `mpo_l` | L | 256 / 512 | 2 / 3 | `mpo_width_l` |

## Frozen protocol (scaffold defaults)

| Knob | Charter (Phase 0) | Scaffold (`profile.json`) |
|------|-------------------|---------------------------|
| Agent | Production `MPOAgent` | same |
| dt | 1.5 s / 1.5 s | same |
| Train episodes | 7 | **50** (r2 placeholder — SAC hparam winner) |
| Warmup | 5 (rebuild per arm) | same |
| Eval | 2 | same |
| LRs | production | **π 4.5e-4, Q 1e-3, actor_dropout 0** |
| Reward | dense (H6) unless Exp 3 sparse learns | **sparse default** (`--reward-mode` configurable) |

## Numbered claims (from charter)

| ID | Claim | Success |
|----|-------|---------|
| **H5a** | S under-capacity | M or L beats S on `learning_mode` or eval ↑ ≥ 20% |
| **H5b** | Monotonic width | S ≤ M ≤ L eval return when learnable |
| **H5d** | Width not bottleneck | S and L collapse equally with high KL |

## Primary KPI

`learning_mode`; eval return mean vs S; KL/η last train ep; Q-loss trend; `action_diagnostics`.

## JSON contract

- `results/mpo_model_size_summary.json` — arms map, train_episodes, reward_mode, shared MPO knobs
- `results/arm_kpis/{arm}.json` — full KPI payload per arm

## Smoke

`--smoke --arms mpo_s` — warmup + one MPO train step; verify `config.json` `mpo.num_units_actor/critic` match S preset.

## Literature basis

[model-size-investigation.md](../../../../docs/research/model-size-investigation.md) §5 ablation matrix; MPO 2018 appendix; Co-Adaptation 2021 large-net sensitivity.
