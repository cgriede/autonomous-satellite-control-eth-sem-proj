"""Run MPO training and export best/mean Sat Sim videos for train + eval phases."""

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
from tqdm import tqdm

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from autonomous_control.config.randomness import RandomnessConfig, apply_global_seed, derive_seed
from autonomous_control.controller_agent import MPOAgent
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.training_preflight import TrainingPreflightError, run_training_preflight
from autonomous_control.training_runtime import EpisodeResult, make_attitude_control_env, run_episode
from environment_definition.constants import RenderMode, SIMULATION
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import sample_satellite_altitude
from render.render_main import render_from_series
from utils.ml_training.ml_training_utils import (
    append_jsonl_record,
    append_run_markdown_event,
    checkpoint_path,
    create_run_dir,
    init_run_markdown,
)


@dataclass(frozen=True)
class PhaseSummary:
    phase: str
    episodes: int
    return_mean: float
    return_std: float
    return_best: float
    return_worst: float
    best_episode_idx: int
    mean_episode_idx: int


def _episode_return(result: EpisodeResult) -> float:
    return float(result.episode_return)


def _best_episode_index(results: list[EpisodeResult]) -> int:
    return max(range(len(results)), key=lambda i: _episode_return(results[i]))


def _mean_episode_index(results: list[EpisodeResult]) -> int:
    if not results:
        return 0
    totals = np.asarray([_episode_return(r) for r in results], dtype=np.float64)
    mean = float(np.mean(totals))
    return int(np.argmin(np.abs(totals - mean)))


def _summarize_phase(phase: str, results: list[EpisodeResult]) -> PhaseSummary:
    totals = np.asarray([_episode_return(r) for r in results], dtype=np.float64)
    return PhaseSummary(
        phase=phase,
        episodes=len(results),
        return_mean=float(np.mean(totals)) if len(totals) else 0.0,
        return_std=float(np.std(totals)) if len(totals) else 0.0,
        return_best=float(np.max(totals)) if len(totals) else 0.0,
        return_worst=float(np.min(totals)) if len(totals) else 0.0,
        best_episode_idx=_best_episode_index(results),
        mean_episode_idx=_mean_episode_index(results),
    )


def _export_sat_sim_video(
    *,
    result: EpisodeResult,
    out_path: Path,
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_from_series(
        simulation_series=result.simulation_series,
        render_mode=RenderMode.EXPORT,
        output_path=out_path,
    )
    if rendered is None or not out_path.exists():
        raise RuntimeError(f"Render export failed: {out_path}")
    return out_path


def _write_episode_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _save_checkpoint(agent: MPOAgent, path: Path) -> None:
    import torch

    payload = {
        "pi": agent.pi.state_dict(),
        "pi_target": agent.pi_target.state_dict(),
        "q1": agent.q1.state_dict(),
        "q2": agent.q2.state_dict(),
        "q1_target": agent.q1_target.state_dict(),
        "q2_target": agent.q2_target.state_dict(),
        "q_optimizer": agent.q_optimizer.state_dict(),
        "pi_optimizer": agent.pi_optimizer.state_dict(),
        "eta_optimizer": agent.eta_optimizer.state_dict(),
        "log_eta": float(agent.log_eta.detach().cpu().item()),
        "step_counter": agent.step_counter,
        "episode_returns": agent.episode_returns,
    }
    torch.save(payload, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MPO training showcase with video exports.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--train-episodes", type=int, default=20)
    parser.add_argument("--eval-episodes", type=int, default=5)
    parser.add_argument("--warmup-episodes", type=int, default=5)
    parser.add_argument("--updates-per-step", type=int, default=1)
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument(
        "--export-speed-multiplier",
        type=float,
        default=float(SIMULATION.export_speed_multiplier),
        help="Sim-time compression for Sat Sim export (default: SIMULATION.export_speed_multiplier).",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip training preflight checks.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.skip_preflight:
        try:
            run_training_preflight()
        except TrainingPreflightError as exc:
            print(f"Training preflight failed:\n{exc}", file=sys.stderr)
            raise SystemExit(1) from exc

    speed_mult = float(args.export_speed_multiplier)
    print(
        f"Sat Sim export time compression: {speed_mult:.0f}x "
        f"(SIMULATION.export_speed_multiplier)"
    )

    seed_cfg = RandomnessConfig(seed=args.seed)
    apply_global_seed(seed_cfg)
    sampled_altitude = sample_satellite_altitude(
        seed=derive_seed(args.seed, "mission_altitude")
    )

    config = MPOConfig(warmup_episodes=args.warmup_episodes)
    env = make_attitude_control_env(reward_config=config.reward)
    agent = MPOAgent(env, config=config)
    run_dir = create_run_dir(run_id=args.run_id)
    ckpt = checkpoint_path(run_dir)

    init_run_markdown(
        run_dir,
        title="MPO Training Showcase",
        metadata={
            "run_dir": str(run_dir),
            "seed": args.seed,
            "train_episodes": args.train_episodes,
            "eval_episodes": args.eval_episodes,
            "warmup_episodes": args.warmup_episodes,
            "export_speed_multiplier": speed_mult,
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        },
    )

    train_results: list[EpisodeResult] = []
    eval_results: list[EpisodeResult] = []
    started = time.perf_counter()

    # Warmup (random + baseline split like train_sat_agent)
    random_warmup = (args.warmup_episodes + 1) // 2
    baseline_warmup = args.warmup_episodes // 2
    warmup_idx = 0
    if args.warmup_episodes > 0:
        with tqdm(total=args.warmup_episodes, desc="Warmup", unit="ep") as pbar:
            for controller, count in (("random", random_warmup), ("baseline", baseline_warmup)):
                for _ in range(count):
                    run_episode(
                        env,
                        agent,
                        mode="warmup",
                        train_updates_per_step=0,
                        warmup_controller=controller,
                        satellite_altitude=sampled_altitude,
                        np_rng=np.random.default_rng(
                            derive_seed(args.seed, "warmup_episode", warmup_idx)
                        ),
                    )
                    warmup_idx += 1
                    pbar.update(1)

    with tqdm(total=args.train_episodes, desc="Train", unit="ep") as pbar:
        for ep in range(args.train_episodes):
            result = run_episode(
                env,
                agent,
                mode="train",
                train_updates_per_step=args.updates_per_step,
                satellite_altitude=sampled_altitude,
                np_rng=np.random.default_rng(derive_seed(args.seed, "train_episode", ep)),
            )
            train_results.append(result)
            pbar.set_postfix(reward=f"{result.episode_return:.1f}")
            pbar.update(1)

    _save_checkpoint(agent, ckpt)

    with tqdm(total=args.eval_episodes, desc="Eval", unit="ep") as pbar:
        for ep in range(args.eval_episodes):
            result = run_episode(
                env,
                agent,
                mode="test",
                train_updates_per_step=0,
                satellite_altitude=sampled_altitude,
                np_rng=np.random.default_rng(derive_seed(args.seed, "eval_episode", ep)),
            )
            eval_results.append(result)
            pbar.set_postfix(reward=f"{result.episode_return:.1f}")
            pbar.update(1)

    train_summary = _summarize_phase("train", train_results)
    eval_summary = _summarize_phase("eval", eval_results)

    from dataclasses import replace
    import environment_definition.constants.SIMULATION as sim_mod

    if speed_mult != float(sim_mod.SIMULATION.export_speed_multiplier):
        sim_mod.SIMULATION = replace(
            sim_mod.SIMULATION,
            export_speed_multiplier=speed_mult,
        )

    video_exports: dict[str, Path] = {}
    selections = (
        ("train_best", train_results, train_summary.best_episode_idx),
        ("train_mean", train_results, train_summary.mean_episode_idx),
        ("eval_best", eval_results, eval_summary.best_episode_idx),
        ("eval_mean", eval_results, eval_summary.mean_episode_idx),
    )
    for label, results, idx in selections:
        out = run_dir / f"{label}.mp4"
        print(f"Exporting {label} (episode {idx + 1}, return={_episode_return(results[idx]):.2f})...")
        video_exports[label] = _export_sat_sim_video(result=results[idx], out_path=out)

    elapsed = time.perf_counter() - started
    train_rows = [
        {
            "phase": "train",
            "episode": i + 1,
            "total_reward": _episode_return(r),
            "average_reward": _episode_return(r) / max(1, r.steps),
            "steps": r.steps,
        }
        for i, r in enumerate(train_results)
    ]
    eval_rows = [
        {
            "phase": "eval",
            "episode": i + 1,
            "total_reward": _episode_return(r),
            "average_reward": _episode_return(r) / max(1, r.steps),
            "steps": r.steps,
        }
        for i, r in enumerate(eval_results)
    ]
    _write_episode_csv(run_dir / "train_episodes.csv", train_rows)
    _write_episode_csv(run_dir / "eval_episodes.csv", eval_rows)

    summary_lines = [
        f"Run directory: {run_dir}",
        f"Checkpoint: {ckpt}",
        f"Elapsed: {elapsed / 60.0:.1f} min",
        "",
        "Train:",
        f"  mean return = {train_summary.return_mean:.2f} ± {train_summary.return_std:.2f}",
        f"  best  ep {train_summary.best_episode_idx + 1}  return = {train_summary.return_best:.2f}",
        f"  mean  ep {train_summary.mean_episode_idx + 1}  return = {_episode_return(train_results[train_summary.mean_episode_idx]):.2f}",
        "",
        "Eval:",
        f"  mean return = {eval_summary.return_mean:.2f} ± {eval_summary.return_std:.2f}",
        f"  best  ep {eval_summary.best_episode_idx + 1}  return = {eval_summary.return_best:.2f}",
        f"  mean  ep {eval_summary.mean_episode_idx + 1}  return = {_episode_return(eval_results[eval_summary.mean_episode_idx]):.2f}",
        "",
        "Videos (30x sim-time compression by default):",
    ]
    for label, path in video_exports.items():
        summary_lines.append(f"  {label}: {path}")
    summary_text = "\n".join(summary_lines)
    print("\n" + summary_text)
    (run_dir / "showcase_summary.txt").write_text(summary_text + "\n", encoding="utf-8")

    append_run_markdown_event(
        run_dir,
        heading="Showcase summary",
        payload={
            "train_mean_return": f"{train_summary.return_mean:.6f}",
            "train_best_return": f"{train_summary.return_best:.6f}",
            "eval_mean_return": f"{eval_summary.return_mean:.6f}",
            "eval_best_return": f"{eval_summary.return_best:.6f}",
            "videos": {k: str(v) for k, v in video_exports.items()},
        },
    )
    append_jsonl_record(
        {
            "event": "mpo_training_showcase_finished",
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
            "run_dir": str(run_dir),
            "checkpoint_path": str(ckpt),
            "train_episodes": args.train_episodes,
            "eval_episodes": args.eval_episodes,
            "train_mean_return": train_summary.return_mean,
            "eval_mean_return": eval_summary.return_mean,
            "videos": {k: str(v) for k, v in video_exports.items()},
            "export_speed_multiplier": speed_mult,
        }
    )


if __name__ == "__main__":
    main()
