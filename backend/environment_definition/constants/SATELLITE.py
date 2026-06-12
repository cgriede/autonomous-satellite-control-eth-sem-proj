from .UNIT_REGISTRY import UREG as ureg

#####################################
SATELLITE_MASS                 = 250.0* ureg.kg
STAR_TRACKER_MAX_MANEUVER_RATE = 3.0* ureg.deg/ureg.s

#some generic rocket lab reaction wheel torque and momentum values
REACTION_WHEEL_MAX_TORQUE   = 0.1 * ureg.N* ureg.m
REACTION_WHEEL_MAX_MOMENTUM = 0.4 * ureg.N * ureg.m * ureg.s

#3d moment of inertia
Ixx = 16.6 * ureg.kg* ureg.m**2
Iyy = 21.7 * ureg.kg* ureg.m**2
Izz = 31.2 * ureg.kg* ureg.m**2 

#2d simplified case
MOMENT_OF_INERTIA_2D        = Izz
#####################################
# Camera specs (source of truth for optics)
#
# Required by design:
# - Sensor resolution: 9344 (cross-track) x 7000 (along-track)
# - Pixel size: 3.2 µm
# - Focal length: 1067 mm
# - Nominal altitude: 500 km (mission reference; GSD/swath are computed vs. actual altitude in simulation)
CAMERA_ALTITUDE = 550 * ureg.km

N_PIXELS_X = 9344
N_PIXELS_Y = 7000

PIXEL_SIZE = 3.2 * ureg.um  # pixel pitch
FOCAL_LENGTH = 1067 * ureg.mm

CAMERA_EXPOSURE_TIME = 100 * ureg.microsecond  # for GSD-based motion blur estimation

# Arbitrary OBC limit: max primary-camera shutter events per orbit (memory + downlink budget).
# One simulation episode ≈ one orbit pass. Source of truth for take-picture mode.
MAX_PRIMARY_CAPTURES_PER_ORBIT = 10

# Ground blur [m] during exposure at which normalized quality = 0.5 (quality = ref / (blur + ref)).
# Calibrated ~0.3 quality at nominal nadir orbit ground-track (~0.7 m blur over 100 µs).
IMAGE_QUALITY_SMEAR_REFERENCE_M = 0.30 * ureg.m

# Legacy px reference (smear_px = blur_m / GSD); kept for docs / equivalence at ~1.65 m GSD.
IMAGE_QUALITY_SMEAR_REFERENCE_PX = 1.0

# Physical sensor dimensions (rectangle in the focal plane)
SENSOR_WIDTH = N_PIXELS_X * PIXEL_SIZE  # cross-track dimension
SENSOR_HEIGHT = N_PIXELS_Y * PIXEL_SIZE # along-track dimension

####################################