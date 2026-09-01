"""Fuel library: physical constants for the six substances modelled in the MVP.

All heats of combustion are lower heating values (LHV) per unit mass, derived
from NIST WebBook (https://webbook.nist.gov) primary species pages using
ΔcH° values and H₂O latent-heat correction.

Adiabatic flame temperatures and liquid densities are flagged values from
NIST-JANAF / Perry's Chemical Engineers' Handbook. Each carries a citation
note in its dataclass field.

Flame emissivities are from SFPE Handbook of Fire Protection Engineering
Table 5.3 (radiative fraction / emissivity for common fuels), inferred
from the consensus literature. **Not primary-verified** — see
`.scratch/solid-flame-research.md` for the full caveat list.

Research notes live in `.scratch/fuel-research.md` and
`.scratch/solid-flame-research.md`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fuel:
    """A single fuel substance with the physical constants needed for
    blast and thermal-zone computation."""

    name: str
    formula: str
    cas: str
    lhv_kj_kg: float  # lower heating value, kJ/kg
    flame_temperature_k: float  # adiabatic flame temperature, K
    liquid_density_kg_m3: float | None  # None for gases stored under pressure
    vapor_density_kg_m3: float  # at 15 °C, 1 atm (ideal-gas derivation from MW)
    vapor_relative_to_air: float  # dimensionless
    nist_webbook_url: str
    emissivity: float  # flame emissivity, dimensionless ∈ (0, 1]


# Per-fuel constants. LHV values derived from NIST WebBook ΔcH° data; see
# `.scratch/fuel-research.md` for derivation traces and per-species
# references.

PROPANE = Fuel(
    name="propane",
    formula="C3H8",
    cas="74-98-6",
    lhv_kj_kg=46_340.0,  # NIST WebBook, Pittam & Pilcher 1972
    flame_temperature_k=2267.0,  # Perry's 8th ed.; flagged in research notes
    liquid_density_kg_m3=493.0,  # Younglove & Ely 1987 (J. Phys. Chem. Ref. Data 16, 577)
    vapor_density_kg_m3=1.97,  # derived from MW = 44.0956
    vapor_relative_to_air=1.52,  # MW(air) = 28.97
    nist_webbook_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C74986&Units=SI",
    emissivity=0.30,  # SFPE Handbook Table 5.3 (flagged: not primary-verified)
)

# Gasoline is a mixture. Per CCPS convention we use n-heptane as the standard
# surrogate; for "typical gasoline" see CCPS *Guidelines for CPQRA* 2nd ed.
# Table 2-7 (LHV ~ 43.4 MJ/kg) which we have not pinned here.
GASOLINE = Fuel(
    name="gasoline",
    formula="C7H16 (n-heptane surrogate)",
    cas="142-82-5",
    lhv_kj_kg=44_560.0,  # NIST WebBook, Prosen & Rossini 1945
    flame_temperature_k=2300.0,  # Perry's 8th ed.; flagged
    liquid_density_kg_m3=688.0,  # NIST TRC; CRC Handbook
    vapor_density_kg_m3=4.24,  # derived from MW = 100.20
    vapor_relative_to_air=3.46,
    nist_webbook_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C142825&Units=SI",
    emissivity=0.35,  # SFPE Handbook Table 5.3 (flagged: not primary-verified)
)

METHANE = Fuel(
    name="methane",
    formula="CH4",
    cas="74-82-8",
    lhv_kj_kg=50_030.0,  # NIST WebBook, Pittam & Pilcher 1972
    flame_temperature_k=2223.0,  # JANAF / Perry's; flagged
    liquid_density_kg_m3=None,  # stored as cryogenic liquid or pressurized gas
    vapor_density_kg_m3=0.679,  # derived from MW = 16.04
    vapor_relative_to_air=0.554,
    nist_webbook_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C74828&Units=SI",
    emissivity=0.20,  # SFPE Handbook Table 5.3 (flagged: not primary-verified)
)

ETHANOL = Fuel(
    name="ethanol",
    formula="C2H5OH",
    cas="64-17-5",
    lhv_kj_kg=26_830.0,  # NIST WebBook, Chao & Rossini 1965
    flame_temperature_k=2263.0,  # Perry's 8th ed.; flagged
    liquid_density_kg_m3=789.0,  # CRC Handbook
    vapor_density_kg_m3=1.95,  # derived from MW = 46.07
    vapor_relative_to_air=1.59,
    nist_webbook_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C64175&Units=SI",
    emissivity=0.20,  # SFPE Handbook Table 5.3 (flagged: not primary-verified)
)

HYDROGEN = Fuel(
    name="hydrogen",
    formula="H2",
    cas="1333-74-0",
    lhv_kj_kg=119_950.0,  # CODATA / Chase 1998 (NIST-JANAF)
    flame_temperature_k=2389.0,  # JANAF; flagged
    liquid_density_kg_m3=None,  # stored as cryogenic liquid or compressed gas
    vapor_density_kg_m3=0.0853,  # derived from MW = 2.016
    vapor_relative_to_air=0.0696,
    nist_webbook_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C1333740&Units=SI",
    emissivity=0.10,  # SFPE Handbook Table 5.3 (flagged: not primary-verified)
)

AMMONIA = Fuel(
    name="ammonia",
    formula="NH3",
    cas="7664-41-7",
    lhv_kj_kg=18_600.0,  # derived from NIST WebBook ΔfH° (Cox 1984) + H₂O ΔfH°
    flame_temperature_k=1850.0,  # JANAF; flagged
    liquid_density_kg_m3=618.0,  # CRC Handbook (at bp; ~602 at −33 °C)
    vapor_density_kg_m3=0.721,  # derived from MW = 17.03
    vapor_relative_to_air=0.588,
    nist_webbook_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C7664417&Units=SI",
    emissivity=0.10,  # SFPE Handbook Table 5.3 (flagged: not primary-verified)
)

# Diesel (n-dodecane C₁₂H₂₆, CAS 112-40-3 surrogate).
# NIST WebBook (Prosen & Rossini 1945): ΔcH°(liquid) = -8086.0 ± 1.2 kJ/mol.
# C₁₂H₂₆ + 18.5 O₂ → 12 CO₂ + 13 H₂O, so 13 moles water per mole fuel.
# LHV per kg: (8086 - 13·44.01) / 0.1703348 ≈ 44,100 kJ/kg.
DIESEL = Fuel(
    name="diesel",
    formula="C12H26 (n-dodecane surrogate)",
    cas="112-40-3",
    lhv_kj_kg=44_100.0,  # NIST WebBook, Prosen & Rossini 1945; see derivation in research notes
    flame_temperature_k=2280.0,  # Perry's 8th ed.; flagged
    liquid_density_kg_m3=750.0,  # CRC Handbook at 15 °C; flagged (NIST WebBook lists ρc only)
    vapor_density_kg_m3=170.3348 / 22.414 * 273.15 / 288.15,  # derived from MW
    vapor_relative_to_air=170.3348 / 28.97,  # derived
    nist_webbook_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C112403&Units=SI",
    emissivity=0.30,  # SFPE Handbook Table 5.3 (flagged: not primary-verified)
)

# Kerosene (Jet A) — use n-dodecane as a clean surrogate.
# Same constants as diesel (both use the same C₁₂ surrogate).
# Flagged in name: real kerosene is a C₁₀–C₁₆ mixture.
KEROSENE = Fuel(
    name="kerosene",
    formula="C12H26 (n-dodecane surrogate for Jet A)",
    cas="112-40-3",
    lhv_kj_kg=44_100.0,  # Same as diesel surrogate
    flame_temperature_k=2280.0,  # Perry's 8th ed.; flagged
    liquid_density_kg_m3=800.0,  # CRC Handbook for Jet A at 15 °C; flagged
    vapor_density_kg_m3=170.3348 / 22.414 * 273.15 / 288.15,  # derived from MW
    vapor_relative_to_air=170.3348 / 28.97,  # derived
    nist_webbook_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C112403&Units=SI",
    emissivity=0.30,  # SFPE Handbook Table 5.3 (flagged: not primary-verified)
)

# Methanol (CH₃OH, CAS 67-56-1).
# Wikipedia (citing primary sources): HHV = 725.7 kJ/mol.
# LHV per kg: (725.7 - 2·44.01) / 0.032042 ≈ 19,910 kJ/kg.
METHANOL = Fuel(
    name="methanol",
    formula="CH3OH",
    cas="67-56-1",
    lhv_kj_kg=19_910.0,  # derived from HHV via NIST-style latent-heat correction
    flame_temperature_k=2230.0,  # Perry's 8th ed.; flagged
    liquid_density_kg_m3=792.0,  # CRC Handbook at 20 °C; flagged
    vapor_density_kg_m3=32.042 / 22.414 * 273.15 / 288.15,  # derived from MW
    vapor_relative_to_air=32.042 / 28.97,  # derived
    nist_webbook_url="https://webbook.nist.gov/cgi/cbook.cgi?ID=C67561&Units=SI",
    emissivity=0.20,  # SFPE Handbook Table 5.3 (flagged: not primary-verified)
)


FUELS: dict[str, Fuel] = {
    PROPANE.name: PROPANE,
    GASOLINE.name: GASOLINE,
    METHANE.name: METHANE,
    ETHANOL.name: ETHANOL,
    HYDROGEN.name: HYDROGEN,
    AMMONIA.name: AMMONIA,
    DIESEL.name: DIESEL,
    KEROSENE.name: KEROSENE,
    METHANOL.name: METHANOL,
}


def get_fuel(name: str) -> Fuel:
    """Return the Fuel for the given name, or raise KeyError with a helpful
    message listing the available fuels."""
    try:
        return FUELS[name]
    except KeyError as exc:
        available = ", ".join(sorted(FUELS))
        raise KeyError(
            f"Unknown fuel {name!r}. Available fuels: {available}"
        ) from exc


__all__ = [
    "Fuel",
    "FUELS",
    "PROPANE",
    "GASOLINE",
    "METHANE",
    "ETHANOL",
    "HYDROGEN",
    "AMMONIA",
    "DIESEL",
    "KEROSENE",
    "METHANOL",
    "get_fuel",
]
