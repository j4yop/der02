# 08: Folium map rendering

**What to build:** A `map.py` module that converts a list of `ZoneRecord` into a Folium `Map` with three colored polygon overlays (red, orange, yellow), a tank marker at the source, a wind arrow, and a numeric band-distance legend.

**Blocked by:** 07

**Status:** ready-for-agent

- [ ] `src/der02/map.py` exposes `render_map(zone_records, source_lat, source_lon, wind) -> folium.Map`
- [ ] Polygons colored by severity: lethal = `#8B0000`, danger = `#FF4500`, caution = `#FFA500`
- [ ] Tank marker placed at source with a popup showing fuel name and volume
- [ ] Wind arrow (folium marker with custom icon or `PolyLine`) showing wind-from direction
- [ ] Legend in the bottom-right with band names and the maximum distance at which each band still appears
- [ ] Center of map is on source lat/lon, default zoom 14
- [ ] Returns a `folium.Map` ready for `.save("out.html")` or for use with `streamlit-folium`
- [ ] Smoke test in `tests/test_map.py`: build a small synthetic zone list, call `render_map`, assert it returns a `folium.Map` and that `.save("out.html")` writes a non-empty file