"""Vectorized target-area classification from geodetic points."""

from __future__ import annotations

import unittest

import numpy as np

from environment_definition.constants.MISSION import OBSERVATION_TARGET_AREAS
from utils.geometry.mission_stripe_disk import (
    batch_geodetic_target_area_indices,
    target_areas_track_offset_ranges_deg,
)


class BatchGeodeticTargetAreaIndicesTest(unittest.TestCase):
    def test_empty_input_returns_empty(self) -> None:
        out = batch_geodetic_target_area_indices(
            np.array([], dtype=float),
            np.array([], dtype=float),
            (),
        )
        self.assertEqual(out.shape, (0,))

    def test_batch_matches_scalar_ranges(self) -> None:
        ranges = target_areas_track_offset_ranges_deg(OBSERVATION_TARGET_AREAS)
        lon = np.array([0.0, 0.0], dtype=float)
        lat = np.array([89.8, 45.0], dtype=float)
        indices = batch_geodetic_target_area_indices(lon, lat, ranges)
        self.assertEqual(indices.shape, (2,))
        self.assertEqual(int(indices[0]), 0)
        self.assertEqual(int(indices[1]), -1)


if __name__ == "__main__":
    unittest.main()
