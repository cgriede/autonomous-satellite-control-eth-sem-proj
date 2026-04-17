"""
Headless printout of the 1D fixed-bird observation line as ASCII per timestep.

Run with current working directory set to ``backend/`` (see VS Code launch
``Sat Sim: fixed bird observation (headless)``), or rely on the path fix below::

    conda activate LRF
    cd backend
    python scripts/print_fixed_bird_observation_line.py

Each timestep prints ``ts <1-based index>:`` then one character per bin:
``-`` space, ``E`` earth, ``C`` cloud, ``X`` target, ``S`` cone hit on Earth.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

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
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE, SATELLITE_ALTITUDE
from simulation.observation_line_constants import (
    FIXED_GROUND_CONE_HIT_EARTH,
    OBSERVATION_LINE_NOT_COMPUTED,
)
from simulation.run_simulation import run_simulation
from utils.flight_geometry.line_of_sight import minimum_contact_angle


def _fixed_ground_codes_to_ascii_line(codes: np.ndarray) -> str:
    mapping = {
        0: "-",
        1: "E",
        2: "C",
        3: "X",
        int(FIXED_GROUND_CONE_HIT_EARTH): "S",
        int(OBSERVATION_LINE_NOT_COMPUTED): "?",
    }
    chars: list[str] = []
    for c in np.asarray(codes, dtype=np.int8).ravel():
        ci = int(c)
        ch = mapping.get(ci)
        if ch is None:
            raise ValueError(f"Unknown fixed-ground observation code: {ci}")
        chars.append(ch)
    return "".join(chars)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Print fixed-bird observation line (ASCII) per strided timestep. "
            "Observer target angle matches the renderer (north pole, pi/2 rad). "
            "Uses exactly 100 bins over the fixed 1000 km stripe."
        )
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=10,
        help="Print every k-th frame (default: 10).",
    )
    parser.add_argument(
        "--num-frames",
        type=int,
        default=None,
        help="Override SIMULATION.num_frames for shorter runs.",
    )
    args = parser.parse_args()

    r_earth_km = EARTH_RADIUS.to(ureg.km).magnitude
    theta_center = SIMULATION.theta_center.to(ureg.rad).magnitude
    alpha = minimum_contact_angle(observer_height=0.0 * ureg.km, orbit_height=SATELLITE_ALTITUDE)
    contact_half_angle_deg = alpha.to(ureg.deg).magnitude
    margin_deg = SIMULATION.contact_margin_angle.to(ureg.deg).magnitude
    start_angle_deg = -(contact_half_angle_deg + margin_deg)
    end_angle_deg = contact_half_angle_deg + margin_deg

    num_frames = int(args.num_frames) if args.num_frames is not None else int(SIMULATION.num_frames)

    series = run_simulation(
        earth_radius=EARTH_RADIUS,
        earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
        satellite=SATELLITE,
        satellite_altitude=SATELLITE_ALTITUDE,
        theta_center_rad=float(theta_center),
        start_angle_deg=float(start_angle_deg),
        end_angle_deg=float(end_angle_deg),
        sat_motion_span_scale=float(SIMULATION.sat_motion_span_scale),
        num_frames=num_frames,
        sat_z_offset_deg=float(SIMULATION.sat_z_offset.to(ureg.deg).magnitude),
        ureg=ureg,
        observer_target_angle_rad=float(np.arctan2(r_earth_km, 0.0)),
        camera_pixel_ray_samples=SIMULATION.camera_pixel_ray_samples,
        camera_observation_line_n_bins=100,
    )

    stride = max(1, int(args.stride))
    n = series.t_s.shape[0]
    for k in range(0, n, stride):
        line = _fixed_ground_codes_to_ascii_line(series.fixed_ground_line_codes[k])
        print(f"ts {k + 1}:")
        print(line)


if __name__ == "__main__":
    main()
