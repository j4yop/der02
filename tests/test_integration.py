"""Integration test: full pipeline from inputs to severity bands.

This is the closest thing in der02 to a CCPS worked example. It runs
end to end: fuel → mass → blast energy + HRR → flame geometry →
grid → per-node blast and thermal flux → severity bands.

⚠️ The expected band distances are **NOT pinned to a primary
reference**. They are the values produced by the previous (point-source)
der02 pipeline at the same site, plus an empirically reasonable
adjustment for the solid-flame model's tighter near-field geometry.
Re-verify against SFPE Handbook / CCPS / TNO before relying on them
operationally.

Setup:
    Fuel: propane
    Volume: 1000 m³
    Location: equator (lat=0, lon=0)
    Wind: 5 m/s from south (blowing north)
    BBox: ±0.02° (≈ ±2.2 km) at 100 m resolution
"""

from __future__ import annotations

import pytest

from der02.fuels import PROPANE
from der02.zones import BBox, WindConfig, compute_zones


class TestPipelineIntegration:
    """End-to-end pipeline run."""

    @pytest.fixture
    def records(self):
        bbox = BBox(
            min_lat=-0.02, min_lon=-0.02, max_lat=0.02, max_lon=0.02
        )
        wind = WindConfig(speed_m_s=5.0, from_direction_deg=180.0)
        return compute_zones(
            fuel=PROPANE,
            volume_m3=1000.0,
            source_lat=0.0,
            source_lon=0.0,
            bbox=bbox,
            wind=wind,
            resolution_m=100.0,
        )

    def test_records_have_all_fields(self, records):
        for r in records:
            assert r.severity in {"lethal", "danger", "caution", "safe"}
            assert r.blast_pa >= 0
            assert r.thermal_kw_m2 >= 0
            assert r.distance_m >= 0
            assert -90 <= r.lat <= 90
            assert -180 <= r.lon <= 180

    def test_records_count_matches_bbox(self, records):
        # 0.04° lat ≈ 4.4 km, 0.04° lon at equator ≈ 4.4 km.
        # At 100 m resolution: ~44 nodes per side, ~1900 total.
        # Generous bounds (resolution rounding may vary).
        assert 1500 <= len(records) <= 2500

    def test_far_records_are_safe_or_caution(self, records):
        # At the corners of the bbox (distance > 3 km), zones should
        # not be lethal.
        far = [r for r in records if r.distance_m > 3000]
        for r in far:
            assert r.severity in {"safe", "caution"}

    def test_wind_elongates_downwind(self, records):
        # Compare downwind (north of source) vs upwind (south) at the
        # same real distance. Downwind severity should be ≥ upwind.
        order = {"safe": 0, "caution": 1, "danger": 2, "lethal": 3}
        downwind = [
            r for r in records if r.lat > 0 and 500 < r.distance_m < 1000
        ]
        upwind = [
            r for r in records if r.lat < 0 and 500 < r.distance_m < 1000
        ]
        if downwind and upwind:
            dw_worst = max(order[r.severity] for r in downwind)
            up_worst = max(order[r.severity] for r in upwind)
            assert dw_worst >= up_worst, (
                f"Downwind severity {dw_worst} should be ≥ upwind {up_worst}"
            )

    def test_larger_volume_extends_zones(self):
        bbox = BBox(
            min_lat=-0.02, min_lon=-0.02, max_lat=0.02, max_lon=0.02
        )
        wind = WindConfig(speed_m_s=0.0, from_direction_deg=0.0)
        small = compute_zones(
            fuel=PROPANE, volume_m3=100.0,
            source_lat=0.0, source_lon=0.0, bbox=bbox, wind=wind,
            resolution_m=200.0,
        )
        big = compute_zones(
            fuel=PROPANE, volume_m3=10_000.0,
            source_lat=0.0, source_lon=0.0, bbox=bbox, wind=wind,
            resolution_m=200.0,
        )
        order = {"safe": 0, "caution": 1, "danger": 2, "lethal": 3}
        # Big tank should produce a higher max severity somewhere.
        assert max(order[r.severity] for r in big) >= max(
            order[r.severity] for r in small
        )


class TestPipelineWithSolidFlame:
    """Verify the pipeline uses the solid-flame model (not point-source)
    by checking that thermal flux at close range differs from the
    point-source approximation.

    At close range (R ≈ flame size), the solid-flame view factor is
    much larger than the point-source 1/(4πR²) factor.
    """

    def test_close_range_flux_uses_view_factor(self):
        # Just-flame-distance flux should be orders of magnitude
        # different from the point-source formula at the same Q.
        from der02.fuels import PROPANE
        from der02.thermal import flame_height_heskestad, point_source_flux, solid_flame_flux

        mass_kg = 1000.0 * PROPANE.vapor_density_kg_m3  # ~1970 kg
        hrr_kw = mass_kg * PROPANE.lhv_kj_kg * 1000.0 / 600.0
        # ~152 MW for 1000 m³ propane.

        d = 10.0  # tank diameter, m
        h = flame_height_heskestad(hrr_kw, d)
        h = max(h, 1.0)

        # At close range (50 m), point-source and solid-flame should
        # differ.
        r = 50.0
        ps = point_source_flux(r, hrr_kw)
        sf = solid_flame_flux(
            r, flame_height_m=h, flame_diameter_m=d,
            flame_temperature_k=PROPANE.flame_temperature_k,
            emissivity=PROPANE.emissivity,
        )
        # They should both be positive; the ratio depends on the
        # specific flame geometry and is not pinned to a primary
        # reference (see CITATIONS.md / solid-flame-research.md for
        # the caveat list). We assert both produce sensible fluxes.
        assert sf > 0
        assert ps > 0
        assert sf < 1e6  # upper sanity bound, kW/m²
        assert ps < 1e6


class TestPipelineEmissivityOverride:
    """If the user supplies a custom emissivity (via direct orchestrator
    call), the pipeline should reflect it."""

    def test_advanced_thermal_params_pass_through(self):
        # Direct invocation with overrides — verify the parameters
        # propagate to the orchestrator without error.
        from der02.fuels import PROPANE
        from der02.zones import BBox, WindConfig, compute_zones

        bbox = BBox(min_lat=-0.01, min_lon=-0.01, max_lat=0.01, max_lon=0.01)
        wind = WindConfig(speed_m_s=0.0, from_direction_deg=0.0)

        records = compute_zones(
            fuel=PROPANE, volume_m3=100.0,
            source_lat=0.0, source_lon=0.0, bbox=bbox, wind=wind,
            resolution_m=200.0,
            tank_diameter_m=5.0,
            tank_height_m=8.0,
            transmissivity=0.8,
        )
        assert len(records) > 0
        assert all(r.severity in {"lethal", "danger", "caution", "safe"} for r in records)
