# Analysis — ml_mpo_decoupled_dual_torque (Exp 8)

**Pipeline closeout:** [08-mpo-decoupled-dual-fix.md](../../../../docs/experiments/pipeline/4-documentation/08-mpo-decoupled-dual-fix.md)  
**Source JSON:** `results/mpo_torque.json`  
**Pre-fix comparator:** `9998217218692971_ml_mpo_model_size_mpo_s_01-01-46` (−51.6 eval, KL→0)

## Hypothesis

Fixed decoupled-KL MPO achieves `learning_mode=true` on sparse torque + dt 1.5 s with bounded KL/η and escapes torque saturation.

## Verdict table

| Claim | Criterion | torque_sparse | Pre-fix | **Verdict** |
|-------|-----------|---------------|---------|-------------|
| **H8a** | Learning unblocked | `learning_mode=true` or eval ≥ −41 | **true**; train best **+8.7** | −51.6 floor | **Supported** |
| **H8b** | KL/η bounded | KL ~target; no η ramp | KL **0.021**; η **0.788** | KL→0 / →1e11 | **Supported** |
| **H8c** | Saturation < 0.9 | train sat fraction | **0.951** | ~0.998 | **Not supported** |
| **H8d** | α_μ/α_Σ active | finite duals | α_μ ~1e-5; α_σ ~0.28 | frozen | **Supported** |

**Overall: partial** — algorithm fix validated; mission / saturation not.

## Video / frame evidence

| Clip | Path |
|------|------|
| Eval ep 0 | `...\9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19\videos\eval_ep_0_rank1.mp4` |
| Train ep 28 (+8.7) | `...\videos\train_ep_28_rank1.mp4` |
| Frame manifest | `.cursor/video_frame_inspect/data/eval_best_20260630T150214Z/manifest.json` |

Eval: latent peaks, almost no applied capture dots. Train ep 28: rare good shutters.

## Follow-up

- [Exp 10](../../../../docs/experiments/pipeline/3-evaluation/10-mpo-safe-mode-penalty.md) — safe-mode reward penalty
- [Exp 11 MPO vector](../../../../docs/experiments/pipeline/3-evaluation/11-mpo-decoupled-dual-vector.md) — mode comparison
- MPO decoupled-KL regression test (deferred)
