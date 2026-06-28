"""Render-only target color mapping (camera strip + captured replay)."""

from __future__ import annotations

import unittest

import numpy as np

from environment_definition.constants import RENDER
from environment_definition.constants.observation_codes import observation_target_code_for_index
from render._satellite_cam_view import _rgba_for_observation_line_code
from simulation.capture_reward import captured_target_indices_at_step
from tests.test_capture_reward_series import _minimal_series


class RenderTargetColorsTest(unittest.TestCase):
    def test_all_target_observation_codes_map_to_red_when_pending(self) -> None:
        for idx in (0, 1, 7, 49):
            code = int(observation_target_code_for_index(idx))
            rgba = _rgba_for_observation_line_code(code)
            np.testing.assert_allclose(rgba[:3], RENDER.target_pending_cam_rgb, err_msg=f"T{idx}")

    def test_captured_target_is_purple_in_camera_strip(self) -> None:
        code = int(observation_target_code_for_index(4))
        rgba = _rgba_for_observation_line_code(code, captured_target_indices=frozenset({4}))
        np.testing.assert_allclose(rgba[:3], RENDER.target_captured_cam_rgb)

    def test_captured_target_indices_replay_from_cmd_steps(self) -> None:
        series = _minimal_series()
        self.assertEqual(
            captured_target_indices_at_step(series, 1, cmd_steps=(2,)),
            frozenset(),
        )
        self.assertEqual(
            captured_target_indices_at_step(series, 2, cmd_steps=(2,)),
            frozenset({0}),
        )


if __name__ == "__main__":
    unittest.main()
