# 03: Threshold table with citations

**What to build:** A `thresholds.py` module exposing numeric thresholds for blast overpressure and thermal radiation, mapped to severity bands, with every number cited in a docstring or inline comment.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] `src/der02/thresholds.py` defines `BLAST_BANDS` and `THERMAL_BANDS` as ordered lists of `(lower_bound_pa_or_kw_m2, severity)` tuples
- [ ] Blast bands: `>100_000 Pa` lethal, `>30_000 Pa` danger, `>10_000 Pa` caution, else safe (CCPS *Guidelines for CPQRA* 2nd ed., Table 2.x overpressure damage criteria)
- [ ] Thermal bands: `>37.5 kW/m²` lethal, `>12.5 kW/m²` danger, `>4 kW/m²` caution, else safe (CCPS thermal radiation criteria, Eisenberg reference)
- [ ] `classify_blast(overpressure_pa) -> severity` and `classify_thermal(flux_kw_m2) -> severity` use the bands
- [ ] Tests assert: `classify_blast(150_000)` is `"lethal"`; `classify_blast(5_000)` is `"safe"`; `classify_thermal(20)` is `"danger"`; edge values at boundaries behave consistently
- [ ] All thresholds and citations live in `CITATIONS.md` (additions made here, not yet rendered as a section in the README)