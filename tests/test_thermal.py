"""Tests for the point-source thermal radiation model."""

from __future__ import annotations

import pytest

from der02.thermal import (
    DEFAULT_RADIATIVE_FRACTION,
    DEFAULT_TRANSMISSIVITY,
    STEFAN_BOLTZMANN_KW,
    point_source_flux,
)


class TestPointSourceSanity:
    def test_returns_positive_flux(self):
        assert point_source_flux(10.0, 1.0e4) > 0

    def test_flux_decreases_with_distance(self):
        near = point_source_flux(10.0, 1.0e4)
        far = point_source_flux(100.0, 1.0e4)
        assert near > far

    def test_flux_proportional_to_Q(self):
        a = point_source_flux(50.0, 1.0e4)
        b = point_source_flux(50.0, 2.0e4)
        assert b == pytest.approx(2.0 * a, rel=1e-9)

    def test_flux_inverse_square_with_distance(self):
        f1 = point_source_flux(50.0, 1.0e4)
        f2 = point_source_flux(100.0, 1.0e4)
        assert f1 == pytest.approx(4.0 * f2, rel=1e-9)

    def test_transmissivity_scales_linearly(self):
        f_full = point_source_flux(50.0, 1.0e4, transmissivity=1.0)
        f_half = point_source_flux(50.0, 1.0e4, transmissivity=0.5)
        assert f_half == pytest.approx(0.5 * f_full, rel=1e-9)

    def test_radiative_fraction_scales_linearly(self):
        f_full = point_source_flux(50.0, 1.0e4, radiative_fraction=1.0)
        f_half = point_source_flux(50.0, 1.0e4, radiative_fraction=0.5)
        assert f_half == pytest.approx(0.5 * f_full, rel=1e-9)


class TestPointSourceValidation:
    def test_negative_distance_raises(self):
        with pytest.raises(ValueError, match="distance_m"):
            point_source_flux(-1.0, 1.0e4)

    def test_zero_distance_raises(self):
        with pytest.raises(ValueError, match="distance_m"):
            point_source_flux(0.0, 1.0e4)

    def test_negative_Q_raises(self):
        with pytest.raises(ValueError, match="heat_release_rate_kw"):
            point_source_flux(10.0, -1.0)

    def test_zero_Q_raises(self):
        with pytest.raises(ValueError, match="heat_release_rate_kw"):
            point_source_flux(10.0, 0.0)

    def test_transmissivity_zero_raises(self):
        with pytest.raises(ValueError, match="transmissivity"):
            point_source_flux(10.0, 1.0e4, transmissivity=0.0)

    def test_transmissivity_above_one_raises(self):
        with pytest.raises(ValueError, match="transmissivity"):
            point_source_flux(10.0, 1.0e4, transmissivity=1.5)

    def test_radiative_fraction_zero_raises(self):
        with pytest.raises(ValueError, match="radiative_fraction"):
            point_source_flux(10.0, 1.0e4, radiative_fraction=0.0)

    def test_radiative_fraction_above_one_raises(self):
        with pytest.raises(ValueError, match="radiative_fraction"):
            point_source_flux(10.0, 1.0e4, radiative_fraction=1.5)


class TestPointSourceNumeric:
    """Numerical sanity: 10 MW pool fire, 50 m → ~0.32 kW/m² (safe)."""

    def test_10MW_at_50m(self):
        flux = point_source_flux(50.0, 10_000.0)
        assert flux == pytest.approx(0.318, rel=1e-2)

    def test_10MW_at_10m(self):
        flux = point_source_flux(10.0, 10_000.0)
        assert flux == pytest.approx(7.96, rel=1e-2)


class TestModuleConstants:
    def test_stefan_boltzmann_value(self):
        assert STEFAN_BOLTZMANN_KW == pytest.approx(5.6704e-11, rel=1e-9)

    def test_default_transmissivity(self):
        assert 0 < DEFAULT_TRANSMISSIVITY <= 1

    def test_default_radiative_fraction(self):
        assert 0 < DEFAULT_RADIATIVE_FRACTION <= 1
