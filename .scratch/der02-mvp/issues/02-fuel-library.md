# 02: Fuel library with cited constants

**What to build:** A fuel library that exposes six substances (propane/LPG, gasoline, methane/LNG, ethanol, hydrogen, ammonia) with their physical constants and a defensive default that raises if an unknown fuel is requested. Every constant is sourced from NIST WebBook or CCPS.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `src/der02/fuels.py` defines a `Fuel` dataclass with: `name`, `formula`, `heat_of_combustion_kj_kg`, `flame_temperature_k`, `vapor_density_kg_m3` (optional, None for gases that don't pool)
- [ ] A module-level `FUELS` dict maps `"propane"` / `"gasoline"` / `"methane"` / `"ethanol"` / `"hydrogen"` / `"ammonia"` to `Fuel` instances
- [ ] Each `Fuel` has a docstring citing its source (NIST WebBook URL or CCPS table reference)
- [ ] `get_fuel(name)` returns the `Fuel` or raises `KeyError` with a clear message
- [ ] Tests in `tests/test_fuels.py` assert: each fuel is retrievable; `get_fuel("water")` raises; `heat_of_combustion_kj_kg` for propane is ~46,000 kJ/kg (NIST reference value within 5%); same for hydrogen ~120,000 kJ/kg
- [ ] `pytest -q tests/test_fuels.py` passes