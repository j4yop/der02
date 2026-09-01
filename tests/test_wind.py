"""Tests for the wind distortion model."""

from __future__ import annotations

import pytest

from der02.wind import (
    DEFAULT_WIND_COUPLING,
    bearing_from_source,
    effective_distance,
)


class TestEffectiveDistanceZeroWind:
    def test_zero_wind_returns_real_distance(self):
        d = effective_distance(100.0, 90.0, 180.0, wind_speed_m_s=0.0)
        assert d == pytest.approx(100.0, rel=1e-9)


class TestEffectiveDistanceCrosswind:
    def test_crosswind_no_distortion(self):
        # Wind from S (blowing N), receptor E of source: crosswind.
        d = effective_distance(
            distance_m=100.0,
            bearing_to_receptor_deg=90.0,  # East of source
            wind_from_direction_deg=180.0,  # wind from S, blowing N
            wind_speed_m_s=10.0,
        )
        # Blow direction = 0° (N). Bearing 90° (E) is 90° from blow
        # direction → crosswind → cos = 0 → no distortion.
        assert d == pytest.approx(100.0, rel=1e-9)


class TestEffectiveDistanceDownwind:
    def test_pure_downwind_shorter_effective_distance(self):
        # Wind from N (blowing S), receptor S of source: pure downwind.
        d = effective_distance(
            distance_m=100.0,
            bearing_to_receptor_deg=180.0,  # S of source
            wind_from_direction_deg=0.0,    # wind from N (blowing S)
            wind_speed_m_s=10.0,
        )
        # Downwind: stretch = 1 / (1 + 0.1*10*1) = 1/2 = 0.5 → d = 50.
        assert d < 100.0
        assert d == pytest.approx(50.0, rel=1e-9)

    def test_stronger_wind_more_compression_downwind(self):
        kwargs = dict(
            distance_m=100.0,
            bearing_to_receptor_deg=180.0,
            wind_from_direction_deg=0.0,
        )
        weak = effective_distance(wind_speed_m_s=5.0, **kwargs)
        strong = effective_distance(wind_speed_m_s=15.0, **kwargs)
        assert strong < weak


class TestEffectiveDistanceUpwind:
    def test_pure_upwind_longer_effective_distance(self):
        # Wind from S (blowing N), receptor S of source: pure upwind.
        d = effective_distance(
            distance_m=100.0,
            bearing_to_receptor_deg=180.0,  # S of source
            wind_from_direction_deg=180.0,  # wind from S, blowing N
            wind_speed_m_s=10.0,
        )
        # Upwind: stretch = 1 / (1 + 0.1*10*−1) = 1/0 → clamped to 10×
        # → d = 1000 (clamped).
        assert d > 100.0
        assert d == pytest.approx(1000.0, rel=1e-9)


class TestEffectiveDistanceValidation:
    def test_negative_distance_raises(self):
        with pytest.raises(ValueError, match="distance_m"):
            effective_distance(-1.0, 90.0, 0.0, 10.0)

    def test_zero_distance_raises(self):
        with pytest.raises(ValueError, match="distance_m"):
            effective_distance(0.0, 90.0, 0.0, 10.0)

    def test_negative_wind_raises(self):
        with pytest.raises(ValueError, match="wind_speed_m_s"):
            effective_distance(100.0, 90.0, 0.0, -1.0)

    def test_zero_coupling_raises(self):
        with pytest.raises(ValueError, match="wind_coupling"):
            effective_distance(100.0, 90.0, 0.0, 10.0, wind_coupling=0.0)

    def test_negative_coupling_raises(self):
        with pytest.raises(ValueError, match="wind_coupling"):
            effective_distance(100.0, 90.0, 0.0, 10.0, wind_coupling=-0.1)


class TestBearingFromSource:
    def test_due_north(self):
        b = bearing_from_source(0.0, 0.0, 1.0, 0.0)
        assert b == pytest.approx(0.0, abs=0.1)

    def test_due_east(self):
        b = bearing_from_source(0.0, 0.0, 0.0, 1.0)
        assert b == pytest.approx(90.0, abs=0.1)

    def test_due_south(self):
        b = bearing_from_source(1.0, 0.0, 0.0, 0.0)
        assert b == pytest.approx(180.0, abs=0.1)

    def test_due_west(self):
        b = bearing_from_source(0.0, 1.0, 0.0, 0.0)
        assert b == pytest.approx(270.0, abs=0.1)

    def test_returns_in_0_360(self):
        for rlat in (-10.0, -1.0, 0.0, 1.0, 10.0):
            for rlon in (-10.0, -1.0, 0.0, 1.0, 10.0):
                if rlat == 0.0 and rlon == 0.0:
                    continue
                b = bearing_from_source(0.0, 0.0, rlat, rlon)
                assert 0.0 <= b < 360.0


class TestModuleConstants:
    def test_default_coupling_positive(self):
        assert DEFAULT_WIND_COUPLING > 0
