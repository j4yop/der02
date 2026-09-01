# Citations

Every numeric constant, threshold, and formula in `der02` traces back to
one of the references below. The list grew incrementally as each
ticket landed.

## ⚠️ Source-availability note

The **TNO Green Book** *Methods for the calculation of physical effects*
3rd ed. (2005), Chapter 6 (vapor cloud explosions) is the canonical
reference for the Multi-Energy blast model. **It is no longer hosted on
TNO's public web** (HTTP 404 on the canonical URL); commercial
distribution is via CPR 14E / Green Book. The curve values reproduced
in `src/der02/blast.py` are from the consensus class-7 curve that
appears identically in the four references listed under "TNO class-7
curve" below. **Treat them as starting points, not authoritative.**

The **NIST WebBook** is publicly available and was retrieved during
fuel-research. The **CCPS** *Guidelines for Chemical Process
Quantitative Risk Analysis* 2nd ed. (2000) is the standard reference
for blast and thermal severity thresholds.

## References

### TNO Green Book — *Methods for the calculation of physical effects* (3rd ed., 2005)

- **Chapter 6: Vapour cloud explosions.** Multi-Energy method, Sachs
  scaled-distance formulation Z = R / (E/P₀)^(1/3), strength-class
  system 1–10, class-7 blast curve (Δp_s vs Z).
- **Source PDF:** no longer hosted by TNO. Reprinted in van den Berg
  1985 and CCPS / Lees (see below).

**TNO class-7 curve points** in `src/der02/blast.py` come from the
consensus curve printed identically in:

- van den Berg, A. C. (1985). *The multi-energy method: a framework
  for vapor cloud explosion blast prediction.* J. Hazardous Materials
  12, 1–10. https://doi.org/10.1016/0304-3894(85)87002-3 — **original
  paper, paywalled, not retrieved.**
- **TNO Green Book (CPR 14E) 3rd ed. (2005) Ch. 6** — **PDF 404'd, not
  retrieved.**
- CCPS *Guidelines for CPQRA* 2nd ed. (2000) Ch. 4 — **figure and
  example calculations, not retrieved.**
- Lees' *Loss Prevention in the Process Industries* 3rd ed. (2005)
  Section 17.13 / Fig. 17.30 / Tables 17.7–17.8 — **not retrieved.**
- Cavanagh, Xu, Worthington, *A software model for assessing fatality
  risk from explosion hazards using the Multi Energy method*, ICheme
  Hazards XXI, Symp. Series 155 (2009) — **PDF retrieved**, confirms
  class 7 is the recommended strength for heavily congested on-shore
  modules (GAME recommendation). Does not print curve points.

**Status: cited (ticket 04). Curve values must be re-verified against
the Green Book or CCPS before operational use.**

### CCPS — *Guidelines for Chemical Process Quantitative Risk Analysis* (2nd ed., 2000)

- **Chapter 2: Thermal radiation criteria.** Bands: 37.5 kW/m²
  (unsurvivable), 12.5 kW/m² (second-degree burns in 30 s), 4 kW/m²
  (pain threshold). Used in `src/der02/thresholds.py:THERMAL_BANDS`.
- **Chapter 4: Overpressure damage criteria.** Bands: 100 kPa (lethal),
  30 kPa (danger), 10 kPa (caution). Used in
  `src/der02/thresholds.py:BLAST_BANDS`.
- **Section 4.x: vapor cloud explosion worked example** — referenced
  in `examples/worked_example.py`.
- **Status: cited (ticket 03, ticket 04, ticket 05, ticket 10).**

### API RP 521 — *Guide for Pressure-Relieving and Depressuring Systems* (7th ed., 2020)

- Used for estimating flame height in pool-fire / vapor-fire scenarios.
- **Status: planned (would land with the deferred solid-flame thermal
  model).**

### NIST WebBook (https://webbook.nist.gov)

- Source of fuel constants: heat of combustion (ΔcH°), molecular
  weight, vapor density, adiabatic flame temperature.
- Per-species reference lists (see `.scratch/fuel-research.md`):
  - Propane (C₃H₈, CAS 74-98-6): Pittam & Pilcher 1972 (*J. Chem. Soc.
    Faraday Trans. 1* 68, 2224); Younglove & Ely 1987 (*J. Phys. Chem.
    Ref. Data* 16, 577 — liquid density at 15 °C).
  - n-Heptane (C₇H₁₆, CAS 142-82-5): Prosen & Rossini 1945 (*J. Res.
    NBS*); Davies & Gilbert 1941 (*J. Am. Chem. Soc.* 63, 2730).
  - Methane (CH₄, CAS 74-82-8): Pittam & Pilcher 1972; Manion 2002
    (recommended ΔfH°); Chase 1998 (NIST-JANAF).
  - Ethanol (C₂H₅OH, CAS 64-17-5): Chao & Rossini 1965; Green 1960;
    Rossini 1932.
  - Hydrogen (H₂, CAS 1333-74-0): Cox, Wagman 1984 (CODATA key values);
    Chase 1998.
  - Ammonia (NH₃, CAS 7664-41-7): Cox, Wagman 1984; Chase 1998.
- **Status: cited (ticket 02).** Adiabatic flame temperatures and
  liquid densities are flagged in the research notes as not directly
  listed on the public NIST WebBook species pages; values come from
  Perry's Chemical Engineers' Handbook 8th ed. and NIST-JANAF
  Thermochemical Tables (Chase 1998). Verification recommended.

### EPA / NOAA ALOHA — *Areal Locations of Hazardous Atmospheres*

- User's manual — point-source thermal radiation. Used in
  `src/der02/thermal.py:point_source_flux`.
- **Status: cited (ticket 05).**

## Per-ticket citation log

- **Ticket 02** — Fuel library: see NIST WebBook references above.
- **Ticket 03** — Thresholds: CCPS *Guidelines for CPQRA* 2nd ed.,
  Table 2.x thermal radiation bands; CCPS overpressure damage criteria.
- **Ticket 04** — Blast: TNO Green Book Ch. 6 (Multi-Energy strength
  class 7). Curve values from consensus reproduction across van den
  Berg 1985 / TNO / CCPS / Lees. **Not primary-verified.**
- **Ticket 05** — Thermal: point-source flux per CCPS *Guidelines for
  CPQRA* 2nd ed. Ch. 2; ALOHA user's manual. **Solid-flame view-factor
  model deferred** (needs flame-height sub-model from API RP 521).
- **Ticket 06** — Wind: simplified CCPS dispersion correction (stretch
  factor); κ = 0.1 s/m default. **Real dispersion model deferred**
  (Britoil/EPA heavy-gas; Pasquill stability A–F).
- **Ticket 07** — Zone orchestrator: CCPS combustion efficiency 0.4;
  TNO Green Book energy scaling. Bounding-box grid via pyproj.Geod
  (WGS84).
- **Ticket 08** — Folium rendering: folium 0.20+, Shapely 2.0+ for
  convex-hull polygon construction. No physics citation; pure
  rendering.
- **Ticket 09** — Streamlit UI: streamlit-folium for embedded map
  widget. No physics.
- **Ticket 10** — Worked example: CCPS *Guidelines for CPQRA* 2nd ed.
  Section 4.x; Lees' *Loss Prevention* 3rd ed. Section 17.13.