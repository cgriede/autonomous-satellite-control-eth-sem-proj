"""MLP building blocks for autonomous control models."""

from __future__ import annotations

import torch.nn as nn


class MLP(nn.Module):
    '''
    A simple ReLU MLP constructed from a list of layer widths.
    LayerNorm applied after each hidden Linear layer and before activation to prevent initialization issues
    '''
    def __init__(self, sizes, activation=nn.ReLU, dropout=0.0):
        super().__init__()
        layers = []
        for i, (in_size, out_size) in enumerate(zip(sizes[:-1], sizes[1:])):
            layers.append(nn.Linear(in_size, out_size))
            if i < len(sizes) - 2:
                layers.append(activation())
                if dropout > 0.0:
                    layers.append(nn.Dropout(p=dropout))
        self.layers = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.layers(x)

def init_weights_xavier(m):
    if isinstance(m, nn.Linear):
        nn.init.xavier_uniform_(m.weight)
        if m.bias is not None:
            nn.init.zeros_(m.bias)

def init_weights_he(m):
        if isinstance(m, nn.Linear):
            nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
            if m.bias is not None:
                nn.init.zeros_(m.bias)

