# Report figures — TODO

All figures to be added to the LaTeX report.
Desktop machine has the videos and run artifacts. Add figures there, then include them in the relevant `.tex` section.

---

## How to include a figure in LaTeX

```latex
\begin{figure}[htbp]
  \centering
  \includegraphics[width=0.85\linewidth]{figures/<filename>.pdf}
  \caption{<caption text.>}
  \label{fig:<label>}
\end{figure}
```

Put all assets in `docs/report/semester-project/figures/` (create the folder).
Prefer PDF or high-res PNG for vector/raster respectively.

---

## Shortlist (priority order)

### [ ] Fig 0 — Baseline overflight: three phases ⬅ placeholder already in PDF

- **What:** Overhead 2D orbit-disk view of one deterministic baseline episode. Annotate three phases: (1) **Approach** — satellite enters the LOS corridor for the first target; (2) **Point** — attitude controller slews to target bearing, off-nadir angle grows; (3) **Capture** — boresight error below threshold, shutter fires. Mark shutter events on the arc. Repeat pattern visible across all targets. No cloud avoidance — all targets captured regardless of cloud cover.
- **Section:** Introduction → Objective (`sections/02_introduction.tex`, replace `\missingfigure` block)
- **Label:** `fig:baseline-overflight-phases`
- **Effort:** ~1 h — one baseline episode render export from the desktop machine
- **Data needed:** Run one baseline episode with the renderer in export mode (`backend/render/`); any saved baseline run or re-run `SequentialTargetBaselinePolicy` for one episode

---

### [ ] Fig 1 — Image quality curve (analytic, no simulation needed)

- **What:** Plot of the Lorentzian $q = r / (\delta + r)$ with $r = 0.30$ m as a function of ground blur $\delta$ [m]. Annotate three operating points: nadir-at-rest ($\delta \approx 0.76$ m, $q \approx 0.28$), half-tracking ($\delta \approx 0.38$ m, $q \approx 0.44$), full tracking ($\delta \approx 0$, $q \approx 1.0$).
- **Section:** Methods → Image quality (currently §3.3 subparagraph Step 3)
- **Label:** `fig:image-quality-curve`
- **Effort:** ~30 min — pure matplotlib, no simulation
- **Data needed:** none — formula only (`backend/simulation/image_quality.py`, `SATELLITE.py`)

---

### [ ] Fig 2 — dt sweep parity bar chart

- **What:** Four grouped bars, one per dt candidate {0.4, 0.8, 1.0, 1.5} s. Y = warmup episode return. Draw horizontal dashed line at 50% of the 0.4 s reference return (≈ 51.9). All four bars should clear the line (all passed). Optionally a second axis with wall-clock step rate.
- **Section:** Methods → Simulation timestep selection (H0 sweep)
- **Label:** `fig:dt-sweep`
- **Effort:** ~30 min
- **Data:** `backend/scripts/experiments/ml_algo_overnight/results/dt_profile.json` → `candidates[*].parity.episode_return`

---

### [ ] Fig 3 — Episode render / trajectory overview

- **What:** Overhead 2D orbit-disk render of one representative episode from the best run (Exp 9 or Exp 14). Shows: satellite arc, target corridor, cloud patches, shutter events (green = accepted, red = wasted/budget-exhausted). Use the existing renderer export.
- **Section:** Methods → Environment overview (or Results intro)
- **Label:** `fig:episode-render`
- **Effort:** ~1 h — need to run renderer on a saved `SimulationStateSeries` from the desktop machine
- **Data needed:** any saved run episode export from `backend/autonomous_control/runs/<run-id>/`; the renderer is `backend/render/`

---

### [ ] Fig 4 — Experiment return progression bar chart

- **What:** Horizontal bar chart (or lollipop). X = mean eval episode return. Y = experiment ID (Exp 0 baseline → Exp 14). Baseline nb07 at −38.6 drawn as vertical dashed reference line. Color: below baseline = red, above = green.
- **Section:** Results
- **Label:** `fig:return-progression`
- **Effort:** 1–2 h
- **Data:** KPI JSON files per experiment under `backend/scripts/experiments/*/results/*_kpi*.json` or `*_summary.json`; baseline anchor = −38.6 (Exp 13 Track A1)

---

### [ ] Fig 5 — Learning curve (best single run)

- **What:** Episode return vs. training episode number for the best experiment (Exp 9 SAC shutter-split or Exp 14 multienv). Mark warmup episodes in grey, training in blue, eval points as diamonds. Optionally overlay shutter cmds/ep on a twin axis.
- **Section:** Results
- **Label:** `fig:learning-curve`
- **Effort:** ~1 h
- **Data:** `episodes.csv` in the best run directory on desktop machine: `backend/autonomous_control/runs/<run-id>/episodes.csv`

---

### [ ] Fig 6 — KL / η explosion: pre- vs post-Exp 8 fix

- **What:** Two-panel plot. Left: MPO run before decoupled-KL fix — KL diverges ~10⁵, η → 10¹¹. Right: same setup after fix — KL bounded, learning proceeds. Motivates the algorithm fix section.
- **Section:** Methods → MPO decoupled-KL fix, or Results Exp 8
- **Label:** `fig:kl-explosion`
- **Effort:** ~1 h
- **Data:** `episodes.csv` from `ml_compare_compare_mpo_23-22-09` (pre-fix, Exp 3) and `ml_mpo_decoupled_dual_torque_sparse_*` (post-fix, Exp 8). Both on desktop machine.

---

### [ ] Fig 7 — Shutter-spam reduction across experiments

- **What:** Line or bar: shutter commands per episode (train mean or warmup) across the experiment arc. Shows the evolution from ~968 cmds/ep (legacy 0.4 s run) down to 8–10 cmds/ep in final experiments.
- **Section:** Results
- **Label:** `fig:shutter-reduction`
- **Effort:** ~1 h
- **Data:** `*_summary.json` fields `mean_shutter_cmds` or equivalent, one per experiment. On desktop machine.

---

### [ ] Fig 8 — Safe-mode activation rate per experiment

- **What:** Bar chart: safe-mode activations per episode (eval) per experiment. Shows how safe-mode shrinks as the agent learns to respect the off-nadir limit.
- **Section:** Results
- **Label:** `fig:safe-mode`
- **Effort:** ~1 h
- **Data:** eval episode metadata from run directories on desktop machine.

---

## Notes

- All figure source scripts should be saved under `docs/report/semester-project/figures/scripts/` so they can be reproduced.
- Use consistent color scheme: baseline = grey, SAC = blue, MPO = orange.
- Font size in plots: minimum 10 pt to match report body text.
- Export at ≥300 DPI (PNG) or as PDF (preferred for vector plots).
