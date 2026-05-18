"""Pinhole camera imaging spec: optics + pixel grid (not a captured frame)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from environment_definition.constants.SATELLITE import (
    FOCAL_LENGTH,
    N_PIXELS_X,
    N_PIXELS_Y,
    PIXEL_SIZE,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.camera_optics import nadir_ground_sample_distance, pinhole_full_fov_rad


@dataclass(frozen=True)
class CameraImage:
    focal_length: Any
    pixel_size: Any
    n_pixels_x: int
    n_pixels_y: int

    def sensor_width(self) -> Any:
        return (self.n_pixels_x * self.pixel_size).to(ureg.m)

    def sensor_height(self) -> Any:
        return (self.n_pixels_y * self.pixel_size).to(ureg.m)

    def _sensor_dim(self, *, axis: Literal["x", "y"]) -> Any:
        if axis == "x":
            return self.sensor_width()
        if axis == "y":
            return self.sensor_height()
        raise ValueError(f"axis must be 'x' or 'y', got {axis!r}.")

    def fov(self, *, axis: Literal["x", "y"]) -> Any:
        return pinhole_full_fov_rad(sensor_dim=self._sensor_dim(axis=axis), focal_length=self.focal_length)

    def gsd_at(self, altitude: Any) -> Any:
        return nadir_ground_sample_distance(
            pixel_size=self.pixel_size,
            altitude=altitude,
            focal_length=self.focal_length,
        )

    def swath_at(self, altitude: Any, *, axis: Literal["x", "y"]) -> Any:
        n_pixels = self.n_pixels_x if axis == "x" else self.n_pixels_y
        return (n_pixels * self.gsd_at(altitude)).to(ureg.m)

    @classmethod
    def from_hardware(
        cls,
        *,
        focal_length: Any,
        pixel_size: Any,
        n_pixels_x: int,
        n_pixels_y: int,
    ) -> CameraImage:
        return cls(
            focal_length=focal_length,
            pixel_size=pixel_size,
            n_pixels_x=int(n_pixels_x),
            n_pixels_y=int(n_pixels_y),
        )

    @classmethod
    def from_fov(
        cls,
        *,
        fov_y: Any,
        pixel_size: Any,
        n_pixels_x: int,
        n_pixels_y: int,
        axis: Literal["x", "y"] = "y",
    ) -> CameraImage:
        n_x = int(n_pixels_x)
        n_y = int(n_pixels_y)
        sensor_dim = (n_y if axis == "y" else n_x) * pixel_size
        half_fov_rad = 0.5 * fov_y.to(ureg.rad).magnitude
        tan_half = float(np.tan(half_fov_rad))
        if tan_half <= 0.0:
            raise ValueError("fov_y must be positive and less than 180 deg.")
        focal_length = (sensor_dim / (2.0 * tan_half)).to(ureg.m)
        return cls(
            focal_length=focal_length,
            pixel_size=pixel_size,
            n_pixels_x=n_x,
            n_pixels_y=n_y,
        )


@dataclass(frozen=True)
class CameraMount:
    camera: CameraImage
    tilt_off_nadir: Any


DEFAULT_NADIR_CAMERA = CameraImage.from_hardware(
    focal_length=FOCAL_LENGTH,
    pixel_size=PIXEL_SIZE,
    n_pixels_x=N_PIXELS_X,
    n_pixels_y=N_PIXELS_Y,
)
