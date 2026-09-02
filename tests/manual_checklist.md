# Manual Review Checklist

This is what an evaluator can check **without writing any code**. Every
check has a one-line description and a "what to expect" answer. If a
check fails, the project is not in a reviewable state.

## 1. Repo basics

- [ ] **Repo at `~/Desktop/der02/` has a clean git history.** Run `git log --oneline`. Expect 5+ commits labelled `ticket 01` through `ticket 10`.
- [ ] **`pip install -e ".[dev]"` succeeds** without errors.
- [ ] **`pytest -q` reports ≥ 100 tests, all passing.**
- [ ] **`ruff check src tests streamlit_app.py` reports no issues.**

## 2. The Streamlit app starts

- [ ] `streamlit run streamlit_app.py` starts without traceback.
- [ ] The browser shows three colored polygons on a map.
- [ ] The legend in the bottom-right of the map lists the three bands with distances.
- [ ] The footer contains the disclaimer "Not for life-safety decisions."

## 3. Physics responds correctly

- [ ] **Dragging the wind speed slider** changes the shape of the zones (downwind grows, upwind shrinks).
- [ ] **Dragging the wind direction slider** rotates the elongation direction.
- [ ] **Switching fuel from propane to gasoline** makes the zones grow (gasoline is denser and stores more energy per m³).
- [ ] **Switching fuel from propane to hydrogen** makes the zones shrink (hydrogen gas is much less dense at atmospheric pressure).
- [ ] **Increasing tank volume** makes zones grow.
- [ ] **Moving the tank location** updates the map (zones stay anchored to the new source).

## 4. Code review

- [ ] **`src/der02/fuels.py`** has six fuels, each with NIST WebBook URL in the source.
- [ ] **`src/der02/thresholds.py`** cites CCPS *Guidelines for CPQRA* 2nd ed. and lists the four bands (37.5 / 12.5 / 4 kW/m²; 100 / 30 / 10 kPa).
- [ ] **`src/der02/blast.py`** uses the Sachs scaled-distance formula `Z = R / (E/P₀)^(1/3)`, not the simplified `Z = R / E^(1/3)`.
- [ ] **`src/der02/blast.py`** has a comment that the TNO curve values are not primary-verified.
- [ ] **`src/der02/thermal.py`** uses the point-source formula `I = Q · τ / (4π · R²)`.
- [ ] **`src/der02/wind.py`** uses a "blow direction" (= wind-from + 180°) convention, not the raw wind-from direction.
- [ ] **`src/der02/zones.py`** orchestrates blast + thermal, taking the worst-of-two severity at each grid point.
- [ ] **`CITATIONS.md`** lists every reference used (NIST WebBook, CCPS, TNO Green Book, ALOHA).

## 5. Honesty signals

- [ ] **The disclaimer appears in the app UI.**
- [ ] **The TNO curve values are flagged as not primary-verified.**
- [ ] **Solid-flame thermal model is marked as deferred**, not implemented-and-fudged.
- [ ] **Wind distortion uses a heuristic, not real dispersion.** Real dispersion is flagged as future work.
- [ ] **Every module has a docstring citing its source.**

## 6. Test quality

- [ ] `pytest -q tests/test_blast.py` includes a test that fails if `math.isclose(rel=...)` is used (the bug we hit during development).
- [ ] `pytest -q tests/test_wind.py` includes a test that fails if the wind angle convention is wrong.
- [ ] `pytest -q tests/test_zones.py` includes a test that fails if the source-point distance is not handled.

## What "fail" means

Any unchecked item is a real problem. Don't accept "looks fine" as a
substitute for a check.