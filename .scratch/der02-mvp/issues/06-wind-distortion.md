# 06: Wind distortion

**What to build:** A `wind.py` module that, given wind speed (m/s), wind-from direction (degrees from north), source location (lat, lon), and a receptor location (lat, lon), returns an effective distance multiplier such that zones elongate downwind and compress upwind.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `src/der02/wind.py` exposes `effective_distance(distance_m, bearing_to_receptor_deg, wind_from_direction_deg, wind_speed_m_s) -> distance_m`
- [ ] Downwind (receptor on the downwind side of source relative to wind direction): effective distance < real distance (compressed)
- [ ] Upwind: effective distance > real distance (elongated hazard extends further downwind)
- [ ] Crosswind (perpendicular): effective distance ≈ real distance (small adjustment)
- [ ] No-wind case (`wind_speed_m_s == 0`): returns real distance unchanged
- [ ] Tests in `tests/test_wind.py`:
  - Pure downwind, wind 5 m/s: effective < real
  - Pure upwind, wind 5 m/s: effective > real
  - Crosswind: effective ≈ real (within 10%)
  - Wind 0: returns real unchanged
- [ ] Module docstring states the heuristic and cites a reference (CCPS or TNO wind correction)