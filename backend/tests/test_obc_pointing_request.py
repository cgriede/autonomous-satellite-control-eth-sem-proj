"""Unit tests for nadir-relative OBC pointing (Exp 4 / production resolver)."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from environment_definition.constants.SATELLITE import MOMENT_OF_INERTIA_2D

from simulation.attitude_controller import nadir_target_angle_rad
from simulation.obc_pointing_request import (
    ObcPointingResolver,
    baseline_pointing_u,
    is_outside_safe_bounds,
    max_safe_rad,
    theta_target_to_u,
    u_to_fn,
    u_to_theta_req,
)


def test_u_zero_maps_to_nadir():
    theta_orbit = 0.5
    theta_req = u_to_theta_req(u=0.0, theta_orbit_rad=theta_orbit)
    theta_nadir = nadir_target_angle_rad(theta_orbit)
    assert theta_req == pytest.approx(theta_nadir)


def test_u_plus_minus_one_span_max_safe():
    limit = max_safe_rad()
    theta_orbit = 1.0
    fn_pos = u_to_fn(u=1.0)
    fn_neg = u_to_fn(u=-1.0)
    assert fn_pos == pytest.approx(limit)
    assert fn_neg == pytest.approx(-limit)
    theta_nadir = nadir_target_angle_rad(theta_orbit)
    assert u_to_theta_req(u=1.0, theta_orbit_rad=theta_orbit) == pytest.approx(
        theta_nadir + limit, abs=1e-6
    )


def test_u_clipped_at_adapter_boundary():
    fn = u_to_fn(u=2.0)
    assert fn == pytest.approx(max_safe_rad())


def test_hold_last_when_oob():
  sat_xy = np.array([7000.0, 0.0])
  limit = max_safe_rad()
  theta_orbit = 0.0
  theta_nadir = nadir_target_angle_rad(theta_orbit)
  resolver = ObcPointingResolver(tau_max_nm=0.02, sat_inertia=MOMENT_OF_INERTIA_2D)
  resolver.reset_episode(theta_orbit_rad=theta_orbit)

  # Request that would exceed safe envelope — use u=1 at extreme geometry.
  u_oob = 1.0
  theta_req = u_to_theta_req(u=u_oob, theta_orbit_rad=theta_orbit)
  if not is_outside_safe_bounds(theta_req_rad=theta_req, sat_pos_xy_km=sat_xy):
    pytest.skip("geometry does not produce OOB at u=1 for this sat position")

  tau1 = resolver.resolve_u_to_torque_nm(
      u=u_oob,
      theta_orbit_rad=theta_orbit,
      sat_pos_xy_km=sat_xy,
      body_z_rad=float(theta_nadir),
      omega_sat_rad_s=0.0,
      omega_orbit_rad_s=0.001,
  )
  assert resolver.diagnostics.hold_last_count == 1
  used1 = resolver.diagnostics.last_theta_used_rad

  tau2 = resolver.resolve_u_to_torque_nm(
      u=u_oob,
      theta_orbit_rad=theta_orbit,
      sat_pos_xy_km=sat_xy,
      body_z_rad=float(theta_nadir),
      omega_sat_rad_s=0.0,
      omega_orbit_rad_s=0.001,
  )
  assert resolver.diagnostics.hold_last_count == 2
  assert resolver.diagnostics.last_theta_used_rad == pytest.approx(used1)
  assert isinstance(tau1, float) and isinstance(tau2, float)


def test_in_bounds_updates_last_valid():
    sat_xy = np.array([7000.0, 0.0])
    theta_orbit = 0.3
    resolver = ObcPointingResolver(tau_max_nm=0.02, sat_inertia=MOMENT_OF_INERTIA_2D)
    resolver.reset_episode(theta_orbit_rad=theta_orbit)

    resolver.resolve_u_to_torque_nm(
        u=0.25,
        theta_orbit_rad=theta_orbit,
        sat_pos_xy_km=sat_xy,
        body_z_rad=float(nadir_target_angle_rad(theta_orbit)),
        omega_sat_rad_s=0.0,
        omega_orbit_rad_s=0.001,
    )
    assert resolver.diagnostics.hold_last_count == 0
    assert resolver.diagnostics.last_theta_used_rad == pytest.approx(
        resolver.diagnostics.last_theta_req_rad
    )


def test_episode_reset_initializes_nadir_hold():
    theta_orbit = 0.8
    resolver = ObcPointingResolver(tau_max_nm=0.02, sat_inertia=MOMENT_OF_INERTIA_2D)
    resolver.reset_episode(theta_orbit_rad=theta_orbit)
    theta_nadir = nadir_target_angle_rad(theta_orbit)
    assert resolver._last_valid_theta_req_rad == pytest.approx(theta_nadir)


def test_baseline_u_from_nadir_phase():
    policy = SimpleNamespace(pointing_phase="nadir")
    state = SimpleNamespace(theta_orbit_rad=0.4)
    sat_xy = np.array([7000.0, 0.0])
    u = baseline_pointing_u(policy, state, sat_pos_xy_km=sat_xy)
    assert u == pytest.approx(0.0)


def test_baseline_u_from_engage_target():
    anchor = np.array([7005.0, 10.0])
    policy = SimpleNamespace(pointing_phase="engage", active_anchor=lambda: anchor)
    state = SimpleNamespace(theta_orbit_rad=0.2)
    sat_xy = np.array([7000.0, 0.0])
    u = baseline_pointing_u(policy, state, sat_pos_xy_km=sat_xy)
    theta_target = float(np.arctan2(anchor[1] - sat_xy[1], anchor[0] - sat_xy[0]))
    expected = theta_target_to_u(
        theta_target_rad=theta_target,
        theta_orbit_rad=float(state.theta_orbit_rad),
    )
    assert u == pytest.approx(expected)
