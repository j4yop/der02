# 07: Zone computation across a grid

**What to build:** A `zones.py` orchestrator that takes a `Fuel`, a tank volume, a wind config, and a bounding box (lat/lon corners + resolution), and returns a list of zone records `(lat, lon, band, blast_pa, thermal_kw_m2)`. Pure-Python, no Folium dependency yet.

**Blocked by:** 02, 04, 05, 06

**Status:** ready-for-agent

- [ ] `src/der02/zones.py` exposes `compute_zones(fuel, volume_m3, wind, bbox, resolution_m) -> list[ZoneRecord]`
- [ ] `ZoneRecord` is a dataclass with `lat`, `lon`, `severity`, `blast_pa`, `thermal_kw_m2`
- [ ] Energy for blast: `mass = volume * vapor_density` (or fuel mass equivalent); `energy_j = mass * heat_of_combustion_kj_kg * 1000` (uses stoichiometric combustion energy). Combustion efficiency 0.4 default (typical for vapor cloud).
- [ ] For each grid node: compute great-circle distance to source; compute wind-corrected distance; compute blast overpressure and thermal flux; classify both into bands; record worst-of-two severities
- [ ] Bounding box iteration uses pyproj for meter-accurate grid spacing at the relevant latitude
- [ ] Tests in `tests/test_zones.py`:
  - At the source point (distance ~0), severity is lethal
  - At very large distance (>>10 km), severity is safe
  - With wind, the lethal/danger zone is larger downwind than upwind
  - With zero wind, zones are radially symmetric
- [ ] Resolutions of 50 m produce a tractable record count for a 5 km × 5 km box (<15,000 records)