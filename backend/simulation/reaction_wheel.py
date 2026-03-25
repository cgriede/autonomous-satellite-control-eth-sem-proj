from __future__ import annotations

from dataclasses import dataclass

from pint import Quantity

from .attitude_dynamics import AttitudeState2D
from utils.units.require_compatible_unit import require_compatible_units

@dataclass(frozen=True)
class ReactionWheel:
    """
    Reaction wheel "control/safety" model.

    Given:
    - current attitude state
    - commanded wheel torque (direct input)

    This model outputs an *applied* wheel torque that respects a safety cutoff:
    if the satellite angular rate magnitude exceeds `max_manouver_rate`,
    only torques that oppose the current rotation are allowed; other directions
    are blocked (applied torque becomes 0) for the next dynamics step.
    """

    wheel_inertia: Quantity
    max_manouver_rate: Quantity

    def __post_init__(self) -> None:
        # Unit checks are important because dynamics relies on consistent pint quantities.
        require_compatible_units(self.wheel_inertia, "kilogram*meter**2", "wheel_inertia")
        require_compatible_units(
            self.max_manouver_rate,
            "radian/second",
            "max_manouver_rate",
        )

    def compute_applied_torque(self, *, state: AttitudeState2D, tau_cmd: Quantity) -> Quantity:
        """
        Compute applied wheel torque for one dynamics step.

        Safety cutoff rule (based on your requested sign convention):
        - If `abs(omega_sat) > max_manouver_rate`, then torque commands that would
          increase the magnitude of `omega_sat` are blocked (returned torque = 0).
        - With current dynamics `alpha_sat = -wheel_torque / sat_inertia`, torque
          that opposes `omega_sat` has the same sign as `omega_sat`.
        """

        require_compatible_units(state.omega_sat, "radian/second", "state.omega_sat")
        require_compatible_units(tau_cmd, "newton*meter", "tau_cmd")

        omega_sat = state.omega_sat.to("radian/second").magnitude
        omega_limit = self.max_manouver_rate.to("radian/second").magnitude
        tau_cmd_nm = tau_cmd.to("newton*meter").magnitude

        # No cutoff active if we're still within safe angular rate magnitude.
        if abs(omega_sat) <= omega_limit:
            return tau_cmd

        # If cutoff is active, allow only torques with the same sign as omega_sat.
        # Opposite-sign command would increase |omega_sat| (i.e., worsen the violation).
        if omega_sat * tau_cmd_nm < 0.0:
            return 0.0 * tau_cmd
        return tau_cmd

