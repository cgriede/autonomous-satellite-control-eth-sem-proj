import unittest

from environment_definition.constants.SATELLITE import (
    FOCAL_LENGTH,
    N_PIXELS_X,
    N_PIXELS_Y,
    PIXEL_SIZE,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.camera_image import CameraImage


class CameraImageTest(unittest.TestCase):
    def test_from_hardware_gsd_at_500_km_matches_design(self):
        camera = CameraImage.from_hardware(
            focal_length=FOCAL_LENGTH,
            pixel_size=PIXEL_SIZE,
            n_pixels_x=N_PIXELS_X,
            n_pixels_y=N_PIXELS_Y,
        )
        altitude = 500 * ureg.km
        gsd = camera.gsd_at(altitude)
        expected = (PIXEL_SIZE * altitude / FOCAL_LENGTH).to(ureg.m)
        self.assertAlmostEqual(gsd.to(ureg.m).magnitude, expected.to(ureg.m).magnitude, places=12)
        self.assertAlmostEqual(gsd.to(ureg.m).magnitude, 1.5, places=2)

    def test_from_fov_gopro_case_recover_fov_y(self):
        camera = CameraImage.from_fov(
            fov_y=70 * ureg.deg,
            pixel_size=1.55 * ureg.um,
            n_pixels_x=5312,
            n_pixels_y=2988,
        )
        self.assertGreater(camera.focal_length.to(ureg.mm).magnitude, 0.0)
        self.assertAlmostEqual(camera.fov(axis="y").to(ureg.deg).magnitude, 70.0, places=6)

    def test_gsd_at_and_swath_at_return_metres(self):
        camera = CameraImage.from_fov(
            fov_y=70 * ureg.deg,
            pixel_size=1.55 * ureg.um,
            n_pixels_x=5312,
            n_pixels_y=2988,
        )
        altitude = 500 * ureg.km
        gsd = camera.gsd_at(altitude)
        swath_y = camera.swath_at(altitude, axis="y")
        self.assertAlmostEqual(gsd.to(ureg.m).magnitude, gsd.magnitude)
        self.assertAlmostEqual(swath_y.to(ureg.m).magnitude, swath_y.magnitude)
        self.assertAlmostEqual(
            swath_y.to(ureg.m).magnitude,
            (camera.n_pixels_y * gsd.to(ureg.m).magnitude),
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
