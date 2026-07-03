"""Factored MPO actor: Categorical(50) target + Gaussian move + Gaussian shutter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from autonomous_control.controller_encoder import ControllerEncoder
from autonomous_control.controller_observation import ControllerObservationLayout
from autonomous_control.mpo_config import LOG_STD_MAX, LOG_STD_MIN, MPOConfig

from _action_constants import (
    MOVE_IDX,
    N_ACTION_DIMS,
    N_TARGETS,
    SHUTTER_IDX,
    encode_applied_action,
)


def _split_gaussian_params(head_out: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    mu, log_std = torch.chunk(head_out, 2, dim=-1)
    log_std = torch.clamp(log_std, LOG_STD_MIN, LOG_STD_MAX)
    std = torch.exp(log_std)
    return mu.squeeze(-1), std.squeeze(-1)


def _atanh_clamped(x: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    x = torch.clamp(x, -1.0 + eps, 1.0 - eps)
    return 0.5 * (torch.log1p(x) - torch.log1p(-x))


@dataclass(frozen=True)
class FactoredActionSample:
    action: torch.Tensor
    target_idx: torch.Tensor
    move_z: torch.Tensor
    shutter_z: torch.Tensor


def _expand_dists_for_batch(
    dists: dict[str, torch.distributions.Distribution],
    batch_size: int,
) -> dict[str, torch.distributions.Distribution]:
    current = int(dists["target"].logits.shape[0])
    if batch_size == current:
        return dists
    if batch_size % current != 0:
        raise ValueError(f"Cannot expand dist batch {current} to action batch {batch_size}")
    factor = batch_size // current
    return {
        "target": torch.distributions.Categorical(
            logits=dists["target"].logits.repeat(factor, 1),
        ),
        "move": torch.distributions.Normal(
            loc=dists["move"].loc.repeat(factor),
            scale=dists["move"].scale.repeat(factor),
        ),
        "shutter": torch.distributions.Normal(
            loc=dists["shutter"].loc.repeat(factor),
            scale=dists["shutter"].scale.repeat(factor),
        ),
    }


def _pack_actions_from_parts(
    target_idx: torch.Tensor,
    move_gym: torch.Tensor,
    shutter_gym: torch.Tensor,
) -> torch.Tensor:
    """Pack target one-hot + move + shutter into [..., N_ACTION_DIMS]."""
    actions = torch.zeros(
        *target_idx.shape,
        N_ACTION_DIMS,
        device=target_idx.device,
        dtype=torch.float32,
    )
    actions.scatter_(-1, target_idx.unsqueeze(-1), 1.0)
    actions[..., MOVE_IDX] = move_gym
    actions[..., SHUTTER_IDX] = shutter_gym
    return actions


class FactoredActor(nn.Module):
    """Shared trunk + categorical target + two squashed Gaussian bool heads."""

    N_CONTINUOUS = 2

    def __init__(
        self,
        layout: ControllerObservationLayout,
        n_targets: int,
        config: MPOConfig,
    ) -> None:
        super().__init__()
        self.n_targets = int(n_targets)
        self.config = config
        self.encoder = ControllerEncoder(
            layout,
            config,
            activation=config.activation_actor,
        )
        trunk_dim = self.encoder.output_dim
        self.target_head = nn.Linear(trunk_dim, self.n_targets)
        self.move_head = nn.Linear(trunk_dim, 2)
        self.shutter_head = nn.Linear(trunk_dim, 2)

    def forward(
        self,
        scalars: torch.Tensor,
        vision: tuple[torch.Tensor, ...],
    ) -> dict[str, torch.distributions.Distribution]:
        features = self.encoder(scalars, vision)
        target_logits = self.target_head(features)
        move_mu, move_std = _split_gaussian_params(self.move_head(features))
        shutter_mu, shutter_std = _split_gaussian_params(self.shutter_head(features))
        return {
            "target": torch.distributions.Categorical(logits=target_logits),
            "move": torch.distributions.Normal(move_mu, move_std),
            "shutter": torch.distributions.Normal(shutter_mu, shutter_std),
        }

    def sample_stored_action(
        self,
        dists: dict[str, torch.distributions.Distribution],
        *,
        greedy: bool = False,
    ) -> FactoredActionSample:
        actions = self.sample_stored_actions(dists, 1, greedy=greedy)
        target_idx = actions[0, :, : self.n_targets].argmax(dim=-1)
        move_gym = actions[0, :, MOVE_IDX]
        shutter_gym = actions[0, :, SHUTTER_IDX]
        move_z = _atanh_clamped(move_gym)
        shutter_z = _atanh_clamped(shutter_gym)
        return FactoredActionSample(
            action=actions[0],
            target_idx=target_idx,
            move_z=move_z,
            shutter_z=shutter_z,
        )

    def sample_stored_actions(
        self,
        dists: dict[str, torch.distributions.Distribution],
        num_samples: int,
        *,
        greedy: bool = False,
    ) -> torch.Tensor:
        """Sample ``num_samples`` actions per batch row → ``[S, B, N_ACTION_DIMS]``."""
        s = int(num_samples)
        if greedy:
            target_idx = dists["target"].probs.argmax(dim=-1).unsqueeze(0).expand(s, -1)
            move_gym = torch.tanh(dists["move"].loc).unsqueeze(0).expand(s, -1)
            shutter_gym = torch.tanh(dists["shutter"].loc).unsqueeze(0).expand(s, -1)
        else:
            target_idx = dists["target"].sample((s,))
            move_gym = torch.tanh(dists["move"].rsample((s,)))
            shutter_gym = torch.tanh(dists["shutter"].rsample((s,)))
        return _pack_actions_from_parts(target_idx, move_gym, shutter_gym)

    def log_prob(
        self,
        dists: dict[str, torch.distributions.Distribution],
        action: torch.Tensor,
    ) -> torch.Tensor:
        """Sum log-prob over target categorical + tanh-squashed move/shutter."""
        if action.dim() == 3:
            num_samples, batch_size, _ = action.shape
            flat = action.reshape(num_samples * batch_size, -1)
            expanded = _expand_dists_for_batch(dists, flat.shape[0])
            log_flat = self._log_prob_flat(expanded, flat)
            return log_flat.reshape(num_samples, batch_size)

        expanded = _expand_dists_for_batch(dists, action.shape[0])
        return self._log_prob_flat(expanded, action)

    def _log_prob_flat(
        self,
        dists: dict[str, torch.distributions.Distribution],
        action: torch.Tensor,
    ) -> torch.Tensor:
        target_idx = action[:, : self.n_targets].argmax(dim=-1)
        log_target = dists["target"].log_prob(target_idx)

        move_gym = action[:, MOVE_IDX]
        shutter_gym = action[:, SHUTTER_IDX]
        move_z = _atanh_clamped(move_gym)
        shutter_z = _atanh_clamped(shutter_gym)

        log_move = dists["move"].log_prob(move_z)
        log_shutter = dists["shutter"].log_prob(shutter_z)
        # Tanh-squashing Jacobian: log π(a) = log π_z(z) − log(1−a²).
        # Since log(1−a²) < 0, we negate to get a positive (density-increasing) correction.
        jacobian = -torch.log(1.0 - move_gym.pow(2) + 1e-6) - torch.log(
            1.0 - shutter_gym.pow(2) + 1e-6
        )
        return log_target + log_move + log_shutter + jacobian

    def continuous_kl_params(
        self,
        dists: dict[str, torch.distributions.Distribution],
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Stack move+shutter into 2-D Gaussian for decoupled KL."""
        move_mu = dists["move"].loc
        move_std = dists["move"].scale
        shutter_mu = dists["shutter"].loc
        shutter_std = dists["shutter"].scale
        mu = torch.stack([move_mu, shutter_mu], dim=-1)
        std = torch.stack([move_std, shutter_std], dim=-1)
        return mu, std


def numpy_action_from_sample(sample: FactoredActionSample, *, batch_index: int = 0) -> np.ndarray:
    row = sample.action[batch_index].detach().cpu().numpy().astype(np.float32)
    return row


def sample_numpy_action(
    actor: FactoredActor,
    scalars: torch.Tensor,
    vision: tuple[torch.Tensor, ...],
    *,
    train: bool,
) -> np.ndarray:
    with torch.no_grad():
        dists = actor(scalars, vision)
        sample = actor.sample_stored_action(dists, greedy=not train)
    return numpy_action_from_sample(sample, batch_index=0)


__all__ = [
    "FactoredActionSample",
    "FactoredActor",
    "encode_applied_action",
    "numpy_action_from_sample",
    "sample_numpy_action",
]
