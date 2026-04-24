# User Manual: Controllers and Rendering

This manual explains how to run controller experiments and how rendering maps to simulation behavior.

## Environment Setup

From the repository root:

```bash
conda activate auto-sat
cd backend
```

## Controller Modes

Training/evaluation scripts support:

- `mpo`: learned MPO policy (`MPOAgent`), supports checkpoint load/save.
- `baseline`: deterministic max-torque sweep policy.
- `random`: uniform random torque policy.

## Train Controllers

```bash
python scripts/train_sat_agent.py --controller-mode mpo --seed 0 --train-episodes 20 --warmup-episodes 0
python scripts/train_sat_agent.py --controller-mode baseline --seed 0 --train-episodes 20
python scripts/train_sat_agent.py --controller-mode random --seed 0 --train-episodes 20
```

Notes:

- `--controller-mode mpo` is the only mode that writes an MPO checkpoint (`agent.pt`).
- Baseline/random runs are controller rollouts without MPO weight updates.

## Evaluate Controllers

```bash
python scripts/eval_sat_agent.py --controller-mode mpo --checkpoint autonomous_control/models/<run_id>/agent.pt --eval-episodes 5
python scripts/eval_sat_agent.py --controller-mode baseline --eval-episodes 5
python scripts/eval_sat_agent.py --controller-mode random --eval-episodes 5
```

## Rendering and Export

Render CLI currently supports simulation controller modes:

- `baseline`
- `random`

Run interactive render:

```bash
python render/render_main.py --render-mode interactive --controller-mode random
```

Export one-pass video:

```bash
python render/render_main.py --render-mode export --controller-mode baseline --save-one-pass-30x
```

Optional output path:

```bash
python render/render_main.py --render-mode export --controller-mode random --save-one-pass-30x --output-path autonomous_control/models/my_run/sat_sim_export.mp4
```

## Fidelity Rule (What You See Is What Runs)

- Rendered behavior must come from the real simulation model and selected controller mode.
- No hidden substitute controller is used in visualization.
- If a model component exists (for example reaction-wheel dynamics), that same modeled behavior drives both simulation state and rendered output.

## VS Code Launch Configs

Useful launch entries in `.vscode/launch.json`:

- `Sat Sim Interactive`
- `Sat Sim Export`
- `MPO: Train satellite agent`
- `MPO: Eval satellite agent`
