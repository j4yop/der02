# 05: Solid-flame thermal radiation model

**What to build:** A pure-function `thermal_flux(distance_m, heat_release_rate_kw, flame_height_m) -> flux_kw_m2` implementing the solid-flame radiation model. View-factor calculation. Returns kW/m².

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] `src/der02/thermal.py` exposes `thermal_flux(distance_m, heat_release_rate_kw, flame_height_m)`
- [ ] Computes view factor F from flame cylinder to receptor at ground distance R (Shokri-Beyler or Mudan formulation)
- [ ] Applies Stefan-Boltzmann with emissivity 1.0 and flame temperature (passed in or defaulted from fuel)
- [ ] Raises `ValueError` on negative inputs
- [ ] Module docstring cites CCPS *Guidelines for CPQRA* Chapter 2 (thermal radiation) and identifies the source formula
- [ ] Tests in `tests/test_thermal.py`:
  - Monotonicity: flux decreases with distance
  - At R = 0 (receptor at flame surface), flux equals σ·T⁴ (within 10% — view factor approaches 1)
  - Doubling heat release rate at fixed R doubles flux (radiative, linear in Q)
  - Validation: negative distance raises
- [ ] Citations added to `CITATIONS.md`