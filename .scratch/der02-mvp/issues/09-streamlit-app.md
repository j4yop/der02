# 09: Streamlit demo app

**What to build:** A `app.py` at the repo root that runs `streamlit run app.py` and gives the user: a fuel dropdown, a tank volume slider, a wind speed slider, a wind direction compass, and the live Folium map with zones that re-render on every interaction. Footer disclaimer visible.

**Blocked by:** 02, 03, 06, 07, 08

**Status:** ready-for-agent

- [ ] `app.py` uses `streamlit` and `streamlit-folium`
- [ ] Sidebar: fuel selectbox (6 options from `FUELS`), volume slider (10–10,000 m³), wind speed slider (0–20 m/s), wind direction compass (0–360°)
- [ ] Main panel: `st_folium` rendering the result of `compute_zones` → `render_map`
- [ ] Footer: explicit disclaimer "Not for life-safety decisions. Consequence modeling output is for planning and risk assessment only."
- [ ] Numeric summary below map: distance to outer edge of each band
- [ ] Smoke run: `streamlit run app.py` starts cleanly; changing the wind slider re-renders zones visibly within 2 seconds for a 50 m resolution over a 5 km box
- [ ] No new physics code in `app.py` — only orchestration of the existing modules