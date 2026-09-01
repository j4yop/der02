# der02 — Threat-Zone Estimation

Web-native consequence modeling for industrial fire and explosion response. Place a tank, pick a fuel, set the wind, get back three graded hazard bands (lethal / danger / caution) for both blast overpressure and thermal radiation, drawn on OpenStreetMap.

## What it is

- **Blast overpressure** via the TNO Multi-Energy method (industry standard for vapor cloud explosions).
- **Thermal radiation** via the solid-flame model (CCPS formulation).
- **Wind distortion** that elongates zones downwind and compresses them upwind.
- A **Streamlit** web app with sliders and a live map.

## What it is not

- Not for life-safety decisions. Output is for planning and risk assessment only.
- Not a CFD solver. Consequence distances are computed using validated empirical models.
- Not a replacement for DNV PHAST, GexCon EFFECTS, or ALOHA. Those are professional tools used by safety engineers. `der02` is an open alternative for teaching, learning, and lightweight planning.

## Run the app

```bash
pip install -e ".[dev]"
streamlit run app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501).

## Run the tests

```bash
pytest -q
ruff check src tests
```

## Repo layout

```
src/der02/      # the package
  fuels.py      # fuel library (constants from NIST WebBook / CCPS)
  blast.py      # TNO Multi-Energy blast overpressure
  thermal.py    # solid-flame thermal radiation
  wind.py       # wind distortion
  zones.py      # grid orchestrator
  thresholds.py # blast and thermal severity bands with citations
  map.py        # folium rendering
app.py          # Streamlit entry point
tests/          # one test file per module
SPEC.md         # the spec this project is built against
CITATIONS.md    # every reference used in code
```

## Status

Early. See `SPEC.md` and `.scratch/der02-mvp/issues/` for the planned ticket sequence.