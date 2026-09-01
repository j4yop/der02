"""Tests for the blast overpressure and thermal radiation thresholds."""

from __future__ import annotations

import pytest

from der02.thresholds import (
    BLAST_BANDS,
    THERMAL_BANDS,
    classify_blast,
    classify_thermal,
)


class TestBlastBands:
    def test_lethal_band_above_100kPa(self):
        assert classify_blast(150_000) == "lethal"
        assert classify_blast(101_000) == "lethal"

    def test_danger_band_between_30_and_100kPa(self):
        assert classify_blast(50_000) == "danger"
        assert classify_blast(31_000) == "danger"

    def test_caution_band_between_10_and_30kPa(self):
        assert classify_blast(15_000) == "caution"
        assert classify_blast(11_000) == "caution"

    def test_safe_below_10kPa(self):
        assert classify_blast(5_000) == "safe"
        assert classify_blast(0) == "safe"

    def test_bands_are_ordered_lethal_first(self):
        """Sanity: lethal threshold is highest."""
        assert BLAST_BANDS[0][1] == "lethal"
        assert BLAST_BANDS[0][0] > BLAST_BANDS[1][0] > BLAST_BANDS[2][0]


class TestThermalBands:
    def test_lethal_band_above_37_5(self):
        assert classify_thermal(50.0) == "lethal"
        assert classify_thermal(38.0) == "lethal"

    def test_danger_band_between_12_5_and_37_5(self):
        assert classify_thermal(20.0) == "danger"
        assert classify_thermal(13.0) == "danger"

    def test_caution_band_between_4_and_12_5(self):
        assert classify_thermal(6.0) == "caution"
        assert classify_thermal(5.0) == "caution"

    def test_safe_below_4(self):
        assert classify_thermal(1.0) == "safe"
        assert classify_thermal(0.0) == "safe"

    def test_bands_are_ordered_lethal_first(self):
        assert THERMAL_BANDS[0][1] == "lethal"
        assert THERMAL_BANDS[0][0] > THERMAL_BANDS[1][0] > THERMAL_BANDS[2][0]


class TestCitationCompliance:
    """Citation checks: every threshold must trace to a published CCPS band.

    CCPS *Guidelines for CPQRA* 2nd ed. (2000) standard bands:
    - Thermal: 37.5 / 12.5 / 4 kW/m^2 (Chapter 2)
    - Blast:   100 / 30 / 10 kPa (Chapter 4)
    """

    @pytest.mark.parametrize(
        "thermal_threshold", [37.5, 12.5, 4.0], ids=["lethal", "danger", "caution"]
    )
    def test_thermal_thresholds_match_ccps(self, thermal_threshold):
        severities = [s for t, s in THERMAL_BANDS if t == thermal_threshold]
        assert len(severities) == 1

    @pytest.mark.parametrize(
        "blast_threshold", [100_000, 30_000, 10_000], ids=["lethal", "danger", "caution"]
    )
    def test_blast_thresholds_match_ccps(self, blast_threshold):
        severities = [s for t, s in BLAST_BANDS if t == blast_threshold]
        assert len(severities) == 1
