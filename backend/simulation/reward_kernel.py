from __future__ import annotations

from typing import Any

import numpy as np

from autonomous_control.reward import RewardConfig, RewardSignals, compute_reward
from environment_definition.constants.MISSION import OBSERVATION_TARGET_AREAS
from simulation.capture_target import (
    dominant_capture_target_index,
    primary_target_pixel_coverage,
    target_visible_from_codes,
)
from simulation.episode_capture import ShutterRewardOverride
from utils.geodesics.geodesic_helpers import geodesic_distance
from utils.geometry.mission_stripe_disk import _area_endpoint_geodetic_deg
from utils.geometry.orbit_disk_polar_meridian import (
    geodetic_deg_from_track_offset_deg,
    track_offset_deg_from_latitude_only_deg,
)


class RewardKernel:
    @staticmethod
    def evaluate(
        *,
        sat_pos_xy_km: np.ndarray,
        sat_subpoint_lat_deg: float,
        sat_subpoint_lon_deg: float,
        target_area_intersection_ratio: float,
        target_area_novelty_ratio: float,
        camera_observation_line_codes: np.ndarray,
        camera_cloud_blocked_fraction: float = 0.0,
        secondary_camera_cloud_blocked_fraction: float = 0.0,
        wheel_inertia: Any,
        omega_before: Any,
        omega_after: Any,
        reward_config: RewardConfig,
        ureg: Any,
        target_area: Any | None = None,
        target_areas: tuple | None = None,
        camera_image_quality: float = float("nan"),
        shutter_override: ShutterRewardOverride | None = None,
    ) -> float:
        _ = sat_pos_xy_km

        codes = np.asarray(camera_observation_line_codes, dtype=np.int8)
        target_visible = target_visible_from_codes(codes)
        dominant = dominant_capture_target_index(codes)
        frame_coverage = primary_target_pixel_coverage(codes, target_index=dominant)
        frame_quality = float(camera_image_quality)
        if not np.isfinite(frame_quality):
            frame_quality = 0.0
        frame_cloud = float(np.clip(camera_cloud_blocked_fraction, 0.0, 1.0))

        areas = tuple(target_areas) if target_areas is not None else OBSERVATION_TARGET_AREAS

        if target_area is not None and target_area not in areas:
            areas = (target_area,) + areas

        distances_km: list[float] = []

        for area in areas:
            lat_a, _lon_a = _area_endpoint_geodetic_deg(area, which="min")
            lat_b, _lon_b = _area_endpoint_geodetic_deg(area, which="max")
            off_mid = 0.5 * (
                track_offset_deg_from_latitude_only_deg(lat_a)
                + track_offset_deg_from_latitude_only_deg(lat_b)
            )
            target_lat_deg, target_lon_deg = geodetic_deg_from_track_offset_deg(off_mid)
            d_q = geodesic_distance(
                sat_subpoint_lon_deg * ureg.deg,
                sat_subpoint_lat_deg * ureg.deg,
                target_lon_deg * ureg.deg,
                target_lat_deg * ureg.deg,
            )
            distances_km.append(float(d_q.to(ureg.km).magnitude))

        distance_to_target = min(distances_km) * ureg.km

        if shutter_override is not None:
            picture_taken = shutter_override.picture_taken
            capture_target_novel = shutter_override.capture_target_novel
            quality = shutter_override.camera_image_quality
            coverage = shutter_override.primary_target_pixel_coverage
            cloud_frac = shutter_override.camera_cloud_blocked_fraction
            target_visible = shutter_override.target_visible
        elif reward_config.enable_image_quality_capture:
            picture_taken = False
            capture_target_novel = False
            quality = frame_quality
            coverage = frame_coverage
            cloud_frac = frame_cloud
        else:
            picture_taken = target_visible
            capture_target_novel = True
            quality = frame_quality
            coverage = frame_coverage
            cloud_frac = frame_cloud

        signals = RewardSignals(
            distance_to_target=distance_to_target,
            picture_taken=picture_taken,
            capture_target_novel=capture_target_novel,
            target_visible=target_visible,
            camera_image_quality=quality,
            primary_target_pixel_coverage=coverage,
            target_area_intersection_ratio=float(target_area_intersection_ratio),
            target_area_novelty_ratio=float(target_area_novelty_ratio),
            camera_cloud_blocked_fraction=cloud_frac,
            secondary_camera_cloud_blocked_fraction=float(secondary_camera_cloud_blocked_fraction),
            wheel_inertia=wheel_inertia,
            omega_before=omega_before,
            omega_after=omega_after,
        )

        reward_total, _ = compute_reward(signals=signals, cfg=reward_config)
        return float(reward_total)
