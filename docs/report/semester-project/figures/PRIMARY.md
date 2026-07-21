# Report figures — primary set (wired into LaTeX)

Promoted from `docs/raw_image_selection/` into `figures/fig_*.png` and included in `sections/*.tex`.

| File | Label | Section | Provenance / pick notes |
|------|-------|---------|-------------------------|
| `fig_baseline_phase_approach.png` | `fig:baseline-overflight-phases` | Introduction | baseline MP4 f44 — nadir coast into corridor |
| `fig_baseline_phase_point.png` | (same) | Introduction | baseline MP4 f80 — ~31° off-nadir slew |
| `fig_baseline_phase_capture.png` | (same) | Introduction | baseline MP4 f110 — nadir lock (~0.7° off-nadir), quality ~0.93 after first shutter |
| `fig_env_overview.png` | `fig:env-overview` | Methods — environment | `targets-early` f66 — arc + corridor ahead (not a capture duplicate) |
| `fig_image_quality_curve.png` | `fig:image-quality-curve` | Methods — image quality | analytic script |
| `fig_safety_t{0,1,2}.png` | `fig:safety-maneuver` | Methods — safety | ref0 torque eval f125/130/155 — BRAKE / CRUISE / LOCKOUT |
| `fig_learning_curve_exp1.png` | `fig:learning-vs-not` | Results — learning | `returns_by_episode` shutter MPO t09 (`plot_083`) |
| `fig_learning_curve_exp9.png` | (same) | Results — learning | `returns_by_episode` SAC shutter-split (`plot_058`) |
| `fig_learning_curve_exp10.png` | `fig:learning-mpo-contrast` | Results — learning | `returns_by_episode` safe-mode penalty (`plot_056`) |
| `fig_learning_curve_exp11.png` | (same) | Results — learning | `returns_by_episode` MPO vector (`plot_055`) |
| `fig_selective_shutter.png` | `fig:selective-shutter` | Results — shutter | Exp9 eval_best f155 — sparse take-picture cluster |

Source pool + MP4s: `docs/raw_image_selection/`. Analytic curve script: `figures/scripts/make_image_quality_curve.py`.

**Integrity:** hash-check `fig_*.png` after promote — no byte-identical duplicates under different names.
