"""Streamlit app: der02 threat-zone estimator.

Run with:
    streamlit run app.py

The app is a thin UI layer over the der02 physics modules. It does
NOT contain any physics — only orchestration, sliders, and rendering.

UI layout
---------
- Sidebar (left): fuel selectbox, tank volume slider, wind speed slider,
  wind direction slider, bounding box latitude/longitude selectors.
- Main panel: folium map with zone polygons, wind arrow, legend, and
  numeric summary of band distances.
- Footer: disclaimer.
"""

from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium

from der02.fuels import FUELS, get_fuel
from der02.map import MapRequest, render_map
from der02.zones import BBox, WindConfig, compute_zones

# Default starting location: Singapore, near the equator.
DEFAULT_LAT: float = 1.29
DEFAULT_LON: float = 103.85

# Half-extent of the modelling box in degrees latitude/longitude.
# 0.02° ≈ 2.2 km.
BOX_HALF_EXTENT: float = 0.02

# Default resolution: 100 m. Re-renders complete in well under 2 s
# for a ~4 km × 4 km box at 100 m resolution (~1600 records).
DEFAULT_RESOLUTION_M: float = 100.0

DISCLAIMER: str = (
    "Not for life-safety decisions. "
    "Consequence-modeling output is for planning and risk assessment only. "
    "Values rely on the TNO Multi-Energy class-7 blast curve and the "
    "point-source thermal model; both should be re-verified against "
    "primary references (TNO Green Book, CCPS *Guidelines for CPQRA*) "
    "before any operational use."
)


st.set_page_config(
    page_title="der02 — Threat Zone Estimator",
    layout="wide",
)

st.title("der02 — Threat-Zone Estimator")
st.caption(
    "Industrial fire and explosion consequence modelling. "
    "TNO Multi-Energy blast + point-source thermal, with wind distortion."
)

# ── Sidebar controls ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Tank")

    fuel_name = st.selectbox(
        "Fuel",
        options=sorted(FUELS.keys()),
        index=sorted(FUELS.keys()).index("propane"),
        help="Substance stored in the tank.",
    )
    fuel = get_fuel(fuel_name)

    volume_m3 = st.slider(
        "Tank volume (m³)",
        min_value=10,
        max_value=10_000,
        value=1000,
        step=10,
        help="Tank volume in cubic metres.",
    )

    st.header("Wind")
    wind_speed = st.slider(
        "Wind speed (m/s)",
        min_value=0.0,
        max_value=20.0,
        value=5.0,
        step=0.5,
        help="10 m standard anemometer height.",
    )
    wind_from = st.slider(
        "Wind from direction (°)",
        min_value=0,
        max_value=359,
        value=180,
        step=1,
        help="Where the wind is coming FROM, degrees clockwise from North.",
    )

    st.header("Location")
    source_lat = st.number_input(
        "Tank latitude (°)",
        min_value=-90.0,
        max_value=90.0,
        value=DEFAULT_LAT,
        step=0.01,
    )
    source_lon = st.number_input(
        "Tank longitude (°)",
        min_value=-180.0,
        max_value=180.0,
        value=DEFAULT_LON,
        step=0.01,
    )

    st.header("Grid")
    resolution = st.slider(
        "Resolution (m)",
        min_value=50,
        max_value=500,
        value=int(DEFAULT_RESOLUTION_M),
        step=50,
    )

# ── Compute zones ─────────────────────────────────────────────────────
bbox = BBox(
    min_lat=source_lat - BOX_HALF_EXTENT,
    min_lon=source_lon - BOX_HALF_EXTENT,
    max_lat=source_lat + BOX_HALF_EXTENT,
    max_lon=source_lon + BOX_HALF_EXTENT,
)
wind = WindConfig(speed_m_s=wind_speed, from_direction_deg=float(wind_from))

records = compute_zones(
    fuel=fuel,
    volume_m3=float(volume_m3),
    source_lat=source_lat,
    source_lon=source_lon,
    bbox=bbox,
    wind=wind,
    resolution_m=float(resolution),
)

# ── Render map ────────────────────────────────────────────────────────
fmap = render_map(
    records=records,
    request=MapRequest(
        source_lat=source_lat,
        source_lon=source_lon,
        source_label=f"{fuel_name.title()} {volume_m3:.0f} m³",
        wind=wind,
    ),
)

st_folium(fmap, width=None, height=600, returned_objects=[])

# ── Numeric summary ──────────────────────────────────────────────────
st.subheader("Band distances")
order = ["lethal", "danger", "caution"]
cols = st.columns(3)
for i, severity in enumerate(order):
    band = [r for r in records if r.severity == severity]
    if band:
        max_d = max(r.distance_m for r in band)
        cols[i].metric(
            label=severity.capitalize(),
            value=f"{max_d:.0f} m",
        )
    else:
        cols[i].metric(label=severity.capitalize(), value="—")

# ── Footer / disclaimer ───────────────────────────────────────────────
st.markdown("---")
st.caption(DISCLAIMER)
