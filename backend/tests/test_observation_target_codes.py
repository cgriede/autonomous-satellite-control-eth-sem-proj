"""Indexed target observation codes (T0, T1, …) and capture novelty."""

from __future__ import annotations

import unittest

import numpy as np

from environment_definition.constants.SIMULATION import OBSERVATION_TARGET
from environment_definition.constants.observation_codes import (
    observation_code_to_ascii,
    observation_target_ascii_label,
    observation_target_code_for_index,
    target_index_from_observation_code,
)
from simulation.camera_2d import observation_codes_to_ascii_line
from simulation.capture_target import dominant_capture_target_index, primary_target_pixel_coverage
from utils.geometry.mission_stripe_disk import geodetic_target_area_index


class ObservationTargetCodesTest(unittest.TestCase):
    def test_t0_alias(self) -> None:
        self.assertEqual(int(observation_target_code_for_index(0)), int(OBSERVATION_TARGET))

    def test_index_round_trip(self) -> None:
        for idx in (0, 1, 5):
            code = int(observation_target_code_for_index(idx))
            self.assertEqual(target_index_from_observation_code(code), idx)

    def test_ascii_t0_t1(self) -> None:
        self.assertEqual(observation_code_to_ascii(int(OBSERVATION_TARGET)), "0")
        self.assertEqual(observation_code_to_ascii(int(observation_target_code_for_index(1))), "1")
        self.assertEqual(observation_target_ascii_label(int(OBSERVATION_TARGET)), "T0")

    def test_ascii_line_mixed_targets(self) -> None:
        codes = np.array([1, 3, 4], dtype=np.int8)
        self.assertEqual(observation_codes_to_ascii_line(codes), "E01")

    def test_dominant_target_index(self) -> None:
        codes = np.array([3, 3, 4, 1], dtype=np.int8)
        self.assertEqual(dominant_capture_target_index(codes), 0)
        self.assertAlmostEqual(
            primary_target_pixel_coverage(codes, target_index=0),
            0.5,
        )


if __name__ == "__main__":
    unittest.main()
