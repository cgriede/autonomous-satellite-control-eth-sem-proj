# Report figures — TODO

**Authoritative wired set:** [`figures/PRIMARY.md`](figures/PRIMARY.md) (assets under `figures/fig_*.png` already included in LaTeX).

Alternates live in `figures/candidates/`. Do not dump the full experiment tree into the report.

---

## Wired (primary) — done

| Status | Figure | Label | Section |
|--------|--------|-------|---------|
| [x] | Baseline overflight phases | `fig:baseline-overflight-phases` | Introduction |
| [x] | Lookahead sensing geometry | `fig:concept-lookahead` | Introduction |
| [x] | Environment overview | `fig:env-overview` | Methods |
| [x] | Image quality curve | `fig:image-quality-curve` | Methods |
| [x] | Safety maneuver (BRAKE / CRUISE / LOCKOUT) | `fig:safety-maneuver` | Methods |
| [x] | Learning curves Exp 1 vs 9 | `fig:learning-vs-not` | Results |
| [x] | Learning curves Exp 10 vs 11 | `fig:learning-mpo-contrast` | Results |
| [x] | Selective shutter | `fig:selective-shutter` | Results |

---

## Optional backlog (not in PDF)

### [ ] Fig — dt sweep parity bar chart

- **Label:** `fig:dt-sweep`
- **Section:** Methods → Simulation timestep selection
- **Data:** timestep parity sweep KPI JSON under experiment results

### [ ] Fig — Experiment return progression

- **Label:** `fig:return-progression`
- **Section:** Results
- **Data:** frozen per-experiment KPI JSON

### [ ] Fig — KL / η pre- vs post-decoupled dual fix

- **Label:** `fig:kl-explosion`
- **Section:** Experiments / Results (Exp 8)

### [ ] Fig — Shutter-command count across the experiment arc

- **Label:** `fig:shutter-reduction`
- **Section:** Results

### [ ] Fig — Safe-mode activation rate

- **Label:** `fig:safe-mode`
- **Section:** Results

---

## Notes

- Prefer PDF or ≥300 DPI PNG; plot fonts ≥10 pt.
- Color convention: baseline grey, SAC blue, MPO orange.
- Scripts for analytic figures: `figures/scripts/`.
