import unittest

from environment_definition.constants.MISSION import (
    OBSERVATION_TARGET_AREAS,
    OBSERVATION_TARGET_STRIPE_END_LAT,
    OBSERVATION_TARGET_STRIPE_END_LON,
    OBSERVATION_TARGET_STRIPE_PLANE_Z_M,
    OBSERVATION_TARGET_STRIPE_START_LAT,
    OBSERVATION_TARGET_STRIPE_START_LON,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.units.require_compatible_unit import require_compatible_units


class MissionConstantsTest(unittest.TestCase):
    def test_primary_area_has_expected_structure_and_units(self):
        self.assertGreaterEqual(len(OBSERVATION_TARGET_AREAS), 1)
        area = OBSERVATION_TARGET_AREAS[0]
        require_compatible_units(area.lat_min, "radian", "lat_min")
        require_compatible_units(area.lat_max, "radian", "lat_max")
        require_compatible_units(area.lon_min, "radian", "lon_min")
        require_compatible_units(area.lon_max, "radian", "lon_max")
        require_compatible_units(area.legacy_orbital_angle, "radian", "legacy_orbital_angle")
        self.assertLess(float(area.lat_min.to(ureg.deg).magnitude), float(area.lat_max.to(ureg.deg).magnitude))
        self.assertNotEqual(str(area.label).strip(), "")
        require_compatible_units(OBSERVATION_TARGET_STRIPE_PLANE_Z_M, "meter", "STRIPE_PLANE_Z")
        require_compatible_units(OBSERVATION_TARGET_STRIPE_START_LAT, "radian", "STRIPE_START_LAT")
        require_compatible_units(OBSERVATION_TARGET_STRIPE_START_LON, "radian", "STRIPE_START_LON")
        require_compatible_units(OBSERVATION_TARGET_STRIPE_END_LAT, "radian", "STRIPE_END_LAT")
        require_compatible_units(OBSERVATION_TARGET_STRIPE_END_LON, "radian", "STRIPE_END_LON")


if __name__ == "__main__":
    unittest.main()
