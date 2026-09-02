# der02 — Demo Script (2 minutes)

Run the app:
```bash
cd ~/Desktop/der02
source .venv/bin/activate   # or: conda activate base (already has deps)
streamlit run streamlit_app.py
```

Open `http://localhost:8501`.

## Demo flow (read aloud)

### 1. Open with the defaults (~30 s)

> "Here is der02 — a threat-zone estimator for industrial fire and explosion response. Default is a 1000 m³ propane tank in Singapore with 5 m/s wind from the south."

Point at:
- the three colored polygons on the map (red = lethal, orange = danger, yellow = caution)
- the legend in the bottom-right (max distance per band)
- the metric row below the map (lethal 612 m, danger 1050 m, caution 1900 m)
- the wind arrow north of the source (wind blowing from S to N)
- the disclaimer in the footer

### 2. Drag the wind speed slider to 15 m/s (~30 s)

> "Watch what happens. The downwind side of every band stretches further; the upwind side compresses."

Specifically:
- danger band on the south side shrinks (upwind → compressed)
- danger band on the north side grows (downwind → elongated)

### 3. Switch fuel to hydrogen (~30 s)

> "Hydrogen has 2.6× the energy per kilogram of propane but is 23× less dense as a gas. So at the same tank volume, the *mass* participating is much smaller, and zones are smaller."

Switch it back to propane after.

### 4. Show a heavier-than-air release (~30 s)

> "Switch to gasoline — denser than air, more mass per cubic metre, larger zones."

Demonstrate:
- fuel = gasoline, volume = 5000 m³
- zones visibly grow
- the legend max distances increase

### 5. Move the tank to a recognisable location (~30 s)

> "Let me move the tank to the equator — a coastal facility. The map redraws in real time."

Set lat = 0.0, lon = 0.0.

### Wrap-up (~30 s)

> "der02 ships with the TNO Multi-Energy blast model, the point-source thermal flux, a wind distortion factor, and six fuels from NIST WebBook. The disclaimer is real: this is for planning, not life-safety. The TNO curve values are flagged as not primary-verified in `CITATIONS.md` — they need to be checked against the Green Book before any operational use. Source code is in `src/der02/`, tests in `tests/`, and the worked example in `examples/worked_example.py`."

## What to watch for during demo

- **Re-render time.** With 50 m resolution and a 4 km box, every slider change should re-render in < 2 s.
- **Wind effect.** The downwind zone must visibly grow; upwind must visibly shrink.
- **Fuel effect.** Switching from gasoline to hydrogen must produce smaller zones (density dominates).
- **Disclaimer.** Must be visible at all times in the footer.

## Common failure modes

| Symptom | Cause | Fix |
|---|---|---|
| App shows blank map | streamlit-folium version mismatch | `pip install -U streamlit-folium` |
| Long re-render times | Resolution too fine | Set resolution to ≥ 100 m |
| Zones look like a square | Default box at equator | Move lat/lon away from 0/0 |
| Zones don't change with wind | Old code path; check `effective_distance` returns differ for ±bearing | Run `pytest -q tests/test_wind.py` |