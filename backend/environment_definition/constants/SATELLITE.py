from .UNIT_REGISTRY import UREG as ureg

# Mission-level constants from project discussions.
SATELLITE_MASS                 = 250.0* ureg.kg
STAR_TRACKER_MAX_MANEUVER_RATE = 3.0* ureg.deg/ureg.s

# TODO: verify / update these values
#rough aproximation for major axis (across solar wings axis / worst case)
MOMENT_OF_INERTIA_2D        = 252* ureg.kg* ureg.m**2
#some generic rocket lab reaction wheel torque and momentum values
REACTION_WHEEL_MAX_TORQUE   = 0.4* ureg.N* ureg.m
REACTION_WHEEL_MAX_MOMENTUM = 5* ureg.N * ureg.m * ureg.s
