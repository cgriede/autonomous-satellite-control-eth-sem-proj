<!--
  Slideshow-style: blank line, then a line with only --- between slides.
-->

# Physical reference constants

Canonical Earth and gravity parameters and coordinate/ellipsoid choices used in code.

---

# Earth sphere & gravity field

Source: `environment_definition/constants/EARTH.py`.

- **Mean radius (baseline):** `AVERAGE_EARTH_RADIUS` = `EARTH_RADIUS` = **6371.0088 km** (pint).
- **Gravitational parameter (Earth):** `EARTH_GRAVITATIONAL_PARAMETER` μ = **398600.4418 km³/s²** (pint).

*Note: Standard gravitational constant G itself is not stored in this file; μ is the primary orbital parameter here.*

---

# Ellipsoid & geodesy

Source: `environment_definition/constants/EARTH.py`.

- **`pymap3d.ellipsoid.Ellipsoid.from_name("wgs84")`** — exported as **`WGS84_ELLIPSOID`** for Vincenty distances, ENU/LLA conversions, LOS helpers.
- **Geodetic helper API:** `utils/geodesics/geodesic_helpers.py` wraps pymap3d (`vincenty.vdist`, `enu2geodetic`) with pint quantities.

---

# Frames & usage

- Orbit speed uses **μ**, **mean Earth radius**, and altitude from mission constants; **surface/target sensing** uses WGS84 ellipsoid helpers (`camera_2d` Earth intersections).
- Render and LOS utilities consume `EARTH_RADIUS` / μ from shared constants (`render`, `utils/flight_geometry`, etc.).

---

# Geographic coordinates

- **Canonical triple `(lon, lat, z)`:** longitude first, latitude second (matches **`Geod.inv`**-style argument ordering historically referenced in telemetry docs). **`z`** is treated as **altitude above mean sea level** for mission-facing descriptions; episode arrays still store `sat_altitude_m` above the ellipsoid from mission altitude sampling—see `environment_definition/constants/MISSION.py` and `simulation/state_types.py`.
- **Surface distance:** `utils/geodesics/geodesic_helpers.geodesic_distance(lon1, lat1, lon2, lat2)` uses Vincenty inverse via pymap3d with **`WGS84_ELLIPSOID`** (`environment_definition/constants/EARTH.py`).
- **Camera footprint telemetry (`lon_deg`, `lat_deg`):** stored in `camera_ground_*_lon_lat_deg` (`SimulationStateSeries`) as **geodetic LOS footprint corners** when finite (`ecef2geodetic` after WGS84 ellipsoid intersections). Subsatellite columns track **`ecef2geodetic(satellite ECEF)`** from the orbit-disk mapping documented under `utils/geometry/orbit_disk_wgs84.py`.

---

# Traceability

| Quantity | Primary code |
|----------|----------------|
| R_earth, μ | `constants/EARTH.py` |
| Orbit speed | `utils/leo_adapter/orbit_geometry.py` |
