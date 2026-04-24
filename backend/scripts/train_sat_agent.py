from __future__ import annotations

import argparse
import os
import random
import subprocess
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
from autonomous_control.mpo_config import MPOConfig
from autonomous_control.training_runtime import make_attitude_control_env, run_episode
from utils.ml_training.ml_training_utils import (
    append_jsonl_record,
    append_run_markdown_event,
    checkpoint_path,
    create_run_dir,
    init_run_markdown,
)


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _save_checkpoint(agent: MPOAgent, path: str) -> None:
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


def _save_sat_sim_export_video(output_path: Path, *, controller_mode: str) -> Path:
    if controller_mode == "mpo":
        raise ValueError(
            "Sat Sim render export only supports controller modes with direct simulation policies "
            "(baseline, random). MPO render export is disabled until a real checkpoint-driven "
            "simulation controller is wired."
        )
    command = [
        sys.executable,
        str(BACKEND_DIR / "scripts" / "simulation_runner.py"),
        "--render-mode",
        "export",
        "--controller-mode",
        controller_mode,
        "--save-one-pass-30x",
        "--output-path",
        str(output_path),
    ]
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{BACKEND_DIR}{os.pathsep}{current_pythonpath}" if current_pythonpath else str(BACKEND_DIR)
    )
    subprocess.run(command, cwd=str(BACKEND_DIR), check=True, env=env)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train MPO satellite attitude agent.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--train-episodes", type=int, default=20)
    parser.add_argument("--warmup-episodes", type=int, default=0)
    parser.add_argument("--updates-per-step", type=int, default=1)
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--checkpoint-name", type=str, default="agent.pt")
    parser.add_argument("--save-video", action="store_true")
    parser.add_argument("--video-name", type=str, default="policy_trace.mp4")
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _seed_everything(args.seed)

    if args.controller_mode == "mpo":
        config = MPOConfig(warmup_episodes=args.warmup_episodes)
        env = make_attitude_control_env(reward_config=config.reward)
        agent = MPOAgent(env, config=config)
    elif args.controller_mode == "baseline":
        env = make_attitude_control_env()
        agent = MaxTorqueSweepPolicy(env, period_s=10.0)
    else:
        env = make_attitude_control_env()
        agent = RandomTorquePolicy(env)
    run_dir = create_run_dir(run_id=args.run_id)
    ckpt = checkpoint_path(run_dir, filename=args.checkpoint_name)

    init_run_markdown(
        run_dir,
        title=f"Controller Training Run ({args.controller_mode})",
        metadata={
            "run_dir": str(run_dir),
            "seed": args.seed,
            "train_episodes": args.train_episodes,
            "warmup_episodes": args.warmup_episodes,
            "controller_mode": args.controller_mode,
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
        },
    )

    last_result = None
    if args.controller_mode == "mpo":
        for ep in range(args.warmup_episodes):
            result = run_episode(env, agent, mode="warmup", train_updates_per_step=0)
            last_result = result
            append_run_markdown_event(
                run_dir,
                heading=f"Warmup episode {ep + 1}",
                payload={"episode_return": f"{result.episode_return:.6f}", "steps": result.steps},
            )

    for ep in range(args.train_episodes):
        episode_mode = "train" if args.controller_mode == "mpo" else "test"
        result = run_episode(
            env,
            agent,
            mode=episode_mode,
            train_updates_per_step=args.updates_per_step,
        )
        last_result = result
        append_run_markdown_event(
            run_dir,
            heading=f"Train episode {ep + 1}",
            payload={"episode_return": f"{result.episode_return:.6f}", "steps": result.steps},
        )

    if args.controller_mode == "mpo":
        _save_checkpoint(agent, str(ckpt))
        append_run_markdown_event(
            run_dir,
            heading="Checkpoint",
            payload={"path": str(ckpt)},
        )

    trace_video_path: str | None = None
    if args.save_video:
        if last_result is None:
            last_result = run_episode(env, agent, mode="test", train_updates_per_step=0)
        video_path = run_dir / args.video_name
        trace_video_path = str(_save_trace_video(last_result.states, video_path))
        append_run_markdown_event(
            run_dir,
            heading="Policy trace video",
            payload={"path": trace_video_path},
        )

    render_video_path: str | None = None
    if args.save_render_video:
        output_path = run_dir / args.render_video_name
        render_video_path = str(
            _save_sat_sim_export_video(output_path, controller_mode=args.controller_mode)
        )
        append_run_markdown_event(
            run_dir,
            heading="Sat Sim Export video",
            payload={"path": render_video_path},
        )

    append_jsonl_record(
        {
            "event": "train_run_finished",
            "timestamp_utc": datetime.now(tz=timezone.utc).isoformat(),
            "run_dir": str(run_dir),
            "seed": args.seed,
            "warmup_episodes": args.warmup_episodes,
            "train_episodes": args.train_episodes,
            "controller_mode": args.controller_mode,
            "checkpoint_path": str(ckpt) if args.controller_mode == "mpo" else None,
            "final_return": float(agent.episode_returns[-1]) if hasattr(agent, "episode_returns") and agent.episode_returns else float(last_result.episode_return) if last_result is not None else None,
            "video_path": trace_video_path,
            "trace_video_path": trace_video_path,
            "sat_sim_export_video_path": render_video_path,
        }
    )
    if args.controller_mode == "mpo":
        print(f"Training completed. Checkpoint saved to: {ckpt}")
    else:
        print(f"Controller run completed for mode: {args.controller_mode}")


if __name__ == "__main__":
    main()