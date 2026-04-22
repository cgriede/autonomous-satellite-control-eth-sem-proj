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

---

# Frames & usage

- Orbit speed and mission geometry use **μ**, **Earth radius**, and altitude from mission constants.
- Render and LOS utilities consume `EARTH_RADIUS` / μ from shared constants (`render`, `utils/flight_geometry`, etc.).

---

# Traceability

| Quantity | Primary code |
|----------|----------------|
| R_earth, μ | `constants/EARTH.py` |
| Orbit speed | `utils/leo_adapter/orbit_geometry.py` |
