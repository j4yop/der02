# Citations

Every numeric constant, threshold, and formula in `der02` traces back to one of the references below. Citations are added incrementally as each module lands. The list grows ticket by ticket.

## References

### TNO Green Book — *Methods for the calculation of physical effects* (3rd ed., 2005)
Chapter 6: vapour cloud explosions (Multi-Energy model). Source of the Sachs scaled-distance relation and the strength-class-7 overpressure curve used in `src/der02/blast.py`. **Status: cited (ticket 04).**

### CCPS — *Guidelines for Chemical Process Quantitative Risk Analysis* (2nd ed., 2000)
Chapter 2: thermal radiation criteria (37.5 / 12.5 / 4 kW/m² bands). Chapter 4: overpressure damage criteria (Δp bands). Source of the severity thresholds in `src/der02/thresholds.py`. **Status: cited (ticket 03).**

### API RP 521 — *Guide for Pressure-Relieving and Depressuring Systems* (7th ed., 2020)
Used for estimating flame height in pool-fire / vapor-fire scenarios. **Status: planned (ticket 05).**

### NIST WebBook (https://webbook.nist.gov)
Source of fuel constants: heat of combustion, vapor density, flame temperature. **Status: planned (ticket 02).**

## Per-ticket citation log

- **Ticket 02** — Fuel library: NIST WebBook (SRD 69) species pages for ΔcH° and MW of propane, methane, ethanol, hydrogen, ammonia, n-heptane (gasoline surrogate). Per-species reference lists:
  - Propane (C₃H₈, CAS 74-98-6): Pittam & Pilcher 1972 (*J. Chem. Soc. Faraday Trans. 1* 68, 2224); Younglove & Ely 1987 (*J. Phys. Chem. Ref. Data* 16, 577 — liquid density at 15 °C).
  - n-Heptane (C₇H₁₆, CAS 142-82-5): Prosen & Rossini 1945 (*J. Res. NBS*); Davies & Gilbert 1941 (*J. Am. Chem. Soc.* 63, 2730).
  - Methane (CH₄, CAS 74-82-8): Pittam & Pilcher 1972; Manion 2002 (recommended ΔfH°); Chase 1998 (NIST-JANAF).
  - Ethanol (C₂H₅OH, CAS 64-17-5): Chao & Rossini 1965; Green 1960; Rossini 1932.
  - Hydrogen (H₂, CAS 1333-74-0): Cox, Wagman 1984 (CODATA key values); Chase 1998.
  - Ammonia (NH₃, CAS 7664-41-7): Cox, Wagman 1984; Chase 1998.
  - Adiabatic flame temperatures: Perry's Chemical Engineers' Handbook 8th ed., NIST-JANAF Thermochemical Tables (Chase 1998). **Flagged: not directly listed on NIST WebBook species pages; verification by equilibrium calculation recommended.**
  - Liquid densities at 15 °C: CRC Handbook, Younglove & Ely 1987 (propane), NIST TRC Web Thermo Tables (subscription database, linked from species pages). **Flagged: public WebBook species pages list ρ_crit only, not 15 °C ρ.**
- **Ticket 03** — Thresholds: CCPS *Guidelines for CPQRA* 2nd ed., Table 2.x thermal radiation bands; CCPS overpressure damage criteria.
- **Ticket 04** — Blast: TNO Green Book Ch. 6, Multi-Energy strength class 7. Worked example reference: TNO Green Book worked example X.
- **Ticket 05** — Thermal: point-source flux per CCPS *Guidelines for CPQRA* 2nd ed. Ch. 2; ALOHA user's manual. **Solid-flame view-factor model deferred** (needs flame-height sub-model from API RP 521).
- **Ticket 06** — Wind: simplified CCPS dispersion correction (stretch factor); κ = 0.1 s/m default. **Real dispersion model deferred** (Britoil/EPA heavy-gas; Pasquill stability A–F).

(Filled in detail as each ticket lands.)