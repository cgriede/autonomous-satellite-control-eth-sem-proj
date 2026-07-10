# Figure candidate manifest

Generated: `2026-07-10T12:33:09Z`
Total candidates: **186**

Status legend: `theme` = requested highlight series; `backup` = bulk pool from run plots;
`primary` = promote after human pick (none yet).

## Counts by theme

| Theme | Count |
|-------|------:|
| `trend-learning-curve` | 51 |
| `trend-returns` | 51 |
| `dynamic-safety-maneuver` | 25 |
| `episode-diagnostics-eval` | 18 |
| `dynamic-cloud-generation` | 17 |
| `behaviour-selective-shutter` | 12 |
| `static-target-placement` | 12 |

## Requested highlight series

| Theme | Folder | Notes |
|-------|--------|-------|
| static target placement | `candidates/themes/01_target_placement/` | baseline corridor stills |
| dynamic clouds | `candidates/themes/02_cloud_motion/` | 5- and 7-neighbor series |
| dynamic safety | `candidates/themes/03_safety_maneuver/` | torque eval neighbor cycles |

## Next (≤1.5 h)

1. Open theme folders; mark 1–2 series as `primary` in this file.
2. Promote winners into `figures/` (not `candidates/`) for LaTeX.
3. Regenerate only those stills at higher Earth-photo resolution if needed.
4. Trend charts: use `trend-learning-curve` / `trend-returns` backups or replot from KPI JSON.

CSV: `docs/report/semester-project/figures/FIGURE_MANIFEST.csv`

