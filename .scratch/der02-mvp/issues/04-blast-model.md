# 04: TNO Multi-Energy blast model

**What to build:** A pure-function `blast_overpressure(distance_m, energy_joules, ambient_pressure_pa=101325) -> overpressure_pa` implementing the TNO Multi-Energy method (Sachs-scaled-distance lookup with strength class 7 as a default for vapor cloud explosions). Returns numeric Pascal overpressure. Validates inputs.

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] `src/der02/blast.py` exposes `blast_overpressure(distance_m, energy_joules, ambient_pressure_pa=101325)`
- [ ] Computes Sachs scaled distance `Z = R / (E/P0)^(1/3)`
- [ ] Looks up overpressure using the TNO strength-class-7 curve (interpolation over a tabulated Z→Δp curve)
- [ ] Raises `ValueError` on negative distance, negative energy, or zero energy
- [ ] Returns 0 Pa for Z above ~1000 (effectively free-field, atmospheric)
- [ ] Module docstring cites TNO Green Book Chapter 6 (Methods for the calculation of physical effects) and identifies the strength class used
- [ ] Tests in `tests/test_blast.py`:
  - TNO worked example: for E = 5×10^9 J, R = 100 m, P0 = 101325 Pa, assert Δp matches TNO Table 6.x within 10%
  - Monotonicity: overpressure decreases with distance
  - Energy scaling: doubling E at fixed distance increases overpressure (Z decreases)
  - Validation: negative distance raises
- [ ] All numeric values used in tests are recorded in `CITATIONS.md`