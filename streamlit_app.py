"""Streamlit app: der02 threat-zone estimator.

Run with:
    streamlit run streamlit_app.py

The app is a thin UI layer over the der02 physics modules. It does
NOT contain any physics — only orchestration, sliders, and rendering.

UI layout
---------
- Sidebar (left): fuel, tank volume, wind speed/direction, location,
  grid resolution, advanced thermal controls (emissivity override,
  transmissivity, tank dimensions).
- Main panel: folium map with zone polygons, wind arrow, legend, and
  numeric summary of band distances.
- Footer: disclaimer.
"""

from __future__ import annotations

import io
import math

import streamlit as st
from streamlit_folium import st_folium

from der02.export import html_to_pdf_bytes
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
    "Values rely on the TNO Multi-Energy blast curve and the "
    "solid-flame thermal model with Nusselt-analog view-factor "
    "integration. The TNO curve values and per-fuel emissivities are "
    "flagged as not primary-verified in CITATIONS.md — re-verify against "
    "primary references (TNO Green Book, SFPE Handbook, CCPS *Guidelines "
    "for CPQRA*) before any operational use."
)


st.set_page_config(
    page_title="der02 — Threat Zone Estimator",
    layout="wide",
)

st.title("der02 — Threat-Zone Estimator")
st.caption(
    "Industrial fire and explosion consequence modelling. "
    "TNO Multi-Energy blast + solid-flame thermal (Nusselt view-factor), "
    "with wind distortion."
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

    # Default tank diameter from volume (cylinder, H=D).
    default_diameter = (4.0 * 1000.0 / math.pi) ** (1.0 / 3.0)

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

    st.header("Blast")
    strength_class = st.slider(
        "TNO strength class",
        min_value=1,
        max_value=10,
        value=7,
        step=1,
        help="TNO Multi-Energy strength class: 1=unconfined deflagration, "
        "10=highly confined/detonative. Class 7 is the standard siting "
        "class for 'heavily congested on-shore module' per TNO/CCPS/GAME. "
        "Values for non-7 classes are derived by amplitude scaling from "
        "class 7 and are not primary-verified.",
    )

    # Advanced controls — collapsed by default. Users who don't open
    # this section get the fuel-aware defaults.
    with st.expander("Advanced thermal", expanded=False):
        use_fuel_emissivity = st.checkbox(
            "Use fuel emissivity",
            value=True,
            help="If checked, emissivity comes from the Fuel object "
            "(NIST-sourced, SFPE Handbook Table 5.3, not primary-verified).",
        )
        emissivity = st.slider(
            "Flame emissivity",
            min_value=0.0,
            max_value=1.0,
            value=fuel.emissivity,
            step=0.05,
            disabled=use_fuel_emissivity,
            help="Luminous fraction of the flame. CCPS Ch. 2 default 0.4.",
        )
        transmissivity = st.slider(
            "Atmospheric transmissivity",
            min_value=0.0,
            max_value=1.0,
            value=1.0,
            step=0.05,
            help="Path-length / humidity correction. Default 1.0 (no loss).",
        )
        combustion_efficiency = st.slider(
            "Combustion efficiency",
            min_value=0.05,
            max_value=1.0,
            value=0.4,
            step=0.05,
            help="Fraction of fuel energy participating in the blast. "
            "CCPS / TNO typical 0.4 for partially confined VCE; "
            "higher for highly confined or detonative cases.",
        )
        override_tank = st.checkbox(
            "Override tank dimensions",
            value=False,
            help="By default tank diameter is derived from volume. "
            "Tick to override.",
        )
        tank_diameter_m = st.number_input(
            "Tank diameter (m)",
            min_value=0.5,
            max_value=100.0,
            value=default_diameter,
            step=0.5,
            disabled=not override_tank,
        )
        tank_height_m = st.number_input(
            "Tank height (m)",
            min_value=0.5,
            max_value=100.0,
            value=default_diameter,
            step=0.5,
            disabled=not override_tank,
        )

# ── Apply advanced-control logic ──────────────────────────────────────
eff_emissivity = fuel.emissivity if use_fuel_emissivity else float(emissivity)
eff_diameter = float(tank_diameter_m) if override_tank else None
eff_height = float(tank_height_m) if override_tank else None

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
    tank_diameter_m=eff_diameter,
    tank_height_m=eff_height,
    transmissivity=float(transmissivity),
    combustion_efficiency=float(combustion_efficiency),
    strength_class=int(strength_class),
)
# Note: emissivity override isn't a parameter on compute_zones (it
# uses fuel.emissivity directly). For the advanced-override case we
# post-process the records by re-running the thermal calc — but for
# MVP we use the fuel emissivity regardless of the slider setting
# (the slider is informational until the orchestrator takes a parameter).
# This is flagged in the code as a known limitation.
if not use_fuel_emissivity:
    from der02.thermal import flame_height_heskestad, solid_flame_flux
    mass_kg = float(volume_m3) * fuel.vapor_density_kg_m3
    hrr_kw = mass_kg * fuel.lhv_kj_kg * 1000.0 / 600.0
    h = max(flame_height_heskestad(hrr_kw, eff_diameter or 10.0), 1.0)
    for r in records:
        r.thermal_kw_m2 = solid_flame_flux(
            distance_m=max(r.distance_m, 0.1),
            flame_height_m=h,
            flame_diameter_m=eff_diameter or 10.0,
            flame_temperature_k=fuel.flame_temperature_k,
            emissivity=eff_emissivity,
            transmissivity=float(transmissivity),
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

# ── Export ──────────────────────────────────────────────────────────
st.subheader("Export")
export_col1, export_col2 = st.columns(2)

# Render the folium map to HTML bytes for download.
_html_buffer = io.BytesIO()
fmap.save(_html_buffer, close_file=False)
_html_str = _html_buffer.getvalue().decode("utf-8")

with export_col1:
    st.download_button(
        label="Download map HTML",
        data=_html_str.encode("utf-8"),
        file_name="der02_map.html",
        mime="text/html",
        help="Open the file in a browser, then use the browser's "
        "print-to-PDF for a rendered PDF. This is the supported "
        "export path (no headless-browser dependency required).",
    )

with export_col2:
    _pdf_bytes = html_to_pdf_bytes(_html_str)
    st.download_button(
        label="Download map PDF (text-only)",
        data=_pdf_bytes,
        file_name="der02_map.pdf",
        mime="application/pdf",
        help="Text-only PDF containing the HTML source. For a rendered "
        "map PDF, use the HTML download and the browser's print-to-PDF.",
    )

# ── Footer / disclaimer ───────────────────────────────────────────────
st.markdown("---")
st.caption(DISCLAIMER)
