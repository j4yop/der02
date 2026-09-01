"""Tests for the fuel library."""

from __future__ import annotations

import pytest

from der02.fuels import (
    AMMONIA,
    DIESEL,
    ETHANOL,
    FUELS,
    GASOLINE,
    HYDROGEN,
    KEROSENE,
    METHANE,
    METHANOL,
    PROPANE,
    Fuel,
    get_fuel,
)


class TestFuelDataclass:
    def test_fuel_is_frozen(self):
        with pytest.raises((AttributeError, Exception)):
            PROPANE.name = "mutated"  # type: ignore[misc]

    def test_fuel_carries_required_fields(self):
        for fuel in FUELS.values():
            assert isinstance(fuel, Fuel)
            assert isinstance(fuel.name, str) and fuel.name
            assert isinstance(fuel.formula, str) and fuel.formula
            assert isinstance(fuel.cas, str) and fuel.cas
            assert isinstance(fuel.lhv_kj_kg, float) and fuel.lhv_kj_kg > 0
            assert isinstance(fuel.flame_temperature_k, float)
            assert fuel.flame_temperature_k > 1000  # sanity: combustion temps > 1000 K
            assert isinstance(fuel.nist_webbook_url, str)
            assert "webbook.nist.gov" in fuel.nist_webbook_url
            assert isinstance(fuel.emissivity, float)
            assert 0.0 < fuel.emissivity <= 1.0


class TestEmissivity:
    """Per-fuel emissivity from SFPE Handbook Table 5.3 — flagged
    not-primary-verified but pinned here so any change requires a
    citation update."""

    def test_propane_emissivity(self):
        assert PROPANE.emissivity == pytest.approx(0.30, rel=0.20)

    def test_gasoline_emissivity(self):
        assert GASOLINE.emissivity == pytest.approx(0.35, rel=0.20)

    def test_methane_emissivity(self):
        assert METHANE.emissivity == pytest.approx(0.20, rel=0.20)

    def test_ethanol_emissivity(self):
        assert ETHANOL.emissivity == pytest.approx(0.20, rel=0.20)

    def test_hydrogen_emissivity_low(self):
        # Hydrogen diffusion flames have very low radiative fraction.
        assert HYDROGEN.emissivity == pytest.approx(0.10, rel=0.30)
        assert HYDROGEN.emissivity < 0.20

    def test_ammonia_emissivity_low(self):
        # Ammonia flames are barely luminous.
        assert AMMONIA.emissivity == pytest.approx(0.10, rel=0.30)
        assert AMMONIA.emissivity < 0.20


class TestDiesel:
    """Diesel (n-dodecane surrogate). NIST WebBook data.

    ΔcH°(liquid) = -8086 kJ/mol (Prosen & Rossini 1945). 13 H₂O per mole.
    LHV = (8086 - 13·44.01) / 0.1703348 ≈ 44,100 kJ/kg.
    """

    def test_lhv_matches_nist_derivation(self):
        # C₁₂H₂₆ + 18.5 O₂ → 12 CO₂ + 13 H₂O; 13 mol H₂O per mol fuel.
        n_water = 13
        lhv_per_mol = 8086.0 - n_water * 44.01  # kJ/mol
        lhv_per_kg = lhv_per_mol / 0.1703348 * 1000 / 1000  # kJ/kg
        assert DIESEL.lhv_kj_kg == pytest.approx(lhv_per_kg, rel=0.01)

    def test_molecular_weight_in_vapor_density(self):
        # Dodecane MW = 170.3348 g/mol.
        # Vapor density at 15 °C 1 atm from ideal gas.
        expected = 170.3348 / 22.414 * 273.15 / 288.15
        assert DIESEL.vapor_density_kg_m3 == pytest.approx(expected, rel=1e-6)

    def test_diesel_is_liquid(self):
        assert DIESEL.liquid_density_kg_m3 is not None
        assert 700 < DIESEL.liquid_density_kg_m3 < 800

    def test_diesel_denser_than_air(self):
        # C₁₂H₂₆ is much heavier than air.
        assert DIESEL.vapor_relative_to_air > 4.0


class TestKerosene:
    """Kerosene (n-dodecane surrogate for Jet A).

    Kerosene is a C₁₀–C₁₆ mixture in reality; n-dodecane is the standard
    clean surrogate.
    """

    def test_kerosene_uses_dodecane_constants(self):
        assert KEROSENE.lhv_kj_kg == pytest.approx(DIESEL.lhv_kj_kg, rel=1e-9)
        assert KEROSENE.cas == DIESEL.cas

    def test_kerosene_distinct_from_diesel(self):
        # Different fuel names; kerosene is a Jet A mix, diesel is heavier.
        assert KEROSENE.name != DIESEL.name
        assert KEROSENE.formula != DIESEL.formula


class TestMethanol:
    """Methanol (CH₃OH, CAS 67-56-1). LHV derivation from HHV."""

    def test_lhv_matches_derivation(self):
        # HHV = 725.7 kJ/mol (Wikipedia citing primary).
        # 2 H₂O per mole. LHV = (725.7 - 2·44.01) / 0.032042 ≈ 19,910 kJ/kg.
        hhv_kj_mol = 725.7
        n_water = 2  # CH₃OH + 1.5 O₂ → CO₂ + 2 H₂O
        lhv_per_mol = hhv_kj_mol - n_water * 44.01
        lhv_per_kg = lhv_per_mol / 0.032042
        assert METHANOL.lhv_kj_kg == pytest.approx(lhv_per_kg, rel=0.01)

    def test_methanol_denser_than_air(self):
        # MW 32 > air MW 29, so vapor heavier than air.
        assert METHANOL.vapor_relative_to_air > 1.0

    def test_methanol_is_liquid(self):
        assert METHANOL.liquid_density_kg_m3 is not None
        assert 750 < METHANOL.liquid_density_kg_m3 < 850


class TestKnownFuels:
    def test_all_nine_fuels_present(self):
        assert set(FUELS.keys()) == {
            "propane", "gasoline", "methane", "ethanol", "hydrogen",
            "ammonia", "diesel", "kerosene", "methanol",
        }

    def test_get_fuel_returns_correct_instance(self):
        assert get_fuel("propane") is PROPANE
        assert get_fuel("hydrogen") is HYDROGEN
        assert get_fuel("diesel") is DIESEL
        assert get_fuel("kerosene") is KEROSENE
        assert get_fuel("methanol") is METHANOL


class TestGetFuelErrors:
    def test_unknown_fuel_raises(self):
        with pytest.raises(KeyError) as exc_info:
            get_fuel("water")
        msg = str(exc_info.value)
        assert "water" in msg
        assert "propane" in msg  # available fuels listed

    def test_empty_string_raises(self):
        with pytest.raises(KeyError):
            get_fuel("")


class TestNISTValues:
    """Pin the NIST-derived values so they don't drift without a citation update."""

    def test_propane_lhv(self):
        # NIST WebBook C₃H₈: ΔcH°(gas) = 2219.2 kJ/mol, MW = 44.0956
        # LHV = (2219.2 - 4 × 44.01) / 0.0440956 ≈ 46 340 kJ/kg
        assert PROPANE.lhv_kj_kg == pytest.approx(46_340, rel=0.01)

    def test_hydrogen_lhv(self):
        # CODATA / Chase 1998: ΔcH°(gas) = 285.83 kJ/mol, MW = 2.01588
        # LHV = (285.83 - 44.01) / 0.00201588 ≈ 119 950 kJ/kg
        assert HYDROGEN.lhv_kj_kg == pytest.approx(119_950, rel=0.01)

    def test_methane_lhv(self):
        # NIST WebBook CH₄: ΔcH°(gas) = 890.7 kJ/mol, MW = 16.04
        # LHV = (890.7 - 2 × 44.01) / 0.01604 ≈ 50 030 kJ/kg
        assert METHANE.lhv_kj_kg == pytest.approx(50_030, rel=0.01)

    def test_ethanol_lhv(self):
        assert ETHANOL.lhv_kj_kg == pytest.approx(26_830, rel=0.01)

    def test_gasoline_heptane_lhv(self):
        assert GASOLINE.lhv_kj_kg == pytest.approx(44_560, rel=0.01)

    def test_ammonia_lhv(self):
        assert AMMONIA.lhv_kj_kg == pytest.approx(18_600, rel=0.02)


class TestGasesHaveNoLiquidDensity:
    """Gaseous fuels stored under pressure should not pretend to have a
    standard 15 °C liquid density."""

    def test_methane_liquid_density_is_none(self):
        assert METHANE.liquid_density_kg_m3 is None

    def test_hydrogen_liquid_density_is_none(self):
        assert HYDROGEN.liquid_density_kg_m3 is None

    def test_liquids_have_density(self):
        for fuel in (PROPANE, GASOLINE, ETHANOL, AMMONIA):
            assert fuel.liquid_density_kg_m3 is not None
            assert fuel.liquid_density_kg_m3 > 0


class TestVaporDensities:
    def test_hydrogen_lighter_than_air(self):
        assert HYDROGEN.vapor_relative_to_air < 1.0

    def test_propane_heavier_than_air(self):
        assert PROPANE.vapor_relative_to_air > 1.0

    def test_methane_lighter_than_air(self):
        assert METHANE.vapor_relative_to_air < 1.0
