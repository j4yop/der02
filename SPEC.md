# der02 — Threat-Zone Estimation for Industrial Fire and Explosion Response

Consequence-modeling software: given a tank, fuel, and wind, compute blast overpressure and thermal radiation zones around it on a real map.

## Problem Statement

People planning emergency response or facility siting around hazardous-material storage (LPG, gasoline, LNG, hydrogen, ammonia) need to know what distance from a tank is dangerous, why, and by how much. Existing tools (DNV PHAST, GexCon EFFECTS, ALOHA) are either expensive ($50k+/yr), desktop-bound and dated (ALOHA), or require specialized training to operate. A web-native, open alternative that implements the same validated physics (TNO Multi-Energy, solid-flame radiation) does not exist.

## Solution

A Python package + Streamlit web app. The user drops a pin on a map, picks a fuel, sets wind. The app returns three graded hazard bands (lethal / danger / caution) for both blast overpressure and thermal radiation, drawn as filled polygons on OpenStreetMap. The shape responds to wind in real time.

## User Stories

1. As an HSE consultant, I want to place a single tank on a map by clicking, so that I can model a specific facility quickly.
2. As an HSE consultant, I want to choose from a library of common fuels (LPG, gasoline, LNG, methane, ethanol, hydrogen, ammonia), so that I can model the substance the client actually stores.
3. As an HSE consultant, I want to set wind speed (m/s) and direction (degrees from north), so that I can model current or forecast conditions.
4. As an HSE consultant, I want to see blast overpressure zones and thermal radiation zones as separate, color-graded polygons on the same map, so that I can see both hazards at once.
5. As an HSE consultant, I want the danger band to be split into at least three severity levels (lethal / danger / caution), so that I can advise different actions at each distance.
6. As an HSE consultant, I want zones to elongate downwind and compress upwind, so that the result is physically realistic.
7. As an HSE consultant, I want to drag the wind slider and see the zones re-shape in real time, so that I can show a client how wind direction changes the risk picture.
8. As an HSE consultant, I want to see numeric distances (in meters) for each band, so that I can quote them in a report.
9. As an HSE consultant, I want to change the fuel and see the zones change shape, so that I can compare substance risks.
10. As an insurance risk engineer, I want to export the result as a PDF or PNG, so that I can attach it to an underwriting file.
11. As a university student, I want every threshold (e.g. "12.5 kW/m² = second-degree burns in 30s") to be cited to its source, so that I can verify the physics.
12. As an open-source contributor, I want a clean Python package layout with TDD, so that I can add new fuels or models confidently.
13. As a code reviewer, I want unit tests for every physics function with known analytic answers, so that I can trust the implementation.
14. As a fire service planner, I want to see the zones overlaid on OpenStreetMap, so that I can identify real landmarks (buildings, roads) inside the danger bands.
15. As a fire service planner, I want the app to display a disclaimer that the output is not for life-safety decisions, so that misuse is constrained.

## Implementation Decisions

- **Stack:** Python 3.12, numpy, scipy, shapely, geopandas, pyproj, folium, streamlit, streamlit-folium. pytest for tests. uv for dependency management. Prettier.
- **Layout:** single repo. `src/der02/` package containing physics modules, fuel library, and zone computation. `streamlit_app.py` at the root is the Streamlit entry point; `api.py` + `public/index.html` is the FastAPI + static frontend for Vercel. `tests/` mirroring `src/der02/`.
- **Package modules:**
  - `src/der02/fuels.py` — fuel library (dataclass-per-fuel with constants sourced from NIST WebBook and CCPS).
  - `src/der02/blast.py` — TNO Multi-Energy blast overpressure model. Pure function `(distance, energy, ambient_pressure) -> overpressure_pa`.
  - `src/der02/thermal.py` — solid-flame thermal radiation model. Pure function `(distance, heat_release_rate, flame_height) -> flux_kw_m2`.
  - `src/der02/wind.py` — wind distortion. Returns effective distance multiplier given wind speed, wind direction, and bearing from source to point.
  - `src/der02/zones.py` — orchestrates blast + thermal across a grid. Returns a list of `(point, band)` records.
  - `src/der02/thresholds.py` — concentration / flux / overpressure thresholds with citations.
  - `src/der02/map.py` — converts zone records to folium polygons.
- **Testing seam:** the highest seam. Tests target `blast.py`, `thermal.py`, `wind.py`, `thresholds.py` as pure functions. One integration test exercises `zones.py` against a hand-computed case. The Streamlit UI is not unit-tested.
- **Citations:** every constant and threshold lives next to its source in a comment or docstring. A `CITATIONS.md` at the repo root lists all references (TNO Green Book Chapter 6, CCPS *Guidelines for Chemical Process Quantitative Risk Analysis* 2nd ed., API RP 521, NIST WebBook).
- **Disclaimer:** the app footer reads "Not for life-safety decisions. Consequence modeling output is for planning and risk assessment only."
- **Fuel library (MVP):** propane (LPG), gasoline, methane (LNG), ethanol, hydrogen, ammonia. Six substances. Values from NIST WebBook, cross-checked against CCPS.
- **Out of scope (MVP):** multi-tank union, dispersion (toxic gas clouds), jet flames, BLEVE, building damage, weather stability classes (Pasquill A–F), authentication, saved scenarios, payments, mobile-native UI.
- **Out of scope (v1, listed for clarity):** Multi-Energy strength class selection UI, conditional probability / risk integral, dose calculations, GIS shapefile import/export beyond PNG/PDF.

## Testing Decisions

- **What makes a good test:** a test asserts an externally observable property (a known pressure at a known distance, a known flux at a known range) using values from a cited reference. Tests do not assert internal variable names or implementation order. If the function were rewritten with the same model but different internals, the test should still pass.
- **Modules tested:** every module in `src/der02/`. The Streamlit layer (`streamlit_app.py`) is tested by manual demo only.
- **Prior art:** for each physics function we cite at least one textbook example or worked problem (e.g. TNO Green Book worked example, CCPS sample calculation) and write a test that asserts our function reproduces the textbook answer to within 5%.
- **TDD discipline:** for each module, write the failing test first, then implement the function, then refactor.

## Out of Scope

- Multi-tank facility layouts (v1.5).
- Toxic gas dispersion (LPG cloud, ammonia cloud, chlorine).
- BLEVE / fireball modeling.
- Building / equipment damage curves (BST model).
- Real-time weather API integration.
- Auth, saved scenarios, user accounts.
- Mobile-native app.
- 3D visualization.

## Further Notes

- **Validation liability:** this is a portfolio/learning project. The disclaimer in the UI is non-negotiable. Do not soften it.
- **Why TNO over TNT-equivalent:** TNO is what PHAST and EFFECTS use. TNT-equivalent is widely discredited in the blast-safety literature (it over-predicts far-field and under-predicts near-field). A reviewer who knows the field will recognize TNT-equivalent as a "did not read the source" signal. TNO is the right choice even though it's more code.
- **Why Streamlit over Flask:** the killer demo is "drag the wind slider, see the zones rotate." Streamlit ships that in 50 lines of Python. Flask + JS gets there eventually but adds a frontend that distracts from the physics.
- **Why folium over Mapbox/MapLibre:** folium is one dependency, no API token, works offline-ish with downloaded tiles. MapLibre later for the v1 polish.