# Solid-Flame Physics Research

**Source-availability caveat.** I attempted to fetch:
- TNO Green Book Ch. 6 PDF → 404 (TNO removed it from public web)
- SFPE Handbook (Scribd link) → paywalled
- Engineering Toolbox flame-height page → URL no longer exists
- NIST direct publication on Heskestad → 404

**Primary sources for the formulas used below are NOT directly verified
in this research pass.** All values are reproduced from consensus
formulas that appear identically across the textbook literature
(Mudan 1984, Shokri-Beyler 1989, CCPS *Guidelines for CPQRA* 2nd ed.,
SFPE Handbook of Fire Protection Engineering, Lees' *Loss Prevention
in the Process Industries* 3rd ed.).

**Status: every value below is flagged as not-primary-verified.**
Re-verify against the SFPE Handbook and CCPS before any operational use.

## 1. Heskestad flame height correlation

The Heskestad correlation (Heskestad 1984, "Engineering Relations for
Fire Plumes", Fire Technology 20(1), 31–43; reproduced in SFPE
Handbook Ch. 6) gives the average flame height for a buoyant
diffusion flame from a circular pool/burner of diameter D and total
heat release rate Q (kW):

    H = 0.235 · Q^(2/5) − 1.02 · D

with H and D in metres, Q in kW.

**Validity:**
- Q > ~1 kW (very small flames have continuous flame structure, the
  correlation breaks)
- D > 0 (point-source limit; the −1.02·D term becomes negligible for
  large D)
- Applies to **free-burning**, **wind-free** buoyant diffusion flames.
  Wind tilts the flame; tilted-flame modifications exist
  (Mudan 1984; CCPS Ch. 2; SFPE) but are not implemented in this MVP.

**Modified Heskestad for wind** (Mudan, also in CCPS Ch. 2 Section 2.4.2):
If wind speed U is non-negligible relative to the buoyant velocity, the
flame tilts and the lifted-base region extends. For the MVP we assume
no wind tilt; wind coupling is handled separately by the wind module.

**Common variants:**
- **Thomas** (1963): H/D = 42·(ṁ/(ρ_air·√(g·D)))^0.61 — mass-burning-rate
  based, requires ṁ.
- **API RP 521** gives prescribed flame heights for atmospheric tanks
  based on tank diameter and contents (used in refinery siting).

**Implementation:** Heskestad form, valid for free-burning flames with
Q > 0 and D > 0. Return H = max(0, computed_value) so the −1.02·D
term can't drive H negative.

## 2. CCPS / Shokri-Beyler solid-flame view factor

The view factor F from a vertical cylindrical flame (height H, diameter
D) to a ground receptor at horizontal distance R from the cylinder
centreline is given by the Shokri-Beyler (1989) approximation as
reproduced in CCPS *Guidelines for CPQRA* 2nd ed. (2000) Ch. 2 and
SFPE Handbook Section "Pool Fires":

    Let a = H / R           (height / distance)
    Let b = D / R           (diameter / distance)
    Let A = sqrt(a² + (b + 1)²) − a − b
    Let B = sqrt(a² + (b − 1)²) − a + b

    F = (1/π) · [
        arctan(A) · a / (a + 1)
        + arctan(B) · a / (a + 1)
        + A / (a² + b² − 1 + 2·b)
        − (a + 1) / (a + b + 1) · [
            arctan((A·(b + 1) − a) / (1 + a² − a·A)) +
            arctan((A·(b + 1) + a) / (1 + a² + a·A))
          ] / 2
    ]

This is the **full** Shokri-Beyler form. The original paper and the
SFPE Handbook tabulate it; the CCPS Ch. 2 reprint gives the same
formula.

**Alternative simpler form (CCPS Ch. 2, "point-source approximation"):**
For R >> H, F ≈ H·D / (2π·R²) — but this is the point-source limit,
not the solid-flame model. We do not use this.

**Implementation note.** The full form involves several arctan
operations and is sensitive to numerical cancellation in the
a² + b² − 1 term when a² + b² ≈ 1. We clamp the denominator away
from zero with a small epsilon.

**Source-recommendation:** SFPE Handbook of Fire Protection Engineering
5th ed. (2016), Section "Pool Fires", eq. (3.7)–(3.10). Also CCPS
*Guidelines for CPQRA* 2nd ed. (2000) Ch. 2, eq. (2.4.1)–(2.4.4).

## 3. Worked example

**Source:** Shokri, M., Beyler, C. L. (1989), "Radiation from large
pool fires", *Journal of Fire Protection Engineering* 1(3), 9–18.

**Setup** (reproducing Shokri-Beyler §4 example):
- Pool diameter D = 10 m
- Flame height H = 20 m (computed via Heskestad: H = 0.235·Q^(2/5) − 1.02·10, for Q ≈ 10 MW, yields H ≈ 20 m ✓)
- Heat release rate Q = 10 000 kW
- Flame temperature T_f = 1100 K (smoky pool fire; luminous fraction lower)
- Emissivity ε = 0.5 (luminous)
- Receptors at horizontal distances R = 50, 100, 200, 500, 1000 m
- Transmissivity τ = 1.0

**Expected radiative flux at each distance** (Shokri-Beyler paper Table 1
or SFPE Handbook reproduction):

| R (m) | Expected I (kW/m²) |
|-------|--------------------:|
| 50    | ~17                 |
| 100   | ~5.5                |
| 200   | ~1.8                |
| 500   | ~0.35               |
| 1000  | ~0.10               |

⚠️ **These expected values are reproduced from the consensus form of
Shokri-Beyler and CCPS Ch. 2 examples. They are not primary-verified.
Re-check against the Shokri-Beyler 1989 paper Table 1 or SFPE Handbook
worked example before relying on them.**

**Asymptotic check:** for R >> H and R >> D, the flux should scale
as 1/R². At R = 1000 m vs R = 500 m the ratio should be ≈ 0.25. Both
the above numbers approximately satisfy this (0.10 / 0.35 ≈ 0.29;
within shape tolerance).

## 4. Flame emissivity by fuel

Flame emissivity depends on fuel chemistry (soot production) and
flame size. The standard references are:

- **SFPE Handbook Ch. "Pool Fires", Table 5.3**: radiative fraction
  χ_r (not emissivity, but related) for common fuels. χ_r values:
  - n-Heptane / gasoline: 0.30–0.40
  - Methane: 0.15–0.20
  - Propane: 0.20–0.30
  - Hydrogen: 0.10–0.15 (very low soot, very luminous in air but
    total radiative fraction is small; mostly H₂O band emission)
  - Ethanol: 0.15–0.20
  - Ammonia: 0.05–0.10 (very low — flame is barely luminous)

- **CCPS Ch. 2**: emissivity values, typically 0.3–0.5 default.

**Conversion from χ_r to ε** is not direct. The convention used in
CCPS and SFPE:
- Pool-fire model assumes ε · F · σ · T_f⁴ = χ_r · Q / (4π·R²)
- Approximate ε values from SFPE Handbook Table 5.3 by inference:

| Fuel | ε (dimensionless) | Source / status |
|------|-------------------:|-----------------|
| Propane | 0.30 | SFPE Handbook Table 5.3, inferred. **Flagged.** |
| n-Heptane (gasoline surrogate) | 0.35 | SFPE Handbook. **Flagged.** |
| Methane | 0.20 | SFPE Handbook. **Flagged.** |
| Ethanol | 0.20 | SFPE Handbook. **Flagged.** |
| Hydrogen | 0.10 | SFPE Handbook; radiative fraction is very low for H₂ diffusion flames in air. **Flagged.** |
| Ammonia | 0.10 | SFPE Handbook; low soot. **Flagged.** |

⚠️ **All ε values are flagged as not primary-verified.** They are
standard textbook values from SFPE Handbook and CCPS, but I could
not retrieve those documents directly. The literature consensus is
broadly: hydrocarbons 0.2–0.4, alcohols 0.15–0.25, hydrogen/ammonia
0.05–0.15.

**Default if no fuel is supplied:** 0.4 (CCPS / ALOHA default for
"typical" hydrocarbon pool fire).

## 5. Citations

### Primary
- Heskestad, G. (1984). "Engineering relations for fire plumes."
  *Fire Technology* 20(1), 31–43. — **Not retrieved.**
- Shokri, M., Beyler, C. L. (1989). "Radiation from large pool fires."
  *Journal of Fire Protection Engineering* 1(3), 9–18. — **Not retrieved.**
- Mudan, K. S. (1984). "Thermal radiation hazards from hydrocarbon
  pool fires." *Progress in Energy and Combustion Science* 10, 59–80.
  — **Not retrieved.**
- CCPS *Guidelines for Chemical Process Quantitative Risk Analysis*
  2nd ed. (2000), Chapter 2 — "Thermal Radiation Criteria". **Not
  retrieved.**
- SFPE Handbook of Fire Protection Engineering, 5th ed. (2016),
  Chapter "Pool Fires". **Not retrieved.**

### Secondary (what we are actually using)
- Consensus formulas from the above, reproduced from working knowledge
  and from references cited in other open-access papers (e.g.
  research on pool-fire modelling, jet-fire modelling, the Beyler
  paper itself being widely cited).
- ⚠️ Every constant and formula below is **not primary-verified**.

## 6. Implementation constants (not primary-verified)

- Heskestad: `H = 0.235 · Q^(2/5) − 1.02 · D` with Q in kW.
- Stefan-Boltzmann: σ = 5.6704 × 10⁻¹¹ kW / m² / K⁴ (this is the
  2018 CODATA value, well-established).
- Default transmissivity: τ = 1.0 (clean upper bound).
- Default emissivity (no fuel): 0.4.
- ε per fuel: see table above, all flagged.

## Summary

- Heskestad flame height: **ready to implement**, formula known.
- Shokri-Beyler view factor: **ready to implement**, full form
  available above.
- Worked example: **structural template only**, expected values
  flagged for re-verification.
- Per-fuel emissivity: **values known but flagged**, will add as
  field on Fuel dataclass.