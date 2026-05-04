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

- **`pyproj.Geod(ellps="WGS84")`** — WGS 84 ellipsoid for geodetic routines when needed.
- **Geodetic helper API:** `utils/geodesics/geodesic_helpers.py` now provides:
  - point distance (`geodesic_distance`) [m],
  - forward azimuth (`geodesic_initial_bearing`) [deg],
  - geodetic bbox containment/intersection (`GeodeticBoundingBox`, `geodetic_bbox_*`) for area-target scoring.

---

# Frames & usage

- Orbit speed and mission geometry use **μ**, **Earth radius**, and altitude from mission constants.
- Render and LOS utilities consume `EARTH_RADIUS` / μ from shared constants (`render`, `utils/flight_geometry`, etc.).

---

# Geographic coordinates

- **Canonical triple `(lon, lat, z)`:** longitude first, latitude second (matches **`pyproj.Geod.inv`** / **`Geod.fwd`** argument order). **`z`** is treated as **altitude above mean sea level** for mission-facing descriptions; episode arrays still store `sat_altitude_m` above the ellipsoid from mission altitude sampling—see `environment_definition/constants/MISSION.py` and `simulation/state_types.py`.
- **Surface distance:** `utils/geodesics/geodesic_helpers.geodesic_distance(lon1, lat1, lon2, lat2)` uses the project **`geod`** (`environment_definition/constants/EARTH.py`).
- **Camera footprint telemetry (`lon_deg`, `lat_deg`):** stored in `camera_ground_*_lon_lat_deg` (`SimulationStateSeries`) as **`(LON_GLOBAL, subsatellite latitude)`** when the nadir footprint intersects Earth (`camera_ground_center_xy_km` finite). The 2D orbit-disk model does not recover distinct geodetic corners from footprint chord `(x, y)` alone; use footprint XY fields for geometry on the disk.

---

# Traceability

| Quantity | Primary code |
|----------|----------------|
| R_earth, μ | `constants/EARTH.py` |
| Orbit speed | `utils/leo_adapter/orbit_geometry.py` |
