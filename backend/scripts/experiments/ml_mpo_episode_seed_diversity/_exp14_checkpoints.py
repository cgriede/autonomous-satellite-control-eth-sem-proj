"""Save / load FactoredMPOAgent training state across screen → Stage B."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from _exp14_runner_common import RESULTS_DIR

CHECKPOINT_ROOT = RESULTS_DIR / "checkpoints"


def checkpoint_path(arm_id: str, *, tag: str = "screen_final") -> Path:
    return CHECKPOINT_ROOT / arm_id / f"{tag}.pt"


def checkpoint_meta_path(arm_id: str, *, tag: str = "screen_final") -> Path:
    return CHECKPOINT_ROOT / arm_id / f"{tag}.json"


def save_agent_checkpoint(
    agent: Any,
    *,
    arm_id: str,
    tag: str,
    phase: str,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Persist policy/critic weights, optimizers, and training counters."""
    out_path = checkpoint_path(arm_id, tag=tag)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "version": 1,
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "arm_id": arm_id,
        "phase": phase,
        "tag": tag,
        "entropy_coef": float(agent.entropy_coef),
        "step_counter": int(agent.step_counter),
        "episode_returns": [float(x) for x in agent.episode_returns],
        "metrics": {k: [float(x) for x in vals] for k, vals in agent.metrics.items()},
        "networks": {
            "pi": agent.pi.state_dict(),
            "pi_target": agent.pi_target.state_dict(),
            "q1": agent.q1.state_dict(),
            "q2": agent.q2.state_dict(),
            "q1_target": agent.q1_target.state_dict(),
            "q2_target": agent.q2_target.state_dict(),
        },
        "optimizers": {
            "pi": agent.pi_optimizer.state_dict(),
            "q": agent.q_optimizer.state_dict(),
            "eta": agent.eta_optimizer.state_dict(),
            "alpha": agent.alpha_optimizer.state_dict(),
        },
        "trust_region": {
            "log_eta": agent.log_eta.detach().cpu(),
            "log_alpha_mu": agent.log_alpha_mu.detach().cpu(),
            "log_alpha_sigma": agent.log_alpha_sigma.detach().cpu(),
        },
        "metadata": dict(metadata or {}),
    }
    torch.save(payload, out_path)

    meta = {
        "checkpoint_path": str(out_path),
        "arm_id": arm_id,
        "phase": phase,
        "tag": tag,
        "saved_at_utc": payload["saved_at_utc"],
        **(metadata or {}),
    }
    meta_path = checkpoint_meta_path(arm_id, tag=tag)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return out_path


def load_agent_checkpoint(agent: Any, path: Path | str) -> dict[str, Any]:
    """Restore agent weights/optimizers; returns checkpoint metadata."""
    ckpt_path = Path(path)
    if not ckpt_path.is_file():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")

    payload = torch.load(ckpt_path, map_location=agent.device, weights_only=False)
    nets = payload["networks"]
    agent.pi.load_state_dict(nets["pi"])
    agent.pi_target.load_state_dict(nets["pi_target"])
    agent.q1.load_state_dict(nets["q1"])
    agent.q2.load_state_dict(nets["q2"])
    agent.q1_target.load_state_dict(nets["q1_target"])
    agent.q2_target.load_state_dict(nets["q2_target"])

    opts = payload["optimizers"]
    agent.pi_optimizer.load_state_dict(opts["pi"])
    agent.q_optimizer.load_state_dict(opts["q"])
    agent.eta_optimizer.load_state_dict(opts["eta"])
    agent.alpha_optimizer.load_state_dict(opts["alpha"])

    tr = payload["trust_region"]
    agent.log_eta.data.copy_(tr["log_eta"].to(agent.device))
    agent.log_alpha_mu.data.copy_(tr["log_alpha_mu"].to(agent.device))
    agent.log_alpha_sigma.data.copy_(tr["log_alpha_sigma"].to(agent.device))

    agent.step_counter = int(payload.get("step_counter", 0))
    agent.episode_returns = [float(x) for x in payload.get("episode_returns", [])]
    agent.metrics = {
        k: [float(x) for x in vals] for k, vals in (payload.get("metrics") or {}).items()
    }
    if "entropy_coef" in payload:
        agent.entropy_coef = float(payload["entropy_coef"])

    return {
        "arm_id": payload.get("arm_id"),
        "phase": payload.get("phase"),
        "tag": payload.get("tag"),
        "saved_at_utc": payload.get("saved_at_utc"),
        **(payload.get("metadata") or {}),
    }


def resolve_screen_checkpoint(arm_id: str) -> Path:
    return checkpoint_path(arm_id, tag="screen_final")


__all__ = [
    "CHECKPOINT_ROOT",
    "checkpoint_meta_path",
    "checkpoint_path",
    "load_agent_checkpoint",
    "resolve_screen_checkpoint",
    "save_agent_checkpoint",
]
