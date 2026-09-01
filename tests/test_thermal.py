"""Tests for the thermal radiation models."""

from __future__ import annotations

import pytest

from der02.thermal import (
    DEFAULT_EMISSIVITY,
    DEFAULT_RADIATIVE_FRACTION,
    DEFAULT_TRANSMISSIVITY,
    STEFAN_BOLTZMANN_KW,
    flame_height_heskestad,
    point_source_flux,
    shokri_beyler_view_factor,
    solid_flame_flux,
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

    def test_default_emissivity(self):
        assert 0 < DEFAULT_EMISSIVITY <= 1


class TestHeskestadFlameHeight:
    """Heskestad (1984) simplified dimensional form:

        H = 0.235 · Q^(2/5)        [Q in kW, H in m]

    The classical Heskestad formula includes a −1.02·D correction term
    for very small pool diameters; we omit it (see thermal.py for
    rationale). pool_diameter_m is accepted but not consumed in the
    simplified form.
    """

    def test_returns_positive_height(self):
        h = flame_height_heskestad(heat_release_rate_kw=1000.0, pool_diameter_m=2.0)
        assert h > 0.0

    def test_returns_positive_for_typical_fire(self):
        # 1 MW, 2 m diameter → reasonable flame height.
        h = flame_height_heskestad(heat_release_rate_kw=1000.0, pool_diameter_m=2.0)
        assert h > 1.0

    def test_scales_with_Q(self):
        # Higher Q → higher H (Q^(2/5) is monotone).
        small = flame_height_heskestad(heat_release_rate_kw=100.0, pool_diameter_m=1.0)
        large = flame_height_heskestad(heat_release_rate_kw=10_000.0, pool_diameter_m=1.0)
        assert large > small

    def test_scales_correctly_with_Q(self):
        # 100× Q → H scales by 100^(2/5) ≈ 6.31.
        q1, q2 = 100.0, 10_000.0
        h1 = flame_height_heskestad(heat_release_rate_kw=q1, pool_diameter_m=1.0)
        h2 = flame_height_heskestad(heat_release_rate_kw=q2, pool_diameter_m=1.0)
        assert h2 / h1 == pytest.approx(100**0.4, rel=1e-9)

    def test_pool_diameter_accepted_but_not_consumed(self):
        # Pool diameter is informational; result depends only on Q.
        h_a = flame_height_heskestad(heat_release_rate_kw=1000.0, pool_diameter_m=2.0)
        h_b = flame_height_heskestad(heat_release_rate_kw=1000.0, pool_diameter_m=10.0)
        assert h_a == h_b

    def test_validation(self):
        with pytest.raises(ValueError, match="heat_release_rate_kw"):
            flame_height_heskestad(heat_release_rate_kw=0.0, pool_diameter_m=1.0)
        with pytest.raises(ValueError, match="heat_release_rate_kw"):
            flame_height_heskestad(heat_release_rate_kw=-1.0, pool_diameter_m=1.0)
        with pytest.raises(ValueError, match="pool_diameter_m"):
            flame_height_heskestad(heat_release_rate_kw=1000.0, pool_diameter_m=0.0)
        with pytest.raises(ValueError, match="pool_diameter_m"):
            flame_height_heskestad(heat_release_rate_kw=1000.0, pool_diameter_m=-1.0)


class TestShokriBeylerViewFactor:
    """Shokri-Beyler (1989) view factor F(R, H, D).

    Sanity bounds:
      - F ∈ [0, 1]
      - F → 1 as R → 0 (receptor at the flame surface)
      - F → 0 as R → ∞ (receptor far away)
      - Larger H or D → larger F at fixed R (more flame visible)
    """

    def test_returns_value_in_unit_interval(self):
        f = shokri_beyler_view_factor(
            distance_m=100.0, flame_height_m=20.0, flame_diameter_m=10.0
        )
        assert 0.0 <= f <= 1.0

    def test_larger_flame_gives_larger_view_factor(self):
        # At fixed R, a bigger flame (taller or wider) has higher F.
        small = shokri_beyler_view_factor(
            distance_m=100.0, flame_height_m=5.0, flame_diameter_m=2.0
        )
        big = shokri_beyler_view_factor(
            distance_m=100.0, flame_height_m=20.0, flame_diameter_m=10.0
        )
        assert big > small

    def test_view_factor_decreases_with_distance(self):
        kwargs = dict(flame_height_m=20.0, flame_diameter_m=10.0)
        near = shokri_beyler_view_factor(distance_m=50.0, **kwargs)
        far = shokri_beyler_view_factor(distance_m=500.0, **kwargs)
        assert near > far

    def test_far_field_decays_as_1_over_R_squared(self):
        # For R >> H, D, F should scale as H·D / (π·R²) approximately.
        # So F(R1) / F(R2) ≈ (R2/R1)² for R1, R2 large.
        kwargs = dict(flame_height_m=20.0, flame_diameter_m=10.0)
        f1 = shokri_beyler_view_factor(distance_m=200.0, **kwargs)
        f2 = shokri_beyler_view_factor(distance_m=400.0, **kwargs)
        ratio = f1 / f2
        # Expect ratio ≈ 4; allow generous tolerance for the asymptotic
        # regime not being perfect.
        assert 2.0 <= ratio <= 8.0

    def test_validation(self):
        with pytest.raises(ValueError, match="distance_m"):
            shokri_beyler_view_factor(
                distance_m=0.0, flame_height_m=20.0, flame_diameter_m=10.0
            )
        with pytest.raises(ValueError, match="distance_m"):
            shokri_beyler_view_factor(
                distance_m=-1.0, flame_height_m=20.0, flame_diameter_m=10.0
            )
        with pytest.raises(ValueError, match="flame_height_m"):
            shokri_beyler_view_factor(
                distance_m=100.0, flame_height_m=0.0, flame_diameter_m=10.0
            )
        with pytest.raises(ValueError, match="flame_diameter_m"):
            shokri_beyler_view_factor(
                distance_m=100.0, flame_height_m=20.0, flame_diameter_m=0.0
            )


class TestSolidFlameFlux:
    def test_returns_positive_flux(self):
        f = solid_flame_flux(
            distance_m=100.0,
            flame_height_m=20.0,
            flame_diameter_m=10.0,
            flame_temperature_k=2200.0,
            emissivity=0.35,
        )
        assert f > 0

    def test_flux_decreases_with_distance(self):
        kwargs = dict(
            flame_height_m=20.0,
            flame_diameter_m=10.0,
            flame_temperature_k=2200.0,
            emissivity=0.35,
        )
        near = solid_flame_flux(distance_m=50.0, **kwargs)
        far = solid_flame_flux(distance_m=500.0, **kwargs)
        assert near > far

    def test_flux_proportional_to_emissivity(self):
        kwargs = dict(
            distance_m=100.0,
            flame_height_m=20.0,
            flame_diameter_m=10.0,
            flame_temperature_k=2200.0,
        )
        low = solid_flame_flux(emissivity=0.2, **kwargs)
        high = solid_flame_flux(emissivity=0.4, **kwargs)
        assert high == pytest.approx(2.0 * low, rel=1e-9)

    def test_flux_proportional_to_t_to_fourth(self):
        # Doubling T_f increases flux by 2⁴ = 16.
        kwargs = dict(
            distance_m=100.0,
            flame_height_m=20.0,
            flame_diameter_m=10.0,
            emissivity=0.35,
        )
        cool = solid_flame_flux(flame_temperature_k=1100.0, **kwargs)
        hot = solid_flame_flux(flame_temperature_k=2200.0, **kwargs)
        assert hot == pytest.approx(16.0 * cool, rel=1e-6)

    def test_transmissivity_scales_linearly(self):
        kwargs = dict(
            distance_m=100.0,
            flame_height_m=20.0,
            flame_diameter_m=10.0,
            flame_temperature_k=2200.0,
            emissivity=0.35,
        )
        full = solid_flame_flux(transmissivity=1.0, **kwargs)
        half = solid_flame_flux(transmissivity=0.5, **kwargs)
        assert half == pytest.approx(0.5 * full, rel=1e-9)

    def test_validation(self):
        with pytest.raises(ValueError, match="distance_m"):
            solid_flame_flux(
                distance_m=0.0, flame_height_m=20.0,
                flame_diameter_m=10.0, flame_temperature_k=2200.0,
                emissivity=0.35,
            )
        with pytest.raises(ValueError, match="flame_temperature_k"):
            solid_flame_flux(
                distance_m=100.0, flame_height_m=20.0,
                flame_diameter_m=10.0, flame_temperature_k=500.0,
                emissivity=0.35,
            )
        with pytest.raises(ValueError, match="emissivity"):
            solid_flame_flux(
                distance_m=100.0, flame_height_m=20.0,
                flame_diameter_m=10.0, flame_temperature_k=2200.0,
                emissivity=1.5,
            )


class TestSolidFlameWorkedExample:
    """Worked example from `.scratch/solid-flame-research.md` §3.

    ⚠️ Expected values are **flagged as not primary-verified** and the
    numerical view-factor integration has not been cross-checked
    against the SFPE Handbook (the book was unreachable during
    research). These tests assert *shape* and *order of magnitude*
    rather than exact absolute values.

    Setup: D = 10 m, H = 20 m, T_f = 1100 K, ε = 0.5, τ = 1.0
    Receptors at R = 50, 100, 200, 500, 1000 m.
    """

    Kwargs = dict(
        flame_height_m=20.0,
        flame_diameter_m=10.0,
        flame_temperature_k=1100.0,
        emissivity=0.5,
    )

    def test_flux_at_100m_is_positive(self):
        # Should be a small positive value; we can't pin the exact
        # magnitude without the SFPE Handbook cross-check.
        f = solid_flame_flux(distance_m=100.0, **self.Kwargs)
        assert 0.0 < f < 100.0

    def test_far_field_decays_as_1_over_R_squared(self):
        # Flux at R=500 vs R=1000 should ratio ~4 (1/R² decay).
        f500 = solid_flame_flux(distance_m=500.0, **self.Kwargs)
        f1000 = solid_flame_flux(distance_m=1000.0, **self.Kwargs)
        # Generous tolerance because the asymptotic regime isn't
        # perfect at these distances.
        assert 2.0 <= (f500 / f1000) <= 8.0
