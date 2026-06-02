"""Notebook verification helpers for cloud formation (table + static render panels)."""

from __future__ import annotations

from typing import Any

import numpy as np

from environment_definition.constants import EARTH_RADIUS, RENDER, SIMULATION, ureg
from environment_definition.constants.MISSION import los_theta_offsets_deg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import SATELLITE_ALTITUDE
from utils.geometry.mission_stripe_disk import (
    primary_stripe_disk_phi_bounds_deg,
    primary_stripe_midpoint_disk_xy_km_on_sphere,
)
from utils.geometry.orbit_disk_polar_meridian import cloud_disk_phi_bounds_deg, geodetic_lonlat_deg
from utils.geodesics.geodesic_helpers import geodesic_distance

from .cloud_formation import formation_path_length_km


def _extent_km_between_cloud_endpoints(cloud: Any) -> int:
    lat_s, lon_s = geodetic_lonlat_deg(cloud.start_location)
    lat_e, lon_e = geodetic_lonlat_deg(cloud.end_location)
    dist_m = float(
        geodesic_distance(
            lon_s * ureg.deg,
            lat_s * ureg.deg,
            lon_e * ureg.deg,
            lat_e * ureg.deg,
        ).to(ureg.m).magnitude
    )
    return int(round(dist_m / 1000.0))


def print_cloud_verification_summary(
    clouds: list[Any],
    *,
    formation_start: Any,
    formation_end: Any,
) -> None:
    """Print summary + structured table for operator review (Gate 3 numbers)."""
    path_km = formation_path_length_km(formation_start, formation_end)
    lat_fs, lon_fs = geodetic_lonlat_deg(formation_start)
    lat_fe, lon_fe = geodetic_lonlat_deg(formation_end)

    print("Cloud formation verification summary")
    print(f"  count:      {len(clouds)}")
    print(f"  path_km:    {path_km}")
    print(f"  formation:  ({lat_fs:.2f}, {lon_fs:.1f}) -> ({lat_fe:.2f}, {lon_fe:.1f})")

    if not clouds:
        print("\n(no clouds generated)")
        return

    phi_bounds = [cloud_disk_phi_bounds_deg(c) for c in clouds]
    phi_min = min(lo for lo, _ in phi_bounds)
    phi_max = max(hi for _, hi in phi_bounds)

    print(f"  phi span:   {phi_min:.3f} deg -> {phi_max:.3f} deg")
    print("\nStructured cloud table")
    print(
        f"{'idx':>3}  {'base_km':>7} {'top_km':>6} {'thick_km':>8} {'extent_km':>9} "
        f"{'start_lat':>9} {'start_lon':>9} {'phi_lo':>8} {'phi_hi':>8}"
    )
    for idx, cloud in enumerate(clouds):
        base_km = int(round(float(cloud.base_altitude.to(ureg.km).magnitude)))
        top_km = int(round(float(cloud.top_altitude.to(ureg.km).magnitude)))
        thick_km = top_km - base_km
        extent_km = _extent_km_between_cloud_endpoints(cloud)
        lat_s, lon_s = geodetic_lonlat_deg(cloud.start_location)
        phi_lo, phi_hi = phi_bounds[idx]
        print(
            f"{idx:>3}  {base_km:>7} {top_km:>6} {thick_km:>8} {extent_km:>9} "
            f"{lat_s:>9.3f} {lon_s:>9.1f} {phi_lo:>8.3f} {phi_hi:>8.3f}"
        )


def cloud_world_xy_from_clouds(
    clouds: tuple[Any, ...] | list[Any],
    *,
    sim_time_s: float = 0.0,
    sim_total_s: float = 100.0,
) -> list[dict[str, np.ndarray]]:
    """Orbit-disk arc polylines for static preview (same kernel as simulation)."""
    from simulation.camera_2d import compute_cloud_arc_specs_at_time

    earth_radius_km = float(EARTH_RADIUS.to(ureg.km).magnitude)
    specs = compute_cloud_arc_specs_at_time(
        sim_time_s=float(sim_time_s),
        sim_total_s=float(sim_total_s),
        earth_radius_km=earth_radius_km,
        clouds=tuple(clouds),
    )
    n_pts = int(RENDER.cloud_segment_points)
    world: list[dict[str, np.ndarray]] = []
    for spec in specs:
        r = float(spec["radius_km"])
        s = float(spec["start_rad"])
        e = float(spec["end_rad"])
        if not (np.isfinite(r) and np.isfinite(s) and np.isfinite(e)):
            world.append({"x": np.array([], dtype=float), "y": np.array([], dtype=float)})
            continue
        th = np.linspace(s, e, n_pts, dtype=float)
        world.append({"x": r * np.cos(th), "y": r * np.sin(th)})
    return world


def build_static_cloud_preview_scene(
    clouds: tuple[Any, ...] | list[Any],
) -> dict[str, Any]:
    """Scene dict for ``build_main_panel`` / ``build_closeup_panel`` (pre-sim arc preview)."""
    r_earth_km = float(EARTH_RADIUS.to(ureg.km).magnitude)
    r_orbit_km = r_earth_km + float(SATELLITE_ALTITUDE.to(ureg.km).magnitude)
    theta_center_rad = float(SIMULATION.theta_center.to(ureg.rad).magnitude)
    margin_deg = float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude)
    los_lo_deg, los_hi_deg = los_theta_offsets_deg(
        orbit_height=SATELLITE_ALTITUDE,
        margin_deg=margin_deg,
    )

    phi_bounds = [cloud_disk_phi_bounds_deg(c) for c in clouds] if clouds else []
    tgt_lo_deg, tgt_hi_deg = primary_stripe_disk_phi_bounds_deg()
    overall_phi_lo = min([tgt_lo_deg, *(lo for lo, _ in phi_bounds)], default=tgt_lo_deg)
    overall_phi_hi = max([tgt_hi_deg, *(hi for _, hi in phi_bounds)], default=tgt_hi_deg)
    theta_center_deg = float(SIMULATION.theta_center.to(ureg.deg).magnitude)
    frame_lo_deg = min(los_lo_deg, los_hi_deg, overall_phi_lo - theta_center_deg, overall_phi_hi - theta_center_deg)
    frame_hi_deg = max(los_lo_deg, los_hi_deg, overall_phi_lo - theta_center_deg, overall_phi_hi - theta_center_deg)

    view_anchor_xy = primary_stripe_midpoint_disk_xy_km_on_sphere(earth_radius_km=r_earth_km)
    n_clouds = len(clouds)

    return {
        "R_earth": r_earth_km,
        "R_orbit": r_orbit_km,
        "theta_center": theta_center_rad,
        "start_angle_deg": frame_lo_deg,
        "end_angle_deg": frame_hi_deg,
        "target_region_start_angle_deg": float(tgt_lo_deg),
        "target_region_end_angle_deg": float(tgt_hi_deg),
        "target_region_bounds_deg": [(float(tgt_lo_deg), float(tgt_hi_deg))],
        "view_anchor_x": float(view_anchor_xy[0]),
        "view_anchor_y": float(view_anchor_xy[1]),
        "view_anchor_pos": np.asarray(view_anchor_xy, dtype=float),
        "cloud_models": [None] * n_clouds,
        "n_clouds": n_clouds,
        "n_bins": 0,
        "n_bins_secondary": 0,
        "controller_mode": "static-cloud-preview",
        "cloud_world": cloud_world_xy_from_clouds(clouds),
    }


def fit_standalone_axes(
    ax,
    fig,
    *,
    margin_l: float = 0.06,
    margin_b: float = 0.10,
    margin_w: float = 0.9,
    title_frac: float = 0.08,
) -> None:
    """Match figure height to equal-aspect data (from target_grid notebook)."""
    import matplotlib.pyplot as plt

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    data_aspect = (xlim[1] - xlim[0]) / (ylim[1] - ylim[0])
    usable_h_frac = 1.0 - margin_b - title_frac
    fig_w, _ = fig.get_size_inches()
    fig_h = (margin_w * fig_w) / data_aspect / usable_h_frac
    fig.set_size_inches(fig_w, fig_h)
    fig_w, fig_h = fig.get_size_inches()
    h_frac = (margin_w * fig_w) / data_aspect / fig_h
    ax.set_position([margin_l, margin_b, margin_w, h_frac])
    ax.set_aspect("equal", adjustable="box")


def show_static_preview_from_clouds(clouds: tuple[Any, ...] | list[Any]) -> None:
    """Pre-sim main + closeup panels using ``compute_cloud_arc_specs`` arcs only."""
    import matplotlib.pyplot as plt

    from render._closeup_view import build_closeup_panel
    from render._main_view import build_main_panel

    scene = build_static_cloud_preview_scene(clouds)

    fig_main = plt.figure(figsize=(9.5, 6.5), facecolor=RENDER.space_background)
    axes_main, artists_main = build_main_panel(fig_main, scene)
    for i, spec in enumerate(scene["cloud_world"]):
        artists_main["cloud_glow"][i].set_data(spec["x"], spec["y"])
        artists_main["cloud_core"][i].set_data(spec["x"], spec["y"])
    fit_standalone_axes(axes_main["main"], fig_main)
    fig_main.suptitle("Static cloud arc preview (generator)", color="white", fontsize=14)
    plt.show()

    fig_closeup = plt.figure(figsize=(10.5, 4.8), facecolor=RENDER.space_background)
    axes_closeup, artists_closeup = build_closeup_panel(fig_closeup, scene)
    for i, spec in enumerate(scene["cloud_world"]):
        artists_closeup["cloud_glow"][i].set_data(spec["x"], spec["y"])
        artists_closeup["cloud_core"][i].set_data(spec["x"], spec["y"])
    fit_standalone_axes(axes_closeup["closeup"], fig_closeup, margin_b=0.12, title_frac=0.10)
    fig_closeup.suptitle("Cloud arc closeup (generator)", color="white", fontsize=14)
    plt.show()


def show_static_panels_from_series(series: Any, *, frame_idx: int = 0) -> None:
    """Main + closeup panels from canonical ``SimulationStateSeries`` (post-sim Gate 3)."""
    import matplotlib.pyplot as plt

    from render import render_main
    from render._closeup_view import build_closeup_panel, update_closeup_panel
    from render._main_view import build_main_panel, update_main_panel

    render_main._configure_runtime_from_series(series)
    idx = int(np.clip(frame_idx, 0, len(series.t_s) - 1))
    scene = render_main.sample_scene(idx)

    fig_main = plt.figure(figsize=(9.5, 6.5), facecolor=RENDER.space_background)
    axes_main, artists_main = build_main_panel(fig_main, render_main.STATIC_SCENE)
    update_main_panel(artists_main, scene)
    fit_standalone_axes(axes_main["main"], fig_main)
    fig_main.suptitle(f"Cloud overview (sim frame {idx})", color="white", fontsize=14)
    plt.show()

    fig_closeup = plt.figure(figsize=(10.5, 4.8), facecolor=RENDER.space_background)
    axes_closeup, artists_closeup = build_closeup_panel(fig_closeup, render_main.STATIC_SCENE)
    update_closeup_panel(artists_closeup, scene)
    fit_standalone_axes(axes_closeup["closeup"], fig_closeup, margin_b=0.12, title_frac=0.10)
    fig_closeup.suptitle(f"Cloud closeup (sim frame {idx})", color="white", fontsize=14)
    plt.show()

    plt.close(fig_main)
    plt.close(fig_closeup)
    render_main.FIG = None
