"""Tests for pole-crossing meridian target grid placement."""

import unittest

import numpy as np

from environment_definition.constants.EARTH import EARTH_RADIUS
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.geometry.polar_meridian_track import (
    build_target_grid_polar_meridian,
    lat_deg_from_track_offset_deg,
    track_offset_deg_from_anchor_lat_deg,
)


class PolarMeridianTrackTest(unittest.TestCase):
    def test_lat_from_offset_matches_anchor_convention(self) -> None:
        self.assertAlmostEqual(lat_deg_from_track_offset_deg(-5.0), 85.0, places=9)
        self.assertAlmostEqual(lat_deg_from_track_offset_deg(0.0), 90.0, places=9)
        self.assertAlmostEqual(lat_deg_from_track_offset_deg(3.0), 87.0, places=9)

    def test_track_offsets_increase_monotonically_past_pole(self) -> None:
        segments = build_target_grid_polar_meridian(
            anchor_lat=85.0 * ureg.deg,
            n_targets=50,
            target_size=15.0 * ureg.km,
            spacing=40.0 * ureg.km,
        )
        offsets = [s.track_offset_lo_deg for s in segments] + [segments[-1].track_offset_hi_deg]
        self.assertTrue(all(b > a for a, b in zip(offsets[:-1], offsets[1:])))

    def test_phi_bounds_increase_monotonically(self) -> None:
        segments = build_target_grid_polar_meridian(
            anchor_lat=85.0 * ureg.deg,
            n_targets=50,
            target_size=15.0 * ureg.km,
            spacing=40.0 * ureg.km,
        )
        phi_endpoints: list[float] = []
        for seg in segments:
            phi_lo, phi_hi = seg.phi_bounds_deg()
            phi_endpoints.extend([phi_lo, phi_hi])
        self.assertTrue(all(b >= a for a, b in zip(phi_endpoints[:-1], phi_endpoints[1:])))

    def test_band_and_gap_lengths_near_pole(self) -> None:
        segments = build_target_grid_polar_meridian(
            anchor_lat=89.0 * ureg.deg,
            n_targets=8,
            target_size=15.0 * ureg.km,
            spacing=40.0 * ureg.km,
        )
        r_m = float(EARTH_RADIUS.to(ureg.m).magnitude)
        target_step_deg = float(np.rad2deg(15_000.0 / r_m))
        spacing_step_deg = float(np.rad2deg(40_000.0 / r_m))
        for seg in segments:
            span_deg = seg.track_offset_hi_deg - seg.track_offset_lo_deg
            self.assertAlmostEqual(span_deg, target_step_deg, places=5)
        for left, right in zip(segments[:-1], segments[1:]):
            gap_deg = right.track_offset_lo_deg - left.track_offset_hi_deg
            self.assertAlmostEqual(gap_deg, spacing_step_deg, places=5)

    def test_anchor_offset_from_lat(self) -> None:
        self.assertAlmostEqual(track_offset_deg_from_anchor_lat_deg(85.0), -5.0, places=9)


if __name__ == "__main__":
    unittest.main()
