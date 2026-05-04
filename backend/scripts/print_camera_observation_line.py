"""
Headless printout of the 1D camera observation line as ASCII per timestep.

Run with current working directory set to ``backend/`` (see VS Code launch
``Sat Sim: camera observation (headless)``), or rely on the path fix below::

    conda activate auto-sat
    cd backend
    python scripts/print_camera_observation_line.py

Each timestep prints ``ts <1-based index>:`` then one character per bin:
``-`` space, ``E`` earth, ``C`` cloud, ``X`` target (observer direction).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python scripts/...` from `backend/` without PYTHONPATH.
_backend_root = Path(__file__).resolve().parents[1]
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from environment_definition.constants import (
    EARTH_GRAVITATIONAL_PARAMETER,
    EARTH_RADIUS,
    SIMULATION,
    UREG as ureg,
)
from environment_definition.constants.MISSION import mission_target_window_deg
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE, SATELLITE_ALTITUDE
from simulation.camera_2d import observation_codes_to_ascii_line
from simulation.run_simulation import run_simulation


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Print camera observation line (ASCII) per strided timestep. "
            "Observer target angle matches the renderer (north pole, pi/2 rad). "
            "Requires current working directory to be backend/ for imports."
        )
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=10,
        help="Print every k-th frame (default: 10).",
    )
    parser.add_argument(
        "--n-bins",
        type=int,
        default=None,
        help="Override SIMULATION.camera_observation_line_n_bins (default: from SIMULATION).",
    )
    parser.add_argument(
        "--num-frames",
        type=int,
        default=None,
        help="Deprecated: simulation frame count is time-based now and this flag is ignored.",
    )
    args = parser.parse_args()

    theta_center = SIMULATION.theta_center.to(ureg.rad).magnitude
    start_angle_deg, end_angle_deg = mission_target_window_deg(
        orbit_height=SATELLITE_ALTITUDE,
        margin_deg=float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude),
    )

    if args.num_frames is not None:
        print("Warning: --num-frames is deprecated and ignored (simulation is time-step based).")

    series = run_simulation(
        earth_radius=EARTH_RADIUS,
        earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
        satellite=SATELLITE,
        satellite_altitude=SATELLITE_ALTITUDE,
        theta_center_rad=float(theta_center),
        start_angle_deg=float(start_angle_deg),
        end_angle_deg=float(end_angle_deg),
        sat_motion_span_scale=float(SIMULATION.sat_motion_span_scale),
        sat_z_offset_deg=float(SIMULATION.sat_z_offset.to(ureg.deg).magnitude),
        ureg=ureg,
        camera_pixel_ray_samples=SIMULATION.camera_pixel_ray_samples,
        camera_observation_line_n_bins=args.n_bins,
    )

    stride = max(1, int(args.stride))
    n = series.t_s.shape[0]
    for k in range(0, n, stride):
        line = observation_codes_to_ascii_line(series.camera_observation_line_codes[k])
        print(f"ts {k + 1}:")
        print(line)


if __name__ == "__main__":
    main()
