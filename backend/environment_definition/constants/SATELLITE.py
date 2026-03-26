from .UNIT_REGISTRY import UREG as ureg

# Mission-level constants from project discussions.
SATELLITE_MASS                 = 250.0* ureg.kg
STAR_TRACKER_MAX_MANEUVER_RATE = 3.0* ureg.deg/ureg.s

#some generic rocket lab reaction wheel torque and momentum values
REACTION_WHEEL_MAX_TORQUE   = 0.1 * ureg.N* ureg.m
REACTION_WHEEL_MAX_MOMENTUM = 0.4 * ureg.N * ureg.m * ureg.s

# Camera specs (source of truth for optics)
#
# Required by design:
# - Sensor resolution: 9344 (cross-track) x 7000 (along-track)
# - Pixel size: 3.2 µm
# - Focal length: 1067 mm
# - Nominal altitude: 500 km (mission reference; GSD/swath are computed vs. actual altitude in simulation)
CAMERA_ALTITUDE = 500 * ureg.km

N_PIXELS_X = 9344
N_PIXELS_Y = 7000

PIXEL_SIZE = 3.2 * ureg.um  # pixel pitch
FOCAL_LENGTH = 1067 * ureg.mm

# Physical sensor dimensions (rectangle in the focal plane)
SENSOR_WIDTH = (N_PIXELS_X * PIXEL_SIZE).to(ureg.m)  # cross-track dimension
SENSOR_HEIGHT = (N_PIXELS_Y * PIXEL_SIZE).to(ureg.m)  # along-track dimension

#3d moment of inertia
Ixx = 16.6 * ureg.kg* ureg.m**2
Iyy = 21.7 * ureg.kg* ureg.m**2
Izz = 31.2 * ureg.kg* ureg.m**2 

#2d simplified case
MOMENT_OF_INERTIA_2D        = Izz