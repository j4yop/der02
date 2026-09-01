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

- **Ticket 03** — Thresholds: CCPS *Guidelines for CPQRA* 2nd ed., Table 2.x thermal radiation bands; CCPS overpressure damage criteria.
- **Ticket 04** — Blast: TNO Green Book Ch. 6, Multi-Energy strength class 7. Worked example reference: TNO Green Book worked example X.
- **Ticket 05** — Thermal: CCPS *Guidelines for CPQRA* 2nd ed., Ch. 2 (solid-flame model); API RP 521 (flame height).
- **Ticket 06** — Wind: heuristic elongation/compression; reference CCPS Section Y.

(Filled in detail as each ticket lands.)