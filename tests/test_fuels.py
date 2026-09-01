"""Tests for the fuel library."""

from __future__ import annotations

import pytest

from der02.fuels import (
    AMMONIA,
    ETHANOL,
    FUELS,
    GASOLINE,
    HYDROGEN,
    METHANE,
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


class TestKnownFuels:
    def test_all_six_fuels_present(self):
        assert set(FUELS.keys()) == {"propane", "gasoline", "methane", "ethanol", "hydrogen", "ammonia"}

    def test_get_fuel_returns_correct_instance(self):
        assert get_fuel("propane") is PROPANE
        assert get_fuel("hydrogen") is HYDROGEN


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
