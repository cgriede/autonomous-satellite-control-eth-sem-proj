import unittest

import numpy as np

from utils.flight_geometry.line_of_sight import subsatellite_latitude_deg_polar_meridian


class SubsatelliteLatPolarMeridianTest(unittest.TestCase):
    def test_pole_and_symmetric_offsets(self) -> None:
        theta_center = float(np.pi / 2)
        lat0 = subsatellite_latitude_deg_polar_meridian(theta_center, theta_center_rad=theta_center)
        self.assertAlmostEqual(lat0, 90.0, places=9)
        for delta_deg in (-23.0, 23.0):
            th = theta_center + np.deg2rad(delta_deg)
            lat = subsatellite_latitude_deg_polar_meridian(th, theta_center_rad=theta_center)
            self.assertAlmostEqual(lat, 90.0 - abs(delta_deg), places=5)

    def test_vectorized_matches_elementwise(self) -> None:
        theta_center = float(np.pi / 2)
        th = theta_center + np.deg2rad(np.array([-10.0, 0.0, 15.0], dtype=float))
        out = subsatellite_latitude_deg_polar_meridian(th, theta_center_rad=theta_center)
        exp = np.array(
            [subsatellite_latitude_deg_polar_meridian(float(x), theta_center_rad=theta_center) for x in th],
            dtype=float,
        )
        np.testing.assert_allclose(out, exp, rtol=0.0, atol=1e-9)


if __name__ == "__main__":
    unittest.main()
