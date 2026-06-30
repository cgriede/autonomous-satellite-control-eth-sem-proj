"""Partition ControllerObservationLayout scalar keys for modular encoder arms."""

from __future__ import annotations

from dataclasses import dataclass

from autonomous_control.controller_observation import ControllerObservationLayout

PASSTHROUGH_KEYS: frozenset[str] = frozenset(
    {
        "body_z_angle_rad",
        "omega_sat_rad_s",
        "theta_orbit_rad",
        "primary_camera_image_quality",
        "capture_budget_remaining",
    }
)


@dataclass(frozen=True)
class ScalarGroupIndices:
    passthrough: tuple[int, ...]
    bearing: tuple[int, ...]
    mask: tuple[int, ...]

    @property
    def passthrough_dim(self) -> int:
        return len(self.passthrough)

    @property
    def bearing_dim(self) -> int:
        return len(self.bearing)

    @property
    def mask_dim(self) -> int:
        return len(self.mask)


def scalar_group_indices(layout: ControllerObservationLayout) -> ScalarGroupIndices:
    passthrough: list[int] = []
    bearing: list[int] = []
    mask: list[int] = []
    for i, key in enumerate(layout.scalar_keys):
        if key in PASSTHROUGH_KEYS:
            passthrough.append(i)
        elif key.startswith("target_bearing_error_rad_"):
            bearing.append(i)
        elif key.startswith("target_already_imaged_"):
            mask.append(i)
    return ScalarGroupIndices(
        passthrough=tuple(passthrough),
        bearing=tuple(bearing),
        mask=tuple(mask),
    )


def gather_columns(scalars: "torch.Tensor", indices: tuple[int, ...]) -> "torch.Tensor":
    import torch

    if not indices:
        return scalars.new_zeros((scalars.shape[0], 0))
    idx = torch.tensor(indices, device=scalars.device, dtype=torch.long)
    return scalars.index_select(dim=1, index=idx)
