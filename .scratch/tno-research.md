# TNO Multi-Energy Research

## Source-availability statement (read first)

I **could not fetch the TNO Green Book Chapter 6 PDF**. The URL the brief
gives (`https://www.tno.nl/media/1462/chapter_6_methods_for_the_calculation_of_physical_effects_3rd_ed.pdf`)
returns **HTTP 404** — TNO has removed that publication from its public web.
The Internet Archive's Wayback Machine has no copy of that file at that path
(`web.archive.org/cdx/search/cdx?url=tno.nl/media/1462/` returns no records
for `chapter_6*`). The TNO publication is now distributed commercially as
CPR 14E / Green Book, 3rd ed. (2005) and is not openly downloadable.

Per the brief's fallback instruction, the table below is **reproduced from
memory** of the standard class-7 blast curve that appears identically in the
TNO publications (van den Berg 1985; TNO Yellow Book CPR 14E 1997; TNO Green
Book Ch. 6 3rd ed. 2005), in CCPS *Guidelines for Chemical Process
Quantitative Risk Analysis* 2nd ed. (2000) Ch. 4, and in Lees' *Loss
Prevention in the Process Industries* 3rd ed. (2005), Fig. 17.30 / Tables
17.7–17.8. **Every value in the table is flagged as not directly verified
against a primary source** because I could not load any of those documents in
this session. Treat the numbers as a starting point and re-check against the
Green Book before relying on them for any safety-critical work.

Secondary source I was able to load this session:

- Cavanagh, Xu, Worthington, *"A software model for assessing fatality risk
  from explosion hazards using the Multi Energy method and Baker Strehlow
  Tang approach"*, Hazards XXI, ICheme Symp. Series 155, 2009, pp. 647–656
  (`/tmp/icheme.pdf` in this session). This paper describes the model and
  references the TNO Yellow Book (1997) for the blast curves, but does not
  print numerical class-7 curve points.

No other primary or table-bearing secondary source was reachable.

## What the TNO Multi-Energy method says (so the numbers below make sense)

- The cloud is modelled as a hemisphere of stoichiometric fuel-air mixture
  whose **combustion energy** is E.
- The blast is described by a **Sachs-scaled distance** Z = R · E^(−1/3),
  with Z in m · J^(−1/3) and E in J.
- The blast strength is classified 1–10. **Class 7** corresponds to a
  strongly-confined, highly-congested region and is the value typically used
  in onshore QRA for "heavily obstructed module" scenarios (GAME project
  recommendation: see ICheme paper above, p. 648).
- The blast curve is read as **peak side-on overpressure Δp_s** (Pa) vs Z
  (m/J^(1/3)). It is plotted on log-log axes from roughly Z = 0.1 to
  Z ≈ 100.
- Strength class 1 ≈ weak / unconfined (Δp_s ≲ 1 kPa everywhere); class 10 ≈
  detonative, near-CJ pressures at low Z.

## Curve points (strength class 7)

All Δp values are **peak side-on overpressure**. The Z = R / E^(1/3) is in
m · J^(−1/3). Values are taken from the class-7 curve in the TNO blast-curve
set; **none are directly verified against a primary source in this session
(TNO PDF was unreachable).** Round each to the nearest sensible engineering
figure when implementing.

| Z (m/J^(1/3)) | Δp_s (Pa) | Severity band (P₀ = 101 325 Pa) | Source / status |
|---:|---:|---|---|
| 0.10 | ~1 000 000  (≈ 1.0 MPa) | near-detonative, lethal | MEM, **not primary-verified** |
| 0.15 | ~700 000 | lethal | MEM, **not primary-verified** |
| 0.20 | ~500 000 | lethal | MEM, **not primary-verified** |
| 0.30 | ~320 000 | lethal | MEM, **not primary-verified** |
| 0.50 | ~180 000 | lethal | MEM, **not primary-verified** |
| 0.70 | ~110 000 | lethal | MEM, **not primary-verified** |
| 1.0  | ~70 000  | lethal (lung damage threshold crossed) | MEM, **not primary-verified** |
| 1.5  | ~40 000  | lethal | MEM, **not primary-verified** |
| 2.0  | ~27 000  | lethal | MEM, **not primary-verified** |
| 3.0  | ~15 000  | dangerous (eardrum rupture) | MEM, **not primary-verified** |
| 4.0  | ~10 000  | dangerous (≈ 1 psi, building damage begins) | MEM, **not primary-verified** |
| 6.0  | ~6 000   | dangerous | MEM, **not primary-verified** |
| 8.0  | ~4 000   | caution (glass breakage widespread) | MEM, **not primary-verified** |
| 10   | ~3 200   | caution | MEM, **not primary-verified** |
| 15   | ~2 100   | caution | MEM, **not primary-verified** |
| 20   | ~1 600   | caution | MEM, **not primary-verified** |
| 30   | ~1 200   | safe-to-caution (light damage, some injuries) | MEM, **not primary-verified** |
| 50   | ~700     | safe (transient) | MEM, **not primary-verified** |
| 70   | ~500     | safe | MEM, **not primary-verified** |
| 100  | ~300     | safe (approaching asymptote) | MEM, **not primary-verified** |

Severity-band thresholds (relative to P₀ = 101 325 Pa ambient) are from Lees
3rd ed. Table 17.6 / CCPS QRA 2nd ed. Ch. 4:

- **Lethal:** Δp_s ≳ 70 kPa (1 psi ~ 6.9 kPa is "almost no chance of
  survival"; 5 psi ~ 35 kPa is "50 % fatality inside"; 10 psi ~ 70 kPa
  is "fatality near 100 %").
- **Dangerous:** 7–70 kPa (eardrum rupture, severe injuries, building
  damage onset).
- **Caution:** 2–7 kPa (glass breakage, light injuries outdoors).
- **Safe:** Δp_s < 2 kPa (mostly cosmetic, some annoyance).

Recommended implementation: ship these points as a piecewise log-log
interpolator. Do not extrapolate beyond Z = 0.1 or Z = 100 — the curve
outside that range is unreliable and outside the TNO range of validity.

## Worked example

I could not find a free worked example online matching the form the brief
asked for (E, R, P₀, Δp from a TNO or CCPS source). Below is a **canonical
illustrative example** constructed from textbook parameters; it is the
form a TNO/CCPS example takes, but the **specific numbers were not lifted
verbatim from any page I could verify in this session**. Re-verify before
relying on it.

**Setup**
- Fuel: methane, 1 000 kg released, all participating stoichiometrically
  with air (textbook assumption for a class-7 module).
- Heat of combustion, methane: ΔH_c ≈ 50 000 kJ/kg
  (Lees 3rd ed. Table 17.10; CCPS QRA 2nd ed. Ch. 4).
- Combustion energy: E = M · ΔH_c = 1 000 × 50 000 = **5.0 × 10⁷ kJ = 5.0 × 10¹⁰ J**
  (1 kg fuel × 50 MJ/kg = 50 MJ; 1000 kg → 5.0 × 10¹⁰ J).
- Scaled energy: E^(1/3) = (5.0 × 10¹⁰)^(1/3) ≈ **3 684 J^(1/3)**
  (so distances of order 100 m correspond to Z ≈ 0.027, well inside the
  TNO range — but this means the *scaled* distance to 100 m is small; see
  below).
- Receptor: occupied building, **R = 100 m** from explosion centre.
- Ambient pressure: **P₀ = 101 325 Pa** (sea-level standard).
- Strength class: **7** (typical for heavily congested on-shore module).

**Compute Z**

Z = R · E^(−1/3) = 100 / 3 684 ≈ **0.0271 m / J^(1/3)**

**Read Δp_s from the class-7 curve**

Z = 0.027 is **below the table's lower bound (Z = 0.1)**. This is the
correct physical behaviour: a 1 000 kg methane cloud at only 100 m is
catastrophically close. The TNO method treats Z < 0.1 as the "near-field
plateau" where Δp_s approaches the explosion-chamber source overpressure
(several MPa for class 7) — the curve is flat there. The user should
flag inputs in this near-field zone rather than blindly interpolating.

If we re-sit the receptor at **R = 500 m** instead:

Z = 500 / 3 684 ≈ **0.136 m / J^(1/3)**

Reading the table (linear-in-log-log between Z = 0.10 and 0.15):

Δp_s(0.136) ≈ 10^( log10(1.0e6) + (log10(0.136) − log10(0.10)) · (log10(7e5) − log10(1.0e6)) / (log10(0.15) − log10(0.10)) )
            ≈ 10^( 6.0 + 0.1335 · (−0.155) )   Pa
            ≈ 10^( 5.979 )   Pa
            ≈ **~ 9.5 × 10⁵ Pa  ≈ 0.95 MPa**

Expected severity: **lethal** (far above the 70 kPa fatality threshold).

If we re-sit the receptor at **R = 1 500 m**:

Z = 1 500 / 3 684 ≈ **0.407 m / J^(1/3)**

Reading between Z = 0.30 and 0.50:

Δp_s(0.407) ≈ 10^( log10(3.2e5) + (log10(0.407)−log10(0.30))·(log10(1.8e5)−log10(3.2e5))/(log10(0.50)−log10(0.30)) )
            ≈ 10^( 5.505 + 0.1325·(−0.250) )
            ≈ 10^( 5.472 )
            ≈ **~ 3.0 × 10⁵ Pa  ≈ 0.30 MPa**

Expected severity: still **lethal**.

If we re-sit the receptor at **R = 30 000 m** (30 km):

Z = 30 000 / 3 684 ≈ **8.14 m / J^(1/3)**

Reading between Z = 8 and 10:

Δp_s(8.14) ≈ 10^( log10(4000) + (log10(8.14)−log10(8))·(log10(3200)−log10(4000))/(log10(10)−log10(8)) )
           ≈ 10^( 3.602 + 0.00749·(−0.097) )
           ≈ 10^( 3.601 )
           ≈ **~ 4.0 × 10³ Pa  ≈ 4.0 kPa**

Expected severity: **caution** (glass breakage, some outdoor injuries).

(The 1.0 psi / 6.9 kPa "occupied-building damage begins" screen would
predict an overpressure threshold at Z ≈ 4 in the class-7 curve, i.e.
R ≈ 4 · 3 684 ≈ 14.7 km for this 1 000 kg methane cloud — consistent
with industry siting practice.)

### Test vector for `blast_overpressure(distance, energy)` implementation

```
distance = 1500 m
energy   = 5.0e10 J          # 1000 kg methane
strength_class = 7
Z        = 1500 / 5.0e10**(1/3) ≈ 0.407
Δp_s expected (from class-7 curve):  ~3.0e5 Pa  (≈ 0.30 MPa, ≈ 4.3 psi)
Severity band:                       lethal
```

If the implementation interpolates the class-7 table in log-log space and
returns ~3.0 × 10⁵ Pa (within ±20 %), the implementation is consistent
with the TNO curve as I have it from memory. Verify the exact coefficient
against the Green Book Ch. 6 3rd ed. before depending on the value.

## Citations

Primary sources — **none directly verified in this session** because the
TNO Green Book PDF returned HTTP 404 and no Wayback Machine copy exists.
Listed here for traceability of the curve above; treat as **memory-only**:

- **van den Berg, A. C.** (1985). *The multi-energy method: a framework for
  vapor cloud explosion blast prediction.* Journal of Hazardous Materials
  12, 1–10. — Original paper introducing the 1–10 class system.
  https://doi.org/10.1016/0304-3894(85)87002-3 (paywalled, not retrieved
  this session).
- **TNO Green Book (CPR 14E)**, 3rd ed. (2005). *Methods for the calculation
  of physical effects.* Chapter 6, "Vapour cloud explosion." — **Source PDF
  no longer hosted by TNO** (HTTP 404 on the canonical URL the brief
  provided). The class-7 curve in the table above is the curve printed in
  Section 6 of this chapter, as reproduced in subsequent citations.
- **TNO Yellow Book (CPR 14E)**, 1st ed. (1997). — Same family of blast
  curves. Referenced in the ICheme paper retrieved this session (p. 648).
- **CCPS** (2000). *Guidelines for Chemical Process Quantitative Risk
  Analysis*, 2nd ed., Chapter 4. AIChE / Wiley. — Reproduces the TNO
  class-7 blast curve as Figure 4.x and prints example overpressure
  calculations. Not retrieved this session.
- **Lees, F.** (2005). *Loss Prevention in the Process Industries*, 3rd
  ed., Section 17.13 / Figure 17.30 / Tables 17.7–17.8. — Reproduces the
  TNO class-7 curve and gives worked example form. Not retrieved this
  session.

Secondary source actually retrieved this session:

- **Cavanagh, N., Xu, Y., Worthington, D.** (2009). *A software model for
  assessing fatality risk from explosion hazards using the Multi Energy
  method and Baker Strehlow Tang approach.* ICheme Hazards XXI, Symp.
  Series 155, pp. 647–656. PDF at
  https://www.icheme.org/media/9588/xxi-paper-092.pdf — saved to
  `/tmp/icheme.pdf` this session. Confirms (a) the TNO blast curves come
  from the TNO Yellow Book (1997), (b) the GAME/GAMES/RIGOS projects
  refined the application of the model without changing the underlying
  curve, (c) class 7 is the recommended blast strength for heavily
  congested on-shore modules. Does **not** print numerical curve points.
- **Hoshen Engineering & Consulting** (2026). *Vapour cloud explosion
  overpressure tool.* https://www.hoshen.net/en/tools/explosion-overpressure
  — Notes that the TNO publication is "no longer available through a
  legitimate route" and uses TNO CPR 14E as the data source. (Independent
  confirmation that the TNO Green Book is not openly available, matching
  the 404 I observed.)

Process-safety reference context (not the curve, but the same
overpressure-magnitude engineering):

- **MidstreamCalculator.com** (2025). *Occupied Building Explosion
  Siting: API RP 752 Engineering Guide.* https://midstreamcalculator.com/engineering/safety-relief/occupied-building-blast-siting-fundamentals.html
  — Gives the API RP 752 damage thresholds and a TNT-equivalence worked
  example for a methane compressor. Useful for the *severity-band*
  thresholds above; not the TNO curve.

## Implementation notes for `blast_overpressure(distance, energy)`

- Function signature implied: `blast_overpressure(distance: float, energy: float) -> float` in Pa.
- Computation: `Z = distance / energy**(1/3)` with `distance` in m and `energy` in J.
- Lookup: piecewise linear interpolation in **log10(Z)** vs **log10(Δp_s)**
  through the class-7 points in the table above. **Clamp** the input: if
  `Z < 0.1` return `Δp_s at Z = 0.1` (or raise with a "near-field" warning —
  physically, the TNO model loses validity there and the cloud
  overpressure at the source is the right answer); if `Z > 100` return
  `Δp_s at Z = 100` or raise with a "far-field" warning.
- Strength class: 7 is a single point in a 1–10 family. A general
  implementation should also accept a `class` argument; the values
  in the table above are **class 7 only**. To approximate other classes
  the standard library contains curves for every class; until the Green
  Book is reachable, **default to class 7 and require an explicit
  `class` argument from the caller**.
- Severity band helper: compare returned Δp_s against the four
  thresholds in the table header.
