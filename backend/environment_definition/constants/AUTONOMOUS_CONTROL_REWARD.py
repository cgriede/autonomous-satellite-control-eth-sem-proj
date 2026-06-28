"""
Constants for autonomous-control reward v1 (distance-band + project deltas).

Distance quantities are ground-range / slant-range proxies in kilometers unless
callers convert; keep consistent with reward helpers (Pint).
"""

from .SATELLITE import MAX_PRIMARY_CAPTURES_PER_ORBIT
from .UNIT_REGISTRY import UREG as ureg

# Outer gate: beyond this distance to target, reward is 0 (no distance-band penalty, no energy term).
CAMERA_VIEWING_DISTANCE_THRESHOLD = 2500.0 * ureg.km

# Distance-band v1: optimal (nadir reference) and resolution outer bound — must satisfy d_th > d_op.
OPTIMAL_GROUND_RANGE = 400.0 * ureg.km
RESOLUTION_GROUND_RANGE_THRESHOLD = 1500.0 * ureg.km

# r_total includes -k_E * E [J]; k_E chosen so typical wheel-step energies do not dwarf ±100.
REWARD_ENERGY_LINEAR_COEFFICIENT = 10.0

# Positive reward scales for geodetic area-target mapping.
REWARD_AREA_INTERSECTION_WEIGHT = 100.0
REWARD_AREA_NOVELTY_WEIGHT = 25.0

# Take-picture mode: alias of SATELLITE.MAX_PRIMARY_CAPTURES_PER_ORBIT (reward / env code).
MAX_PICTURES_PER_EPISODE = MAX_PRIMARY_CAPTURES_PER_ORBIT

# Positive scale for image-quality capture reward: k * quality * (1 - cloud_frac).
REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT = 100.0

# Penalty when shutter fires but applied capture credit is ~0 (repeat target, no FOV, etc.).
REWARD_SHUTTER_WASTE_PENALTY = 5.0

# Per-step penalty on normalized commanded torque squared: -k * (tau/tau_max)^2.
REWARD_TORQUE_EFFORT_COEFFICIENT = 0.1
