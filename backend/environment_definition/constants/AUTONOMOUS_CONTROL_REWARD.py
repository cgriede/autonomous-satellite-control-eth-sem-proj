"""
Constants for autonomous-control reward v1 (distance-band + project deltas).

Distance quantities are ground-range / slant-range proxies in kilometers unless
callers convert; keep consistent with reward helpers (Pint).
"""

from .UNIT_REGISTRY import UREG as ureg

# Outer gate: beyond this distance to target, reward is 0 (no distance-band penalty, no energy term).
CAMERA_VIEWING_DISTANCE_THRESHOLD = 2500.0 * ureg.km

# Distance-band v1: optimal (nadir reference) and resolution outer bound — must satisfy d_th > d_op.
OPTIMAL_GROUND_RANGE = 400.0 * ureg.km
RESOLUTION_GROUND_RANGE_THRESHOLD = 1500.0 * ureg.km

# r_total includes -k_E * E [J]; k_E chosen so typical wheel-step energies do not dwarf ±100.
REWARD_ENERGY_LINEAR_COEFFICIENT = 0
