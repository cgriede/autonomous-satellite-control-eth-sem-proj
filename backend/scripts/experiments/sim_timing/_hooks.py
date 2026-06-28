"""Monkey-patch hooks for simulation timing (experiment-only; no production edits)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from _timing_collector import PER_STEP_CATEGORIES, TimingCollector

_PATCH_STATE: dict[str, Any] = {
    "installed": False,
    "originals": {},
    "collector": None,
}


def _collector() -> TimingCollector:
    coll = _PATCH_STATE.get("collector")
    if coll is None:
        raise RuntimeError("Timing hooks not installed.")
    return coll


def _wrap(name: str, fn: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            _collector().add(name, time.perf_counter() - t0)

    wrapper.__name__ = getattr(fn, "__name__", name)
    wrapper.__doc__ = fn.__doc__
    return wrapper


def install(collector: TimingCollector) -> None:
    """Patch production kernels; call ``uninstall`` in a ``finally`` block."""
    if _PATCH_STATE["installed"]:
        raise RuntimeError("Timing hooks already installed.")

    import simulation.camera_2d as camera_2d_mod
    import simulation.dynamics_kernel as dynamics_mod
    import simulation.reward_kernel as reward_mod
    import simulation.sensor_kernel as sensor_mod
    import simulation.stepper as stepper_mod
    import utils.geodesics.geodesic_helpers as geodesic_mod
    import utils.geometry.orbit_disk_wgs84 as wgs84_mod

    originals: dict[str, Any] = {
        "DynamicsKernel.propagate": dynamics_mod.DynamicsKernel.propagate,
        "compute_cloud_arc_specs_at_time": camera_2d_mod.compute_cloud_arc_specs_at_time,
        "_evaluate_sensors": sensor_mod._evaluate_sensors,
        "RewardKernel.evaluate": reward_mod.RewardKernel.evaluate,
        "disk_xy_km_to_geodetic_deg": wgs84_mod.disk_xy_km_to_geodetic_deg,
        "circle_stripe_footprint_overlap_ratio": geodesic_mod.circle_stripe_footprint_overlap_ratio,
        "SimulationStepper._satellite_xy_km": stepper_mod.SimulationStepper._satellite_xy_km,
        "SimulationStepper.step": stepper_mod.SimulationStepper.step,
    }

    orig_step = originals["SimulationStepper.step"]
    orig_sat_xy = originals["SimulationStepper._satellite_xy_km"]

    def patched_satellite_xy_km(self, k: int) -> Any:
        t0 = time.perf_counter()
        try:
            return orig_sat_xy(self, k)
        finally:
            _collector().add("orbit_kinematics", time.perf_counter() - t0)

    def patched_step(self, *, wheel_torque_cmd_nm: float) -> Any:
        coll = _collector()
        coll.begin_step()
        before = coll.snapshot()
        t0 = time.perf_counter()
        try:
            return orig_step(self, wheel_torque_cmd_nm=wheel_torque_cmd_nm)
        finally:
            step_wall = time.perf_counter() - t0
            delta = coll.delta_since(before)
            hooked = sum(delta.get(c, 0.0) for c in PER_STEP_CATEGORIES if c != "stepper_bookkeeping")
            coll.add("stepper_bookkeeping", max(0.0, step_wall - hooked))

    dynamics_mod.DynamicsKernel.propagate = staticmethod(  # type: ignore[method-assign]
        _wrap("robotics_dynamics", originals["DynamicsKernel.propagate"])
    )
    orig_compute_cloud_specs = originals["compute_cloud_arc_specs_at_time"]
    wrapped_cloud_specs = _wrap("environment_clouds", orig_compute_cloud_specs)
    wrapped_geodesy = _wrap("geodesy", originals["disk_xy_km_to_geodetic_deg"])

    camera_2d_mod.compute_cloud_arc_specs_at_time = wrapped_cloud_specs
    sensor_mod.compute_cloud_arc_specs_at_time = wrapped_cloud_specs
    stepper_mod.disk_xy_km_to_geodetic_deg = wrapped_geodesy
    wgs84_mod.disk_xy_km_to_geodetic_deg = wrapped_geodesy

    if hasattr(wgs84_mod, "batch_disk_xy_rows_km_to_geodetic_deg"):
        originals["batch_disk_xy_rows_km_to_geodetic_deg"] = wgs84_mod.batch_disk_xy_rows_km_to_geodetic_deg
        wgs84_mod.batch_disk_xy_rows_km_to_geodetic_deg = _wrap(
            "geodesy",
            originals["batch_disk_xy_rows_km_to_geodetic_deg"],
        )

    sensor_mod._evaluate_sensors = _wrap(
        "sensor_camera_rays",
        originals["_evaluate_sensors"],
    )
    reward_mod.RewardKernel.evaluate = staticmethod(  # type: ignore[method-assign]
        _wrap("reward_ml", originals["RewardKernel.evaluate"])
    )
    geodesic_mod.circle_stripe_footprint_overlap_ratio = _wrap(
        "footprint_target",
        originals["circle_stripe_footprint_overlap_ratio"],
    )

    stepper_mod.SimulationStepper._satellite_xy_km = patched_satellite_xy_km  # type: ignore[method-assign]
    stepper_mod.SimulationStepper.step = patched_step  # type: ignore[method-assign]

    _PATCH_STATE["originals"] = originals
    _PATCH_STATE["collector"] = collector
    _PATCH_STATE["installed"] = True
    _PATCH_STATE["module_refs"] = {
        "dynamics_mod": dynamics_mod,
        "camera_2d_mod": camera_2d_mod,
        "sensor_mod": sensor_mod,
        "reward_mod": reward_mod,
        "stepper_mod": stepper_mod,
        "wgs84_mod": wgs84_mod,
        "geodesic_mod": geodesic_mod,
    }


def install_render_hooks(collector: TimingCollector) -> None:
    """Patch render export path (nested inside ``render_from_series``)."""
    import render.render_main as render_mod

    originals = _PATCH_STATE.setdefault("originals", {})
    if "save_one_pass_video_30x" not in originals:
        originals["save_one_pass_video_30x"] = render_mod.save_one_pass_video_30x
        originals["render_from_series"] = render_mod.render_from_series

    orig_save = originals["save_one_pass_video_30x"]
    orig_render = originals["render_from_series"]

    def patched_save(*args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return orig_save(*args, **kwargs)
        finally:
            collector.add("export_video", time.perf_counter() - t0)

    def patched_render(*args: Any, **kwargs: Any) -> Any:
        export_before = collector.totals_s.get("export_video", 0.0)
        t0 = time.perf_counter()
        try:
            return orig_render(*args, **kwargs)
        finally:
            render_wall = time.perf_counter() - t0
            export_delta = collector.totals_s.get("export_video", 0.0) - export_before
            collector.add("render", max(0.0, render_wall - export_delta))

    render_mod.save_one_pass_video_30x = patched_save
    render_mod.render_from_series = patched_render
    _PATCH_STATE["render_mod"] = render_mod
    _PATCH_STATE["collector"] = collector


def uninstall() -> None:
    """Restore all patched callables."""
    originals = _PATCH_STATE.get("originals", {})
    if not originals:
        return

    if _PATCH_STATE.get("installed"):
        refs = _PATCH_STATE["module_refs"]
        refs["dynamics_mod"].DynamicsKernel.propagate = originals["DynamicsKernel.propagate"]  # type: ignore[method-assign]
        refs["camera_2d_mod"].compute_cloud_arc_specs_at_time = originals["compute_cloud_arc_specs_at_time"]
        refs["sensor_mod"].compute_cloud_arc_specs_at_time = originals["compute_cloud_arc_specs_at_time"]
        refs["sensor_mod"]._evaluate_sensors = originals["_evaluate_sensors"]
        refs["reward_mod"].RewardKernel.evaluate = originals["RewardKernel.evaluate"]  # type: ignore[method-assign]
        refs["wgs84_mod"].disk_xy_km_to_geodetic_deg = originals["disk_xy_km_to_geodetic_deg"]
        refs["stepper_mod"].disk_xy_km_to_geodetic_deg = originals["disk_xy_km_to_geodetic_deg"]
        if "batch_disk_xy_rows_km_to_geodetic_deg" in originals:
            refs["wgs84_mod"].batch_disk_xy_rows_km_to_geodetic_deg = originals[
                "batch_disk_xy_rows_km_to_geodetic_deg"
            ]
        refs["geodesic_mod"].circle_stripe_footprint_overlap_ratio = originals[
            "circle_stripe_footprint_overlap_ratio"
        ]
        refs["stepper_mod"].SimulationStepper._satellite_xy_km = originals["SimulationStepper._satellite_xy_km"]  # type: ignore[method-assign]
        refs["stepper_mod"].SimulationStepper.step = originals["SimulationStepper.step"]  # type: ignore[method-assign]

    if "render_mod" in _PATCH_STATE:
        render_mod = _PATCH_STATE["render_mod"]
        if "save_one_pass_video_30x" in originals:
            render_mod.save_one_pass_video_30x = originals["save_one_pass_video_30x"]
        if "render_from_series" in originals:
            render_mod.render_from_series = originals["render_from_series"]

    _PATCH_STATE["installed"] = False
    _PATCH_STATE["collector"] = None
    _PATCH_STATE["originals"] = {}
    _PATCH_STATE.pop("module_refs", None)
    _PATCH_STATE.pop("render_mod", None)
