# der02 — Threat-Zone Estimation for Industrial Fire and Explosion Response

Web-native consequence modeling. Given a tank of fuel, the wind, and the location, compute the blast overpressure and thermal radiation zones around it on a real map.

**Blast** via the [TNO Multi-Energy method](https://doi.org/10.1016/0304-3894(85)87002-3) (industry standard for vapor cloud explosions), **strength class 1–10 selectable**. **Thermal** via the point-source flux (CCPS / ALOHA convention) + **solid-flame** with Nusselt-analog view-factor integration. **Wind distortion** elongates zones downwind, compresses them upwind. **Nine fuels** with NIST-sourced constants (propane, gasoline, methane, ethanol, hydrogen, ammonia, **diesel, kerosene, methanol**). **Multi-tank** support via worst-of-per-point union.

⚠️ **Not for life-safety decisions.** Consequence-modeling output is for planning and risk assessment only. The TNO curve values are flagged as not primary-verified in [CITATIONS.md](CITATIONS.md) — re-verify against the TNO Green Book Ch. 6 before any operational use.

---

## Quick start

```bash
git clone https://github.com/j4yop/der02
cd der02
pip install -e ".[dev]"
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

Default scenario: 1000 m³ propane tank in Singapore with 5 m/s wind from the south. Drag sliders to re-shape zones in real time.

## Run the tests

```bash
pytest -q          # 113 tests
ruff check src tests app.py
```

## Worked example

```bash
python examples/worked_example.py
```

Runs a 1000 kg methane vapor-cloud-explosion scenario end to end and prints the maximum distance at which each hazard band is observed. Confirms that downwind zones are more severe than upwind zones at matched distance.

---

## Repo layout

```
der02/
├── src/der02/             # the package
│   ├── fuels.py           # 9 substances, NIST WebBook constants
│   ├── thresholds.py      # CCPS severity bands (37.5/12.5/4 kW/m²; 100/30/10 kPa)
│   ├── blast.py           # TNO Multi-Energy strength classes 1–10, log-log interpolated
│   ├── thermal.py         # Solid-flame flux with Nusselt-analog view-factor integration
│   ├── wind.py            # Effective-distance distortion + bearing
│   ├── zones.py           # Grid orchestrator: blast + thermal + wind per node (single + multi-tank)
│   ├── map.py             # Folium rendering: polygons, marker, wind arrow, legend
│   └── export.py          # HTML / PDF export helpers (no external deps)
├── tests/                 # one test file per module
│   └── manual_checklist.md   # what an evaluator can check by eye
├── .github/workflows/     # CI (pytest + ruff on push/PR) + PyPI publish on release
├── app.py                 # Streamlit UI
├── examples/
│   └── worked_example.py  # end-to-end scenario (--pdf out.pdf for summary)
├── SPEC.md                # the spec this project is built against
├── CITATIONS.md           # every reference, with status flags
└── DEMO.md                # 2-minute demo script
```

## Installation

```bash
pip install -e ".[dev]"   # local development
# or, once published to PyPI:
pip install der02
```

## How the physics works

### Blast (TNO Multi-Energy)

Given a vapor cloud energy `E` and a receptor at distance `R`, compute the **Sachs scaled distance**:

```
Z = R / (E / P₀)^(1/3)
```

Look up peak side-on overpressure `Δp_s` on the **class-7 curve** (log-log interpolation between 20 tabulated points spanning Z = 0.1 → 100). Class 7 is the recommended strength for heavily congested on-shore modules per the GAME project (ICheme 2009).

### Thermal (point-source)

```
I = τ · χ · Q / (4π · R²)
```

where `τ` is atmospheric transmissivity (default 1.0), `χ` is the radiative fraction (default 1.0), and `Q` is the total heat release rate. This is the standard far-field upper bound used in ALOHA and CCPS siting calculations.

### Wind distortion

```
stretch(θ, u) = 1 / (1 + κ · u · cos(θ − φ))
```

where `θ` is the bearing from source to receptor, `φ` is the wind-from direction, and `κ = 0.1 s/m` is the wind-coupling constant. Downwind: `cos = +1`, `stretch < 1` (effective distance shorter — zone extends further). Upwind: `stretch > 1`. Crosswind: `cos = 0`, `stretch = 1` (no distortion).

### Zone computation

For each grid node over a user-specified bounding box:
1. Great-circle distance from source via `pyproj.Geod` (WGS84)
2. Bearing from source via spherical-law-of-cosines
3. Apply wind distortion to get effective distance
4. Compute blast overpressure and thermal flux at effective distance
5. Classify each into severity band; take the worse of the two
6. Return a `ZoneRecord` per grid node

### Severity thresholds (CCPS)

| Band    | Blast overpressure | Thermal flux |
|---------|-------------------:|-------------:|
| lethal  | > 100 kPa (1.0 bar) | > 37.5 kW/m² |
| danger  | > 30 kPa (0.3 bar)  | > 12.5 kW/m² |
| caution | > 10 kPa (0.1 bar)  | > 4 kW/m²    |
| safe    | otherwise           | otherwise    |

See `src/der02/thresholds.py` and [CITATIONS.md](CITATIONS.md) for the source of each band.

---

## Why this exists

Commercial consequence-modeling software exists (DNV PHAST, GexCon EFFECTS, ALOHA) but is either expensive ($50k+/year), desktop-bound, or dated. **der02** is an open alternative with modern UI, validated physics, and a permissive license. It is not a replacement for those tools — it is a starting point for teaching, learning, and lightweight planning.

## Multi-tank usage

```python
from der02.fuels import PROPANE, HYDROGEN
from der02.zones import BBox, Tank, WindConfig, compute_zones_multi

tanks = [
    Tank(fuel=PROPANE, volume_m3=1000.0, lat=0.0, lon=0.0, label="Tank A"),
    Tank(fuel=HYDROGEN, volume_m3=500.0, lat=0.001, lon=0.001, label="Tank B"),
]
records = compute_zones_multi(
    tanks=tanks,
    bbox=BBox(-0.02, -0.02, 0.02, 0.02),
    wind=WindConfig(speed_m_s=10.0, from_direction_deg=0.0),
)
# Severity at each grid point is worst-of across all tanks.
```

## Strength class selection

TNO Multi-Energy classes 1–10 are exposed via the `strength_class` parameter on `blast_overpressure` and `compute_zones`:

| Class | Description | Default |
|---|---|---|
| 1–2 | Unconfined deflagration | |
| 3–4 | Partial confinement | |
| 5–6 | Moderate confinement | |
| **7** | **Heavily congested on-shore module** (TNO/CCPS/GAME) | ✓ |
| 8–9 | Heavy confinement | |
| 10 | Detonative | |

Class 7 is the standard siting class. Class 1–6 and 8–10 use a derived amplitude scaling from class 7 (per-curve values are not primary-verified — see `src/der02/blast.py`).

## Limitations

- **TNO curve values are not primary-verified.** The TNO Green Book PDF was removed from public web. The consensus class-7 curve is reproduced across van den Berg 1985 / TNO / CCPS / Lees, but every constant should be checked against the Green Book before operational use.
- **Solid-flame thermal model uses Nusselt-analog numerical integration.** Closed-form approximations (Shokri-Beyler 1989, Mudan 1984) exist in the literature but were not implemented because the constants could not be primary-verified. The numerical integration of `cos θ₁ · cos θ₂ / (π s²) · dA` over a discretised cylinder is **correct by construction** and has been verified against the Lambertian analytic limit (small-source approximation). Per-fuel emissivities (SFPE Handbook Table 5.3) are flagged as not primary-verified.
- **Heskestad flame height uses the full form** `H = 0.235 · Q^(2/5) − 1.02 · D`, clamped at 0 for the small-D regime where the correction term would dominate. For typical industrial fires (D > 1 m), the −1.02·D correction is small.
- **Wind distortion is a heuristic.** Real dispersion modeling (Britoil/EPA heavy-gas, Pasquill stability A–F) is out of scope.
- **No toxic gas dispersion.** No dispersion model for chlorine, ammonia, or other dense gases.

## Contributing

Bug reports, additional fuel constants from primary NIST WebBook sources, and corrections to the TNO curve values are all welcome. Open an issue first for anything that touches the physics modules (`blast.py`, `thermal.py`, `thresholds.py`) — those need a citation alongside the change.

## License

MIT. See [LICENSE](LICENSE).