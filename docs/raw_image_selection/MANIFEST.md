# Raw image selection manifest

Generated: `2026-07-10T12:52:17Z`
Total entries: **261**

## By kind

| Kind | Count |
|------|------:|
| `frame` | 122 |
| `plot` | 126 |
| `source_video` | 13 |

## By theme

| Theme | Count |
|-------|------:|
| `learning-vs-not` | 63 |
| `trend-learning-curve` | 51 |
| `trend-returns` | 51 |
| `dynamic-safety-maneuver` | 28 |
| `dynamic-cloud-generation` | 24 |
| `episode-diagnostics-eval` | 18 |
| `static-target-placement` | 13 |
| `behaviour-selective-shutter` | 13 |

## Learning label

| Label | Count |
|-------|------:|
| `learning` | 52 |
| `na` | 132 |
| `not_learning` | 77 |

## Theme folders

| Folder | Purpose |
|--------|---------|
| `themes/01_target_placement/` | static target corridor |
| `themes/02_cloud_motion/` | dynamic cloud neighbor series |
| `themes/03_safety_maneuver/` | torque safety cycle scouts |
| `themes/04_selective_shutter/` | learned selective shutter |
| `themes/05_learning_vs_not/` | learning vs not-learning paired stills + curves |

Each theme has `frames/` and `source/` (MP4 hardlink/copy + `*.SOURCE.txt` pointer).

To re-pick frames: open the source MP4, note time, re-run extract or adjust this script.

