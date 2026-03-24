"""
Lightweight coding-model showcase: timed sanity checks across the backend stack.

Run from VS Code via "Showcase: Coding Model Benchmark" or:
  conda activate auto-sat
  cd backend && python tools/showcase_benchmark.py
"""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable
from typing import Any


def _ms(t0: float) -> float:
    return (time.perf_counter() - t0) * 1000.0


def _run_case(name: str, fn: Callable[[], Any], verbose: bool) -> bool:
    t0 = time.perf_counter()
    try:
        out = fn()
        dt = _ms(t0)
        extra = f" → {out!r}" if verbose and out is not None else ""
        print(f"  [PASS] {name} ({dt:.2f} ms){extra}")
        return True
    except Exception as exc:  # noqa: BLE001 — showcase aggregates failures
        dt = _ms(t0)
        print(f"  [FAIL] {name} ({dt:.2f} ms): {exc}")
        return False


def _case_import_mission_objects() -> str:
    from environment_definition.mission_profiles.mission_1_random_fl import (
        MISSION_PROFILE,
        SATELLITE,
        SATELLITE_ALTITUDE,
    )

    _ = SATELLITE.mass
    _ = MISSION_PROFILE.orbit_speed
    return f"alt={SATELLITE_ALTITUDE}"


def _case_line_of_sight() -> str:
    from environment_definition.constants import UREG as ureg
    from environment_definition.mission_profiles.mission_1_random_fl import (
        SATELLITE_ALTITUDE,
    )
    from utils.flight_geometry.line_of_sight import minimum_contact_angle

    alpha = minimum_contact_angle(
        observer_height=0.0 * ureg.km,
        orbit_height=SATELLITE_ALTITUDE,
    )
    return f"contact_half_angle_deg={alpha.to(ureg.deg).magnitude:.6f}"


def _case_kinematic_trajectory() -> str:
    from environment_definition.constants import (
        EARTH_GRAVITATIONAL_PARAMETER,
        EARTH_RADIUS,
        SIMULATION,
        UREG as ureg,
    )
    from environment_definition.mission_profiles.mission_1_random_fl import (
        SATELLITE_ALTITUDE,
    )
    from simulation.trajectory_simulator import (
        KinematicSimulationConfig,
        simulate_kinematic_trajectory,
    )
    from utils.flight_geometry.line_of_sight import minimum_contact_angle

    r_earth_km = EARTH_RADIUS.to(ureg.km).magnitude
    sat_alt_km = SATELLITE_ALTITUDE.to(ureg.km).magnitude
    mu_km3_s2 = EARTH_GRAVITATIONAL_PARAMETER.to(
        (ureg.km**3) / (ureg.s**2)
    ).magnitude
    theta_center_rad = SIMULATION.theta_center.to(ureg.rad).magnitude
    alpha = minimum_contact_angle(
        observer_height=0.0 * ureg.km,
        orbit_height=SATELLITE_ALTITUDE,
    )
    contact_half_deg = alpha.to(ureg.deg).magnitude
    margin_deg = SIMULATION.contact_margin_angle.to(ureg.deg).magnitude
    start_deg = -(contact_half_deg + margin_deg)
    end_deg = contact_half_deg + margin_deg
    sat_z_deg = SIMULATION.sat_z_offset.to(ureg.deg).magnitude

    cfg = KinematicSimulationConfig(
        earth_radius_km=float(r_earth_km),
        sat_altitude_km=float(sat_alt_km),
        mu_earth_km3_s2=float(mu_km3_s2),
        theta_center_rad=float(theta_center_rad),
        start_angle_deg=float(start_deg),
        end_angle_deg=float(end_deg),
        sat_motion_span_scale=float(SIMULATION.sat_motion_span_scale),
        num_frames=128,
        sat_z_offset_deg=float(sat_z_deg),
        body_spin_rate_rad_s=0.0,
    )
    series = simulate_kinematic_trajectory(cfg)
    return f"frames={len(series.t_s)}, T_orbit_s={series.metadata.orbit_period_s:.2f}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backend showcase / micro-benchmark.")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print extra detail from each check.",
    )
    args = parser.parse_args(argv)

    print("Coding model showcase — backend integration checks")
    print("-" * 52)

    cases = [
        ("import mission + Satellite/Mission objects", _case_import_mission_objects),
        ("line-of-sight minimum contact angle", _case_line_of_sight),
        ("kinematic trajectory simulation (128 frames)", _case_kinematic_trajectory),
    ]

    ok = True
    t_suite = time.perf_counter()
    for name, fn in cases:
        ok = _run_case(name, fn, args.verbose) and ok

    print("-" * 52)
    print(f"Suite total: {_ms(t_suite):.2f} ms")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
