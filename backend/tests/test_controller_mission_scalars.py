"""Mission scalar observations: budget + per-target bearing errors [rad]."""

from __future__ import annotations

import unittest

import numpy as np

from autonomous_control.controller_observation import (
    ControllerEpisodeContext,
    build_controller_observation_from_timestep,
    compute_target_bearing_errors_rad,
    controller_observation_layout,
    mission_scalar_values_from_context,
    resolve_target_anchor_xy_km,
)
from s01_utils.baseline_overflight import (
    BASELINE_N_TARGETS,
    build_baseline_target_areas,
)
from autonomous_control.feature_selection import ControllerFeatureConfig
from autonomous_control.training_preflight import _minimal_timestep
from simulation.attitude_controller import target_boresight_angle_rad


class ControllerMissionScalarsTest(unittest.TestCase):
    def test_resolve_target_anchor_xy_km_one_row_per_target_area(self) -> None:
        areas = build_baseline_target_areas(n_targets=BASELINE_N_TARGETS)
        anchors = resolve_target_anchor_xy_km(areas, earth_radius_km=6371.0)
        self.assertEqual(anchors.shape, (BASELINE_N_TARGETS, 2))

    def test_bearing_error_zero_when_aligned(self) -> None:
        sat = np.array([7000.0, 0.0], dtype=float)
        anchor = np.array([6371.0, 0.0], dtype=float)
        body_z = target_boresight_angle_rad(sat, anchor)
        errors = compute_target_bearing_errors_rad(
            sat_pos_xy_km=sat,
            body_z_angle_rad=body_z,
            target_anchor_xy_km=anchor.reshape(1, 2),
        )
        self.assertEqual(errors.shape, (1,))
        self.assertAlmostEqual(float(errors[0]), 0.0, places=6)

    def test_bearing_error_sign_follows_offset(self) -> None:
        sat = np.array([7000.0, 0.0], dtype=float)
        anchor = np.array([6371.0, 0.0], dtype=float)
        body_z = target_boresight_angle_rad(sat, anchor) + 0.2
        errors = compute_target_bearing_errors_rad(
            sat_pos_xy_km=sat,
            body_z_angle_rad=body_z,
            target_anchor_xy_km=anchor.reshape(1, 2),
        )
        self.assertLess(float(errors[0]), 0.0)
        errors_pos = compute_target_bearing_errors_rad(
            sat_pos_xy_km=sat,
            body_z_angle_rad=body_z - 0.4,
            target_anchor_xy_km=anchor.reshape(1, 2),
        )
        self.assertGreater(float(errors_pos[0]), 0.0)

    def test_s01_scalar_count_includes_mission_features(self) -> None:
        n_targets = 3
        feature_config = ControllerFeatureConfig(
            include_capture_budget=True,
            include_captured_target_mask=True,
            include_target_bearing_errors=True,
        )
        layout = controller_observation_layout(
            feature_config=feature_config,
            n_mission_targets=n_targets,
        )
        expected = 3 + 1 + n_targets + n_targets  # attitude + orbit + budget + mask + bearings
        self.assertEqual(layout.scalar_dim, expected)

    def test_captured_target_mask_in_observation(self) -> None:
        ts = _minimal_timestep()
        n_targets = 3
        anchors = np.array(
            [[6371.0, 0.0], [6371.0, 100.0], [6371.0, 200.0]],
            dtype=float,
        )
        feature_config = ControllerFeatureConfig(
            include_capture_budget=True,
            include_captured_target_mask=True,
        )
        layout = controller_observation_layout(
            feature_config=feature_config,
            n_mission_targets=n_targets,
        )
        context_empty = ControllerEpisodeContext(
            capture_budget_remaining=10.0,
            target_anchor_xy_km=anchors,
            captured_target_indices=frozenset(),
        )
        obs_empty = build_controller_observation_from_timestep(
            timestep=ts,
            feature_config=feature_config,
            layout=layout,
            episode_context=context_empty,
        )
        context_captured = ControllerEpisodeContext(
            capture_budget_remaining=9.0,
            target_anchor_xy_km=anchors,
            captured_target_indices=frozenset({0, 2}),
        )
        obs_captured = build_controller_observation_from_timestep(
            timestep=ts,
            feature_config=feature_config,
            layout=layout,
            episode_context=context_captured,
        )
        idx0 = layout.scalar_keys.index("target_already_imaged_0")
        idx1 = layout.scalar_keys.index("target_already_imaged_1")
        idx2 = layout.scalar_keys.index("target_already_imaged_2")
        budget_idx = layout.scalar_keys.index("capture_budget_remaining")
        self.assertAlmostEqual(float(obs_empty.scalars[budget_idx]), 10.0)
        self.assertAlmostEqual(float(obs_captured.scalars[budget_idx]), 9.0)
        self.assertAlmostEqual(float(obs_empty.scalars[idx0]), 0.0)
        self.assertAlmostEqual(float(obs_captured.scalars[idx0]), 1.0)
        self.assertAlmostEqual(float(obs_captured.scalars[idx1]), 0.0)
        self.assertAlmostEqual(float(obs_captured.scalars[idx2]), 1.0)

    def test_build_observation_requires_context_when_mission_enabled(self) -> None:
        ts = _minimal_timestep()
        feature_config = ControllerFeatureConfig(include_capture_budget=True)
        with self.assertRaises(ValueError):
            build_controller_observation_from_timestep(
                timestep=ts,
                feature_config=feature_config,
                n_mission_targets=0,
            )

    def test_mission_scalar_values_in_observation(self) -> None:
        ts = _minimal_timestep()
        n_targets = 2
        anchors = np.array([[6371.0, 0.0], [6371.0, 100.0]], dtype=float)
        feature_config = ControllerFeatureConfig(
            include_capture_budget=True,
            include_target_bearing_errors=True,
        )
        layout = controller_observation_layout(
            feature_config=feature_config,
            n_mission_targets=n_targets,
        )
        context = ControllerEpisodeContext(
            capture_budget_remaining=7.0,
            target_anchor_xy_km=anchors,
        )
        mission_values = mission_scalar_values_from_context(
            timestep=ts,
            episode_context=context,
            feature_config=feature_config,
        )
        self.assertEqual(mission_values["capture_budget_remaining"], 7.0)
        self.assertEqual(len([k for k in mission_values if k.startswith("target_bearing")]), 2)

        obs = build_controller_observation_from_timestep(
            timestep=ts,
            feature_config=feature_config,
            layout=layout,
            episode_context=context,
        )
        self.assertEqual(obs.scalars.shape[0], layout.scalar_dim)
        budget_idx = layout.scalar_keys.index("capture_budget_remaining")
        self.assertAlmostEqual(float(obs.scalars[budget_idx]), 7.0)


if __name__ == "__main__":
    unittest.main()
