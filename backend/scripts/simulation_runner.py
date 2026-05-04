from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
# Keep normal runs quiet; the debug wrapper can still raise this to DEBUG.
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(message)s'
)


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from environment_definition.constants import (
    EARTH_GRAVITATIONAL_PARAMETER,
    EARTH_RADIUS,
    RenderMode,
    SIMULATION,
    SimulationConfig,
    UREG as ureg,
)
from environment_definition.constants.MISSION import los_theta_offsets_deg
from environment_definition.mission_profiles.mission_1_random_fl import SATELLITE, SATELLITE_ALTITUDE
from simulation.run_simulation import run_simulation


def _configure_matplotlib_backend(*, render_mode: RenderMode) -> None:
    if render_mode in {RenderMode.EXPORT, RenderMode.HEADLESS}:
        import matplotlib

        matplotlib.use("Agg")


def _run_sat_simulation(*, simulation_config: SimulationConfig):
    theta_center = SIMULATION.theta_center.to(ureg.rad).magnitude
    start_angle_deg, end_angle_deg = los_theta_offsets_deg(
        orbit_height=SATELLITE_ALTITUDE,
        margin_deg=float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude),
    )

    return run_simulation(
        simulation_config=simulation_config,
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
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run satellite simulation and render output.")
    parser.add_argument(
        "--render-mode",
        type=str,
        choices=(RenderMode.HEADLESS.value, RenderMode.INTERACTIVE.value, RenderMode.EXPORT.value),
        default=RenderMode.INTERACTIVE.value,
        help="Rendering mode for the simulation output.",
    )
    parser.add_argument(
        "--controller-mode",
        type=str,
        choices=("baseline", "random"),
        default="random",
        help="Controller policy used by run_simulation.",
    )
    parser.add_argument(
        "--save-one-pass-30x",
        action="store_true",
        help="Force export mode and save a one-pass MP4 at configured export speed.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Optional explicit MP4 output path for one-pass export.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    render_mode = RenderMode(args.render_mode)
    if args.save_one_pass_30x:
        render_mode = RenderMode.EXPORT

    simulation_config = SimulationConfig(
        render_mode=render_mode,
        controller_mode=args.controller_mode,
    )
    simulation_series = _run_sat_simulation(simulation_config=simulation_config)
    _configure_matplotlib_backend(render_mode=render_mode)

    from render.render_main import render_from_series

    output_path = render_from_series(
        simulation_series=simulation_series,
        render_mode=render_mode,
        output_path=args.output_path,
    )
    if output_path is not None:
        print(f"Saved one-pass video to: {output_path}")


if __name__ == "__main__":
    main()
