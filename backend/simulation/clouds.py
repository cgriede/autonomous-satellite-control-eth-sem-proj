#TODO add missing imports

#TODO define cloud simulation behaviour here, load config from SIMULATION.clouds and tie into main environment simulation loop (run_simulation) and renderning (render_main)
#TODO find other cloud functions and put them here


def _cloud_arc_specs_from_simulation(sim_idx: int) -> list[dict[str, object]]:
    """Build per-cloud plot specs from `SimulationStateSeries` (filled in `run_simulation`)."""
    sim_time_local = float(simulation.t_s[sim_idx])
    growth_phase = sim_time_local / max(simulation.metadata.sim_total_s, 1e-9)
    cloud_thickness = 1.0 + (RENDER.cloud_growth_linewidth_scale - 1.0) * np.clip(growth_phase, 0.0, 1.0)
    r = simulation.cloud_arc_radius_km[sim_idx, :]
    s0 = simulation.cloud_arc_start_rad[sim_idx, :]
    s1 = simulation.cloud_arc_end_rad[sim_idx, :]
    n_clouds = int(r.shape[0])
    specs: list[dict[str, object]] = []
    for i in range(n_clouds):
        radius = float(r[i])
        start = float(s0[i])
        end = float(s1[i])
        if not (np.isfinite(radius) and np.isfinite(start) and np.isfinite(end)):
            specs.append(
                {
                    "radius": float("nan"),
                    "theta": np.array([], dtype=float),
                    "x": np.array([], dtype=float),
                    "y": np.array([], dtype=float),
                    "start": 0.0,
                    "end": 0.0,
                    "growth": cloud_thickness,
                }
            )
            continue
        theta = np.linspace(start, end, RENDER.cloud_segment_points)
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        specs.append(
            {
                "radius": radius,
                "theta": theta,
                "x": x,
                "y": y,
                "start": start,
                "end": end,
                "growth": cloud_thickness,
            }
        )
    return specs

def _sample_cloud_speed_km_s(height_km):
    # Altitude-stratified speed bounds from user-provided weather guidance.
    if height_km < 2.0:
        speed_kmh = cloud_rng.uniform(16.0, 65.0)
    elif height_km < 6.0:
        speed_kmh = cloud_rng.uniform(32.0, 100.0)
    else:
        speed_kmh = cloud_rng.uniform(80.0, 190.0)
    return speed_kmh / 3600.0

cloud_models = []
for cloud in SIMULATION.clouds:
    cloud_height_km = cloud.height.to(ureg.km).magnitude
    start_rad = cloud.start_location.to(ureg.rad).magnitude
    end_rad = cloud.end_location.to(ureg.rad).magnitude
    radius_km = R_earth + cloud_height_km
    speed_km_s = _sample_cloud_speed_km_s(cloud_height_km)
    omega_rad_s = speed_km_s / max(radius_km, 1e-9)
    cloud_models.append(
        {
            "radius_km": radius_km,
            "start_rad_0": start_rad,
            "end_rad_0": end_rad,
            "omega_rad_s": omega_rad_s,
            "noise_amp": float(cloud_rng.uniform(0.12, 0.30)),
            "noise_freq_rad_s": float(cloud_rng.uniform(0.015, 0.05)),
            "noise_phase": float(cloud_rng.uniform(0.0, 2.0 * np.pi)),
        }
    )