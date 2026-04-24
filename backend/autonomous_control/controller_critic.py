"""Critic network used by the MPO agent."""

from __future__ import annotations

import torch
import torch.nn as nn

from .MLP_model import MLP


class Critic(nn.Module):
    """Simple MLP Q-function."""

    def __init__(self, obs_size: int, action_size: int, num_layers: int, num_units: int):
        super().__init__()
        self.net = MLP([obs_size + action_size] + ([num_units] * num_layers) + [1])

    def forward(self, x: torch.Tensor, a: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([x, a], dim=-1))

