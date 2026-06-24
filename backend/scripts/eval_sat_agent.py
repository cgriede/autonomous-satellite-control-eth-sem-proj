from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np
import torch

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from autonomous_control.controller_agent import MPOAgent
from autonomous_control.controller_baselines import MaxTorqueSweepPolicy, RandomTorquePolicy
from autonomous_control.config.randomness import RandomnessConfig, apply_global_seed, derive_seed
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.training_preflight import TrainingPreflightError, run_training_gate
from autonomous_control.training_runtime import EpisodeResult, make_attitude_control_env, run_episode
from environment_definition.constants import RenderMode
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import sample_satellite_altitude
from render.render_main import render_from_series
from utils.ml_training.ml_training_utils import (
    append_jsonl_record,
    append_run_markdown_event,
    create_run_dir,
    init_run_markdown,
)

def _load_checkpoint(agent: MPOAgent, ckpt_path: Path) -> None:
    payload = torch.load(str(ckpt_path), map_location=agent.device)
    agent.pi.load_state_dict(payload["pi"])
    agent.pi_target.load_state_dict(payload["pi_target"])
    agent.q1.load_state_dict(payload["q1"])
    agent.q2.load_state_dict(payload["q2"])
    agent.q1_target.load_state_dict(payload["q1_target"])
    agent.q2_target.load_state_dict(payload["q2_target"])
    agent.q_optimizer.load_state_dict(payload["q_optimizer"])
    agent.pi_optimizer.load_state_dict(payload["pi_optimizer"])
    agent.eta_optimizer.load_state_dict(payload["eta_optimizer"])
    agent.log_eta = torch.tensor(float(payload["log_eta"]), device=agent.device, requires_grad=True)
    agent.step_counter = int(payload.get("step_counter", 0))
    agent.episode_returns = list(payload.get("episode_returns", []))


def _save_trace_video(states: list[np.ndarray], output_path: Path, fps: int = 20) -> Path:
    import imageio.v2 as imageio
    import matplotlib.pyplot as plt

    frames: list[np.ndarray] = []
    labels = ["angle_rel_nadir(rad)", "omega_sat(rad/s)", "alpha_sat(rad/s^2)", "angle_to_target(rad)", "omega_wheel(rad/s)"]
    n_dims = int(np.asarray(states[0], dtype=np.float32).shape[0]) if states else 0
    labels = labels[:n_dims] if n_dims <= len(labels) else [f"state_{j}" for j in range(n_dims)]
    for i in range(1, len(states) + 1):
        arr = np.asarray(states[:i], dtype=np.float32)
        fig, axes = plt.subplots(n_dims, 1, figsize=(8, max(3, 2 * n_dims)), constrained_layout=True)
        if n_dims == 1:
            axes = [axes]
        for idx, label in enumerate(labels):
            axes[idx].plot(arr[:, idx], color="tab:blue")
            axes[idx].set_ylabel(label)
            axes[idx].grid(True, alpha=0.3)
        axes[-1].set_xlabel("step")
        fig.canvas.draw()
        frame = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
        frame = frame.reshape(fig.canvas.get_width_height()[::-1] + (4,))[:, :, :3]
        frames.append(frame)
        plt.close(fig)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(str(output_path), frames, fps=fps)
    return output_path


def _save_sat_sim_export_video(output_path: Path, *, simulation_series) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    out = render_from_series(
        simulation_series=simulation_series,
        render_mode=RenderMode.EXPORT,
        output_path=output_path,
    )
    if out is None:
        raise RuntimeError("Render export did not produce an output path.")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate MPO satellite attitude agent.")
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--eval-episodes", type=int, default=5)
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--save-video", type=Path, default=None)
    parser.add_argument(
        "--save-render-video",
        action="store_true",
        help="Export Sat Sim render video (supported for baseline/random controller modes).",
    )
    parser.add_argument("--render-video-name", type=str, default="sat_sim_export.mp4")
    parser.add_argument(
        "--controller-mode",
        type=str,
        choices=("mpo", "baseline", "random"),
        default="mpo",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip training feature checks and pytest gate (not recommended).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.skip_preflight:
        try:
            run_training_gate()
        except TrainingPreflightError as exc:
            print(f"Training preflight failed:\n{exc}", file=sys.stderr)
            raise SystemExit(1) from exc
    seed_cfg = RandomnessConfig(seed=args.seed)
    apply_global_seed(seed_cfg)
    sampled_altitude = sample_satellite_altitude(
        seed=derive_seed(args.seed, "mission_altitude")
    )
    if args.controller_mode == "mpo":
        if args.checkpoint is None:
            raise ValueError("--checkpoint is required when --controller-mode mpo.")
        config = MPOConfig(warmup_episodes=0)
        env = make_attitude_control_env(reward_config=config.reward)
        agent = MPOAgent(env, config=config)
        _load_checkpoint(agent, args.checkpoint)
    elif args.controller_mode == "baseline":
        env = make_attitude_control_env()
        agent = MaxTorqueSweepPolicy(env, period_s=10.0)
    else:
        env = make_attitude_control_env()
        agent = RandomTorquePolicy(env)

    run_dir = create_run_dir(run_id=args.run_id)
    init_run_markdown(
        run_dir,
        title=f"Controller Evaluation Run ({args.controller_mode})",
        metadata={
            "run_dir": str(run_dir),
            "seed": args.seed,
            "eval_episodes": args.eval_episodes,
            "controller_mode": args.controller_mode,
            "checkpoint": str(args.checkpoint) if args.checkpoint is not None else None,
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        },
    )

    returns: list[float] = []
    last_result: EpisodeResult | None = None
    for ep in range(args.eval_episodes):
        result = run_episode(
            env,
            agent,
            mode="test",
            train_updates_per_step=0,
            satellite_altitude=sampled_altitude,
            np_rng=np.random.default_rng(derive_seed(args.seed, "eval_episode", ep)),
        )
        returns.append(result.episode_return)
        last_result = result
        append_run_markdown_event(
            run_dir,
            heading=f"Eval episode {ep + 1}",
            payload={"episode_return": f"{result.episode_return:.6f}", "steps": result.steps},
        )

    trace_video_path: str | None = None
    if args.save_video is not None and last_result is not None:
        output_path = args.save_video if args.save_video.is_absolute() else (run_dir / args.save_video)
        trace_video_path = str(_save_trace_video(last_result.states, output_path))
        append_run_markdown_event(
            run_dir,
            heading="Policy trace video",
            payload={"path": trace_video_path},
        )

    render_video_path: str | None = None
    if args.save_render_video:
        if last_result is None:
            last_result = run_episode(
                env,
                agent,
                mode="test",
                train_updates_per_step=0,
                satellite_altitude=sampled_altitude,
                np_rng=np.random.default_rng(derive_seed(args.seed, "render_test", 0)),
            )
        output_path = run_dir / args.render_video_name
        render_video_path = str(
            _save_sat_sim_export_video(
                output_path,
                simulation_series=last_result.simulation_series,
            )
        )
        append_run_markdown_event(
            run_dir,
            heading="Sat Sim Export video",
            payload={"path": render_video_path},
        )

    mean_return = float(np.mean(returns)) if returns else 0.0
    std_return = float(np.std(returns)) if returns else 0.0
    append_jsonl_record(
        {
            "event": "eval_run_finished",
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
            "run_dir": str(run_dir),
            "seed": args.seed,
            "eval_episodes": args.eval_episodes,
            "controller_mode": args.controller_mode,
            "checkpoint_path": str(args.checkpoint) if args.checkpoint is not None else None,
            "mean_return": mean_return,
            "std_return": std_return,
            "video_path": trace_video_path,
            "trace_video_path": trace_video_path,
            "sat_sim_export_video_path": render_video_path,
        }
    )
    print(f"Evaluation completed. mean_return={mean_return:.6f}, std_return={std_return:.6f}")


if __name__ == "__main__":
    main()
