import unittest

from environment_definition.constants.MISSION import (
    OBSERVATION_TARGET_AREAS,
    OBSERVATION_TARGET_STRIPE_END_LAT,
    OBSERVATION_TARGET_STRIPE_START_LAT,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.units.require_compatible_unit import require_compatible_units


class MissionConstantsTest(unittest.TestCase):
    def test_primary_area_has_expected_structure_and_units(self):
        self.assertGreaterEqual(len(OBSERVATION_TARGET_AREAS), 1)
        area = OBSERVATION_TARGET_AREAS[0]
        require_compatible_units(area.lat_min, "radian", "lat_min")
        require_compatible_units(area.lat_max, "radian", "lat_max")
        self.assertLess(float(area.lat_min.to(ureg.deg).magnitude), float(area.lat_max.to(ureg.deg).magnitude))
        self.assertNotEqual(str(area.label).strip(), "")
        require_compatible_units(OBSERVATION_TARGET_STRIPE_START_LAT, "radian", "STRIPE_START_LAT")
        require_compatible_units(OBSERVATION_TARGET_STRIPE_END_LAT, "radian", "STRIPE_END_LAT")


if __name__ == "__main__":
    unittest.main()
