from dataclasses import dataclass
from math import pi

from pint import Quantity

from backend.utils.units.require_compatible_unit import require_compatible_units

@dataclass(frozen=True)
class AttitudeState2D:
    theta: object
    omega_sat: object
    omega_wheel: object

def wrap_angle_to_pi(theta: object) -> object:
    """Wrap an angle quantity to [-pi, pi] radians."""
    require_compatible_units(theta, "radian", "theta")
    theta_rad_mag = theta.to("radian").magnitude
    wrapped_rad_mag = ((theta_rad_mag + pi) % (2.0 * pi)) - pi
    return wrapped_rad_mag * theta._REGISTRY.radian


def propagate_reaction_wheel_attitude_2d(
    *,
    state: AttitudeState2D,
    wheel_torque: object,
    sat_inertia: object,
    wheel_inertia: object,
    dt: object,
) -> AttitudeState2D:
    """Propagate one 2D attitude step from a wheel torque command."""
    require_compatible_units(state.theta, "radian", "state.theta")
    require_compatible_units(state.omega_sat, "radian/second", "state.omega_sat")
    require_compatible_units(state.omega_wheel, "radian/second", "state.omega_wheel")
    require_compatible_units(wheel_torque, "newton*meter", "wheel_torque")
    require_compatible_units(sat_inertia, "kilogram*meter**2", "sat_inertia")
    require_compatible_units(wheel_inertia, "kilogram*meter**2", "wheel_inertia")
    require_compatible_units(dt, "second", "dt")

    if sat_inertia.to("kilogram*meter**2").magnitude <= 0.0:
        raise ValueError("sat_inertia must be > 0.")
    if wheel_inertia.to("kilogram*meter**2").magnitude <= 0.0:
        raise ValueError("wheel_inertia must be > 0.")
    if dt.to("second").magnitude <= 0.0:
        raise ValueError("dt must be > 0.")

    alpha_sat = -wheel_torque / sat_inertia
    alpha_wheel = wheel_torque / wheel_inertia

    omega_sat = state.omega_sat + alpha_sat * dt
    omega_wheel = state.omega_wheel + alpha_wheel * dt
    theta = wrap_angle_to_pi(state.theta + omega_sat * dt)

    return AttitudeState2D(
        theta=theta.to("radian"),
        omega_sat=omega_sat.to("radian/second"),
        omega_wheel=omega_wheel.to("radian/second"),
    )
