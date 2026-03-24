import unittest

from environment_definition.constants.SIMULATION import FieldOfViewCone, SIMULATION
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg


class FieldOfViewConeRegressionTest(unittest.TestCase):
    def test_fov_cone_init_only_requires_opening_angle(self):
        cone = FieldOfViewCone(opening_angle=0.2 * ureg.deg)
        self.assertAlmostEqual(cone.opening_angle.to(ureg.deg).magnitude, 0.2)

    def test_simulation_exposes_fov_cone(self):
        self.assertTrue(hasattr(SIMULATION, "field_of_view_cone"))
        self.assertAlmostEqual(
            SIMULATION.field_of_view_cone.opening_angle.to(ureg.deg).magnitude,
            0.1,
        )


if __name__ == "__main__":
    unittest.main()
