# Analysis — export_resolution_720p

## 1. Hypothesis
Explicit 1280x720 export via RENDER.export_pixel_width/height

## 2. Frozen input
- Scenario: gate
- Clouds: ?

## 3. Control KPI
- export_wall_s: None
- export_frames_per_s: None
- n_frames_drawn: None

## 4. Treatment KPI
- export_wall_s: 0.9998722000018461
- export_frames_per_s: 4.0005112653323245
- n_frames_drawn: 4

## 5. Delta
- export_speedup: None
- relative_wall_reduction_pct: None

## 6. Parity
- passed: True
- notes: ffprobe width=1280 height=720 h264

## 7. Verdict
- supported

## 8. Closeout
promote
