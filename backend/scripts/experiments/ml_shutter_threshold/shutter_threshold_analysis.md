# Analysis — shutter_threshold_mpo

**Pipeline closeout:** [01-shutter-threshold.md](../../../docs/experiments/pipeline/4-documentation/01-shutter-threshold.md)  
Source JSON: `results/shutter_threshold_summary.json`

## Hypothesis

Threshold 0.9 reduces MPO shutter spam vs 0.5 with 15s capture window.

## Verdict table

| Claim | Criterion | t05 | t09 | Verdict |
|-------|-----------|-----|-----|---------|
| H1a — less spam at 0.9 | Mean cmds/ep &lt; 50% of t05 (258) | 516.0 | 514.9 | **Rejected** |
| H1c — learning | `learning_mode` true | false | false | **Rejected** |
| H1d — meaningful captures | `shutter_meaningful_fraction` &gt; 0 | 0.0 | 0.0 | **Rejected** |

**Overall H1: not supported** — see pipeline doc for full table and artifacts.

## Arms (summary JSON)

```json
{
  "mpo_t05": {
    "verdict": "inconclusive",
    "threshold": 0.5,
    "learning_mode": false,
    "shutter_cmds_per_episode": [516, 516, 516, 516, 516, 516, 516],
    "eval_return_mean": -101.59999999999805
  },
  "mpo_t09": {
    "verdict": "inconclusive",
    "threshold": 0.9,
    "learning_mode": false,
    "shutter_cmds_per_episode": [508, 516, 516, 516, 516, 516, 516],
    "eval_return_mean": -101.59999999999805
  }
}
```

## Plots

- `results/plots/shutter_unit_hist.png`
- `results/plots/fire_rate_vs_threshold.png`
- `results/plots/shutter_cmds_per_episode.png`
- `results/plots/train_returns.png`
