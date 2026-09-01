# Fuel Physical-Constant Research

Compiled from NIST Chemistry WebBook (SRD 69) primary species pages:
https://webbook.nist.gov

Each entry below lists the data found on the species' NIST WebBook
thermochemistry page (the `Thermo` mask). Liquid densities at 15 °C
are standard textbook property (also in NIST/TRC Web Thermo Tables
which is the subscription database linked from each species page; the
public WebBook pages list critical density but not 15 °C liquid density).
Adiabatic flame temperature (AFT) is **not** tabulated on the public
NIST WebBook species pages; the values below are taken from the
standard combustion reference *Perry's Chemical Engineers' Handbook*
and *NIST-JANAF Thermochemical Tables* (Chase, 1998) — flagged where
used.

## 1. Propane — C₃H₈, CAS 74-98-6

| Property | Value | Source |
|---|---|---|
| Molecular weight | 44.0956 g/mol | NIST WebBook |
| ΔfH°(gas, 298 K) | −104.7 ± 0.5 kJ/mol | NIST WebBook, Pittam & Pilcher 1972 |
| **ΔcH°(gas) = HHV** | **−2219.2 ± 0.46 kJ/mol** | NIST WebBook, Pittam & Pilcher 1972 |
| ΔcH°(liquid) | not listed on public WebBook | — |
| **LHV (per mole)** | 2219.2 − 4 × 44.01 = **−2043.2 kJ/mol** | derived from ΔcH°gas + H₂O latent heat |
| **LHV (per kg)** | **46 340 kJ/kg** | derived |
| Adiabatic flame T (stoich., 1 atm, products as ideal gas) | **~2267 K** | Perry's 8th ed. table; flagged — NIST WebBook does not list AFT |
| Liquid density at 15 °C | ~493 kg/m³ | textbook (Younglove & Ely 1987, J. Phys. Chem. Ref. Data 16, 577 — cited in NIST WebBook references section) |
| T_boil | 231.1 K | NIST WebBook |
| T_crit | 369.9 K / P_crit 42.5 bar / ρ_crit 5.1 mol/L | NIST WebBook |
| Vapor density (gas, 15 °C, 1 atm) | 44.0956/22.414 × 288.15/273.15 = **1.97 kg/m³** | derived from ideal gas |
| Vapor relative to air | 44.0956 / 28.97 = **1.52** | derived |
| **NIST WebBook URL** | https://webbook.nist.gov/cgi/cbook.cgi?ID=C74986&Units=SI | |

References on NIST WebBook page: Pittam & Pilcher 1972 (J. Chem. Soc.
Faraday Trans. 1 68, 2224); Prosen & Rossini 1945 (J. Res. NBS);
Younglove & Ely 1987 (J. Phys. Chem. Ref. Data 16, 577 — propane
thermophysical properties).

---

## 2. Gasoline surrogate — n-Heptane — C₇H₁₆, CAS 142-82-5

(Gasoline is a mixture; per the brief we use n-heptane as the standard
surrogate.)

| Property | Value | Source |
|---|---|---|
| Molecular weight | 100.2019 g/mol | NIST WebBook |
| ΔfH°(liquid) | −224.4 ± 0.79 kJ/mol | NIST WebBook, Prosen & Rossini 1945 |
| **ΔcH°(liquid) = HHV** | **−4817 ± 8 kJ/mol** | NIST WebBook, average of 7 values |
| **LHV (per mole)** | 4817 − 8 × 44.01 = **4464.9 kJ/mol** | derived |
| **LHV (per kg)** | **44 560 kJ/kg** | derived |
| Adiabatic flame T (stoich., 1 atm) | **~2300 K** | Perry's 8th ed.; flagged — not on NIST WebBook |
| Liquid density at 15 °C | ~688 kg/m³ (NIST TRC, also CRC) | textbook — flagged: public WebBook does not list 15 °C ρ |
| T_boil | 371.5 K | NIST WebBook |
| T_crit | 540 K / P_crit 27.4 bar / ρ_crit 2.35 mol/L | NIST WebBook |
| Vapor density (15 °C, 1 atm) | 100.20 × 273.15 / (288.15 × 22.414) = **4.24 kg/m³** | derived |
| Vapor relative to air | 100.20 / 28.97 = **3.46** | derived |
| **NIST WebBook URL** | https://webbook.nist.gov/cgi/cbook.cgi?ID=C142825&Units=SI | |

References on NIST WebBook page: Prosen & Rossini 1945 (J. Res. NBS);
Davies & Gilbert 1941 (J. Am. Chem. Soc. 63, 2730).

> **Mixture caveat.** Gasoline is not a pure compound. CCPS *Guidelines
> for Chemical Process Quantitative Risk Analysis* (2nd ed., 2000)
> Table 2-7 / Section 2 lists an aggregate "typical gasoline" LHV of
> ~43.4 MJ/kg (HHV ~46.5 MJ/kg). These aggregate values were not
> retrieved from CCPS in this run; flag as unverified. n-Heptane
> values above are the surrogate reported on NIST WebBook.

---

## 3. Methane — CH₄, CAS 74-82-8

| Property | Value | Source |
|---|---|---|
| Molecular weight | 16.0425 g/mol | NIST WebBook |
| ΔfH°(gas, 298 K) | −74.6 ± 0.3 kJ/mol (recommended, Manion 2002) | NIST WebBook |
| **ΔcH°(gas) = HHV** | **−890.7 ± 0.4 kJ/mol** | NIST WebBook, Pittam & Pilcher 1972 |
| **LHV (per mole)** | 890.7 − 2 × 44.01 = **802.7 kJ/mol** | derived |
| **LHV (per kg)** | **50 030 kJ/kg** | derived |
| Adiabatic flame T (stoich., 1 atm) | **~2223 K** | JANAF / Perry's; flagged — not on WebBook |
| T_boil | 111 K | NIST WebBook |
| T_crit | 190.6 K / P_crit 46.1 bar / ρ_crit 10.1 mol/L | NIST WebBook |
| Vapor density (15 °C, 1 atm) | 16.0425 × 273.15 / (288.15 × 22.414) = **0.679 kg/m³** | derived |
| Vapor relative to air | 16.0425 / 28.97 = **0.554** | derived |
| **NIST WebBook URL** | https://webbook.nist.gov/cgi/cbook.cgi?ID=C74828&Units=SI | |

References on NIST WebBook page: Pittam & Pilcher 1972; Prosen &
Rossini 1945; Manion 2002 (recommended ΔfH°); Chase 1998
(NIST-JANAF Thermochemical Tables).

---

## 4. Ethanol — C₂H₅OH, CAS 64-17-5

| Property | Value | Source |
|---|---|---|
| Molecular weight | 46.0684 g/mol | NIST WebBook |
| ΔfH°(liquid) | −276 ± 2 kJ/mol (avg of 6) | NIST WebBook |
| ΔfH°(gas) | −234 ± 2 kJ/mol (avg of 9) | NIST WebBook |
| **ΔcH°(liquid) = HHV** | **−1367.6 ± 0.3 kJ/mol** | NIST WebBook, Chao & Rossini 1965 |
| **LHV (per mole)** | 1367.6 − 3 × 44.01 = **1235.6 kJ/mol** | derived |
| **LHV (per kg)** | **26 830 kJ/kg** | derived |
| Adiabatic flame T (stoich., 1 atm) | **~2263 K** | Perry's 8th ed.; flagged |
| Liquid density at 15 °C | ~789 kg/m³ | textbook (CRC); flagged: not on public WebBook |
| T_boil | 351.5 K | NIST WebBook |
| T_crit | 514 K / P_crit 63 bar / ρ_crit 6.0 mol/L | NIST WebBook |
| Vapor density (15 °C, 1 atm) | 46.0684 × 273.15 / (288.15 × 22.414) = **1.95 kg/m³** | derived |
| Vapor relative to air | 46.0684 / 28.97 = **1.59** | derived |
| **NIST WebBook URL** | https://webbook.nist.gov/cgi/cbook.cgi?ID=C64175&Units=SI | |

References on NIST WebBook page: Chao & Rossini 1965; Green 1960;
Rossini 1932.

---

## 5. Hydrogen — H₂, CAS 1333-74-0

| Property | Value | Source |
|---|---|---|
| Molecular weight | 2.01588 g/mol | NIST WebBook |
| ΔfH°(gas) | 0 (reference) | NIST WebBook |
| **ΔcH°(gas) = HHV** | **−285.83 kJ/mol** | NIST-JANAF / CODATA (Cox, Wagman 1984); H₂(g) + ½O₂(g) → H₂O(l); flagged: this number is standard but not directly listed on the H₂ species page in the same format as organics |
| **LHV (per mole)** | 285.83 − 44.01 = **241.82 kJ/mol** | derived |
| **LHV (per kg)** | **119 950 kJ/kg** | derived |
| Adiabatic flame T (stoich., 1 atm) | **~2389 K** | JANAF; flagged |
| T_boil | 20.27 K | NIST WebBook phase-change data |
| T_crit | 33.18 K / P_crit 13.0 bar | NIST WebBook |
| Vapor density (15 °C, 1 atm) | 2.01588 × 273.15 / (288.15 × 22.414) = **0.0853 kg/m³** | derived |
| Vapor relative to air | 2.01588 / 28.97 = **0.0696** | derived |
| **NIST WebBook URL** | https://webbook.nist.gov/cgi/cbook.cgi?ID=C1333740&Units=SI | |

References on NIST WebBook page: Cox, Wagman 1984 (CODATA key values);
Chase 1998 (NIST-JANAF Thermochemical Tables).

---

## 6. Ammonia — NH₃, CAS 7664-41-7

| Property | Value | Source |
|---|---|---|
| Molecular weight | 17.0305 g/mol | NIST WebBook |
| ΔfH°(gas, 298 K) | −45.94 ± 0.35 kJ/mol (CODATA) | NIST WebBook |
| **ΔcH°(gas) = HHV** | NH₃(g) + ¾O₂(g) → ½N₂(g) + 3/2 H₂O(l); from ΔfH°: 1.5 × (−285.83) − (−45.94) = **−382.81 kJ/mol** | derived from NIST WebBook ΔfH° values + H₂O ΔfH° |
| **LHV (per mole)** | 382.81 − 1.5 × 44.01 = **−316.79 kJ/mol** | derived |
| **LHV (per kg)** | **18 600 kJ/kg** | derived |
| Adiabatic flame T (stoich., 1 atm) | **~1850 K** (or ~2080 K with O₂-enriched conditions) | flagged — not on NIST WebBook species page |
| T_boil | 239.7 K | NIST WebBook (Antoine/Stull data) |
| T_crit | 405.4 K / P_crit 113 bar | NIST WebBook |
| Liquid density at 15 °C | ~618 kg/m³ | textbook (CRC); flagged |
| T_fus | 195 K | NIST WebBook |
| Vapor density (15 °C, 1 atm) | 17.0305 × 273.15 / (288.15 × 22.414) = **0.721 kg/m³** | derived |
| Vapor relative to air | 17.0305 / 28.97 = **0.588** | derived |
| **NIST WebBook URL** | https://webbook.nist.gov/cgi/cbook.cgi?ID=C7664417&Units=SI | |

References on NIST WebBook page: Cox, Wagman 1984 (CODATA ΔfH°);
Chase 1998 (NIST-JANAF Shomate equation).

---

## Summary table

| Fuel | LHV (kJ/kg) | AFT (K) | ρ_liq @ 15 °C (kg/m³) | Vapor relative to air | NIST WebBook CAS |
|---|---|---|---|---|---|
| Propane | 46 340 | ~2267 | ~493 | 1.52 | 74-98-6 |
| n-Heptane (gasoline surrogate) | 44 560 | ~2300 | ~688 | 3.46 | 142-82-5 |
| Methane | 50 030 | ~2223 | (gas) | 0.554 | 74-82-8 |
| Ethanol | 26 830 | ~2263 | ~789 | 1.59 | 64-17-5 |
| Hydrogen | 119 950 | ~2389 | (gas) | 0.0696 | 1333-74-0 |
| Ammonia | 18 600 | ~1850 | ~618 (at bp; ~602 at −33 °C) | 0.588 | 7664-41-7 |

---

## Flagged / unverified values

The following values are NOT pinned to a primary NIST WebBook source
and should be treated as flagged for verification:

1. **Adiabatic flame temperature (all fuels).** NIST WebBook species
   pages do not tabulate AFT. Values listed are standard combustion
   references (Perry's Chemical Engineers' Handbook, NIST-JANAF
   Thermochemical Tables / Chase 1998) cited as `flagged` in each
   section above. **Need verification from a primary combustion
   reference (Turns, Borman & Ragland, or similar) or direct
   equilibrium calculation using NIST WebBook Shomate coefficients
   (Chase 1998) — both are tractable in next pass.**

2. **Liquid density at 15 °C (all liquids).** The public NIST WebBook
   species pages list critical density (ρc) and saturated-liquid Cp
   data but do **not** tabulate a single-value 15 °C liquid density.
   The subscription NIST/TRC Web Thermo Tables (linked from each
   species page) does contain 15 °C ρ. Values listed are textbook
   (CRC Handbook, Perry's). **Flagged for verification — open the
   linked NIST/TRC WTT lite edition or another NIST primary source.**

3. **NIST WebBook fluid-property page (`Mask=2&Type=Fluid`)** returned
   an internal error for propane, heptane, ethanol during this fetch —
   those pages would otherwise be the primary source for liquid
   densities. Should be retried.

4. **CCPS *Guidelines for CPQRA* (2nd ed., 2000) values for "typical
   gasoline".** Not retrieved in this run; CCPS Table 2-7 typical
   gasoline LHV ~ 43.4 MJ/kg should be cited when the printed copy
   is consulted.

5. **Hydrogen ΔcH°(gas) = −285.83 kJ/mol** is not listed in the same
   `ΔcH°gas` column as the organics on the H₂ WebBook species page.
   This number is universally cited (CODATA / Chase 1998); flagged
   only because the NIST WebBook page does not present it in the
   same combustion-data table.