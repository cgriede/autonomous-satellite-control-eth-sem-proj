"""Attitude safety / movement constraint constants (notebook 03)."""

from .UNIT_REGISTRY import UREG as ureg

# Off-nadir hard stop: safe mode must recover before exceeding this angle.
OFF_NADIR_HARD_LIMIT_DEG = 45.0 * ureg.deg

# Safe-mode recovery cruise rate (notebook 03).
SAFE_MODE_CRUISE_RATE_DEG_S = 0.05 * ureg.deg / ureg.s

# No external torque accepted after nadir recovery.
SAFE_MODE_LOCKOUT_S = 10.0 * ureg.s

# Nadir pointing tolerance before lockout timer starts.
NADIR_RECOVERY_TOLERANCE_DEG = 1.0 * ureg.deg

# Close enough to nadir to begin final stop.
SAFE_MODE_DECEL_START_DEG = 5.0 * ureg.deg

# |omega_sat| below this counts as "stopped" for safe-mode phases [rad/s].
SAFE_MODE_OMEGA_STOP = 0.1 * ureg.deg / ureg.s
