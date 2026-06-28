import unittest

import numpy as np

from environment_definition.constants import (
    EARTH_GRAVITATIONAL_PARAMETER,
    EARTH_RADIUS,
    RenderMode,
    SIMULATION,
    SimulationConfig,
    UREG as ureg,
)
from environment_definition.constants.MISSION import los_theta_offsets_deg
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE, SATELLITE_ALTITUDE
from simulation.stepper import SimulationStepper


class SimulationStepperTorqueSeriesTest(unittest.TestCase):
    def test_wheel_torque_cmd_nm_indexed_per_step(self) -> None:
        theta_center = float(SIMULATION.theta_center.to(ureg.rad).magnitude)
        start_angle_deg, end_angle_deg = los_theta_offsets_deg(
            orbit_height=SATELLITE_ALTITUDE,
            margin_deg=float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude),
        )

        stepper = SimulationStepper(
            simulation_config=SimulationConfig(
                render_mode=RenderMode.HEADLESS,
                controller_mode="baseline",
            ),
            earth_radius=EARTH_RADIUS,
            earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
            satellite=SATELLITE,
            satellite_altitude=SATELLITE_ALTITUDE,
            theta_center_rad=theta_center,
            start_angle_deg=float(start_angle_deg),
            end_angle_deg=float(end_angle_deg),
            sat_motion_span_scale=float(SIMULATION.sat_motion_span_scale),
            sat_z_offset_deg=float(SIMULATION.sat_z_offset.to(ureg.deg).magnitude),
            ureg=ureg,
        )

        s0 = stepper.finalize_series()
        n = int(s0.t_s.shape[0])
        self.assertEqual(s0.wheel_torque_cmd_nm.shape[0], n)
        np.testing.assert_array_equal(s0.wheel_torque_cmd_nm, np.zeros(n, dtype=float))

        stepper.step(wheel_torque_cmd_nm=1.5)
        stepper.step(wheel_torque_cmd_nm=-0.25)

        s1 = stepper.finalize_series()
        self.assertEqual(s1.wheel_torque_cmd_nm[0], 0.0)
        self.assertEqual(s1.wheel_torque_cmd_nm[1], 1.5)
        self.assertEqual(s1.wheel_torque_cmd_nm[2], -0.25)


if __name__ == "__main__":
    unittest.main()
