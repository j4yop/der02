"""Tests for the TNO Multi-Energy blast overpressure model."""

from __future__ import annotations

import pytest

from der02.blast import (
    DEFAULT_AMBIENT_PA,
    blast_overpressure,
)
from der02.thresholds import classify_blast


class TestBlastOverpressureSanity:
    def test_returns_positive_overpressure(self):
        assert blast_overpressure(100.0, 1.0e9) > 0

    def test_overpressure_decreases_with_distance(self):
        near = blast_overpressure(50.0, 1.0e9)
        far = blast_overpressure(500.0, 1.0e9)
        assert near > far

    def test_overpressure_increases_with_energy(self):
        small = blast_overpressure(500.0, 1.0e9)
        large = blast_overpressure(500.0, 1.0e10)
        assert large > small


class TestBlastValidation:
    def test_negative_distance_raises(self):
        with pytest.raises(ValueError, match="distance_m"):
            blast_overpressure(-1.0, 1.0e9)

    def test_zero_distance_raises(self):
        with pytest.raises(ValueError, match="distance_m"):
            blast_overpressure(0.0, 1.0e9)

    def test_negative_energy_raises(self):
        with pytest.raises(ValueError, match="energy_joules"):
            blast_overpressure(100.0, -1.0)

    def test_zero_energy_raises(self):
        with pytest.raises(ValueError, match="energy_joules"):
            blast_overpressure(100.0, 0.0)

    def test_negative_ambient_raises(self):
        with pytest.raises(ValueError, match="ambient_pressure_pa"):
            blast_overpressure(100.0, 1.0e9, ambient_pressure_pa=-1.0)


class TestBlastClamping:
    def test_far_field_clamps_to_Z_max_endpoint(self):
        # Z → ∞ → clamped to Δp at Z = 100 (~300 Pa).
        p = blast_overpressure(10_000_000.0, 1.0e9)
        assert p == pytest.approx(300.0, rel=1e-3)

    def test_near_field_clamps_to_Z_min_endpoint(self):
        # Z → 0 → clamped to Δp at Z = 0.1 (~1 MPa).
        p = blast_overpressure(1.0, 1.0e9)
        assert p == pytest.approx(1_000_000.0, rel=1e-3)


class TestWorkedExample:
    """Worked example from `.scratch/tno-research.md` corrected for the
    full Sachs formula Z = R / (E/P₀)^(1/3).

    1000 kg methane cloud → E = 5 × 10¹⁰ J, P₀ = 101 325 Pa.

    Correct Sachs scaled distances:
        R =   100 m → Z = 1.27  → curve ~55 kPa   → danger
        R =   500 m → Z = 6.33  → curve ~6 kPa    → caution
        R =  1500 m → Z = 18.98 → curve ~1.7 kPa  → safe
        R = 30000 m → Z = 379   → clamped to 300 Pa → safe

    ⚠️ Source flagged not-primary-verified. Tolerance ±25 %.
    """

    def test_1000kg_methane_at_100m_is_danger(self):
        p = blast_overpressure(100.0, 5.0e10)
        assert p == pytest.approx(55_000.0, rel=0.30)
        assert classify_blast(p) == "danger"

    def test_1000kg_methane_at_500m(self):
        # Curve says ~6 kPa at Z = 6.33 → safe (just below 10 kPa caution).
        p = blast_overpressure(500.0, 5.0e10)
        assert p == pytest.approx(6_000.0, rel=0.30)
        assert p < 10_000.0  # below caution threshold

    def test_1000kg_methane_at_1500m_is_safe(self):
        p = blast_overpressure(1500.0, 5.0e10)
        assert p < 10_000.0
        assert classify_blast(p) in {"safe", "caution"}

    def test_1000kg_methane_at_30km_is_safe(self):
        p = blast_overpressure(30_000.0, 5.0e10)
        # Z far beyond the curve; clamps to Z=100 endpoint (~300 Pa).
        assert p == pytest.approx(300.0, rel=0.05)
        assert classify_blast(p) == "safe"


class TestCurveShape:
    def test_curve_at_Z_1(self):
        e = 1.0e10
        r = (e / DEFAULT_AMBIENT_PA) ** (1.0 / 3.0)  # gives Z = 1
        p = blast_overpressure(r, e)
        assert p == pytest.approx(70_000.0, rel=0.2)

    def test_curve_at_Z_4(self):
        e = 1.0e10
        r = 4.0 * (e / DEFAULT_AMBIENT_PA) ** (1.0 / 3.0)
        p = blast_overpressure(r, e)
        assert p == pytest.approx(10_000.0, rel=0.2)


class TestAmbientPressureEffect:
    def test_higher_ambient_decreases_overpressure(self):
        # Higher P₀ → (E/P₀)^(1/3) is smaller → Z is larger → Δp_s is smaller.
        # (Higher ambient pressure means a *given* energy is "denser" relative
        # to ambient, so the scaled distance is larger — counter-intuitive but
        # correct per the Sachs definition.)
        p_low = blast_overpressure(100.0, 1.0e9, ambient_pressure_pa=80_000.0)
        p_high = blast_overpressure(100.0, 1.0e9, ambient_pressure_pa=120_000.0)
        assert p_high < p_low
