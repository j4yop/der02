"""Tests for the zone orchestrator."""

from __future__ import annotations

import pytest

from der02.fuels import PROPANE
from der02.zones import (
    DEFAULT_COMBUSTION_EFFICIENCY,
    BBox,
    WindConfig,
    compute_zones,
)


@pytest.fixture
def small_bbox() -> BBox:
    """A 1 km × 1 km box centred on the equator near (0,0)."""
    # 1° of latitude ≈ 111 km; 1° of longitude at equator ≈ 111 km.
    return BBox(min_lat=-0.005, min_lon=-0.005, max_lat=0.005, max_lon=0.005)


@pytest.fixture
def no_wind() -> WindConfig:
    return WindConfig(speed_m_s=0.0, from_direction_deg=180.0)


class TestComputeZonesSmoke:
    def test_returns_list_of_records(self, small_bbox, no_wind):
        records = compute_zones(
            fuel=PROPANE,
            volume_m3=1000.0,
            source_lat=0.0,
            source_lon=0.0,
            bbox=small_bbox,
            wind=no_wind,
        )
        assert isinstance(records, list)
        assert len(records) > 0
        for r in records:
            assert r.severity in {"lethal", "danger", "caution", "safe"}
            assert r.blast_pa >= 0
            assert r.thermal_kw_m2 >= 0
            assert r.distance_m >= 0


class TestSeverityAtSource:
    def test_record_at_source_is_lethal(self, small_bbox, no_wind):
        records = compute_zones(
            fuel=PROPANE,
            volume_m3=1000.0,
            source_lat=0.0,
            source_lon=0.0,
            bbox=small_bbox,
            wind=no_wind,
            resolution_m=100.0,
        )
        # Find the closest record to the source.
        closest = min(records, key=lambda r: r.distance_m)
        # Even the closest grid point is at least 50 m away due to
        # resolution. At small distances the result depends on the curve
        # clamping; the band must be at least "danger" for a 1000 m³
        # propane tank.
        assert closest.severity in {"lethal", "danger"}


class TestSeverityAtFarField:
    def test_far_records_are_safe(self, no_wind):
        # 5 km × 5 km box → at the corners (distance > 3.5 km) the
        # result must be safe or caution for a 100 m³ tank.
        bbox = BBox(min_lat=-0.025, min_lon=-0.025, max_lat=0.025, max_lon=0.025)
        records = compute_zones(
            fuel=PROPANE,
            volume_m3=100.0,
            source_lat=0.0,
            source_lon=0.0,
            bbox=bbox,
            wind=no_wind,
            resolution_m=500.0,
        )
        far = max(records, key=lambda r: r.distance_m)
        assert far.severity in {"safe", "caution"}


class TestWindEffect:
    def test_no_wind_is_roughly_radial(self, small_bbox):
        # With no wind, the maximum-distance band boundary should be
        # roughly the same in all directions.
        records = compute_zones(
            fuel=PROPANE,
            volume_m3=1000.0,
            source_lat=0.0,
            source_lon=0.0,
            bbox=small_bbox,
            wind=WindConfig(speed_m_s=0.0, from_direction_deg=0.0),
        )
        # Take records at the same ~750 m distance and check severities
        # are not wildly different.
        sample = [r for r in records if 700.0 <= r.distance_m <= 800.0]
        if len(sample) < 4:
            pytest.skip("not enough sample points at this resolution")
        severities = {r.severity for r in sample}
        # With no wind we expect at most two severity bands at the same
        # distance (e.g. only "danger" or only "caution").
        assert len(severities) <= 2

    def test_wind_extends_downwind_zone(self, small_bbox):
        # With strong wind from N (blowing S), the downwind (S) side
        # should have a more severe zone at the same real distance than
        # the upwind (N) side.
        bbox = BBox(min_lat=-0.01, min_lon=-0.005, max_lat=0.01, max_lon=0.005)
        windy_records = compute_zones(
            fuel=PROPANE,
            volume_m3=1000.0,
            source_lat=0.0,
            source_lon=0.0,
            bbox=bbox,
            wind=WindConfig(speed_m_s=15.0, from_direction_deg=0.0),
            resolution_m=100.0,
        )

        order = {"safe": 0, "caution": 1, "danger": 2, "lethal": 3}
        # Pick a downwind point (S of source, lon ≈ 0).
        def pick(records, side: str) -> tuple[float, float, float]:
            # side == "down" means lat < 0 (since wind from N blows S)
            if side == "down":
                candidates = [r for r in records if r.lat < 0 and r.distance_m > 300]
            else:
                candidates = [r for r in records if r.lat > 0 and r.distance_m > 300]
            if not candidates:
                return (0.0, 0.0, 0.0)
            # Worst severity in that half.
            worst = max(candidates, key=lambda r: order[r.severity])
            return (worst.distance_m, order[worst.severity], worst.severity)

        # Just check that with wind, the downwind severity is at least
        # as bad as the upwind severity.
        dw_with = pick(windy_records, "down")
        up_with = pick(windy_records, "up")
        assert dw_with[1] >= up_with[1], (
            f"Downwind severity {dw_with[2]} should be ≥ upwind severity {up_with[2]}"
        )


class TestValidation:
    def test_zero_volume_raises(self, small_bbox, no_wind):
        with pytest.raises(ValueError, match="volume_m3"):
            compute_zones(
                fuel=PROPANE,
                volume_m3=0.0,
                source_lat=0.0,
                source_lon=0.0,
                bbox=small_bbox,
                wind=no_wind,
            )

    def test_negative_volume_raises(self, small_bbox, no_wind):
        with pytest.raises(ValueError, match="volume_m3"):
            compute_zones(
                fuel=PROPANE,
                volume_m3=-1.0,
                source_lat=0.0,
                source_lon=0.0,
                bbox=small_bbox,
                wind=no_wind,
            )

    def test_efficiency_zero_raises(self, small_bbox, no_wind):
        with pytest.raises(ValueError, match="combustion_efficiency"):
            compute_zones(
                fuel=PROPANE,
                volume_m3=1000.0,
                source_lat=0.0,
                source_lon=0.0,
                bbox=small_bbox,
                wind=no_wind,
                combustion_efficiency=0.0,
            )

    def test_efficiency_above_one_raises(self, small_bbox, no_wind):
        with pytest.raises(ValueError, match="combustion_efficiency"):
            compute_zones(
                fuel=PROPANE,
                volume_m3=1000.0,
                source_lat=0.0,
                source_lon=0.0,
                bbox=small_bbox,
                wind=no_wind,
                combustion_efficiency=1.5,
            )

    def test_burn_duration_zero_raises(self, small_bbox, no_wind):
        with pytest.raises(ValueError, match="burn_duration_s"):
            compute_zones(
                fuel=PROPANE,
                volume_m3=1000.0,
                source_lat=0.0,
                source_lon=0.0,
                bbox=small_bbox,
                wind=no_wind,
                burn_duration_s=0.0,
            )


class TestFuelEffect:
    def test_larger_volume_extends_zone(self, small_bbox, no_wind):
        # Doubling the volume doubles the total combustion energy, which
        # extends the hazard zone further. This is a cleaner fuel-effect
        # test than comparing substances (different substances have very
        # different densities that dominate over LHV/kg).
        bbox = BBox(min_lat=-0.02, min_lon=-0.02, max_lat=0.02, max_lon=0.02)
        small = compute_zones(
            fuel=PROPANE, volume_m3=100.0,
            source_lat=0.0, source_lon=0.0, bbox=bbox, wind=no_wind,
            resolution_m=200.0,
        )
        big = compute_zones(
            fuel=PROPANE, volume_m3=10_000.0,
            source_lat=0.0, source_lon=0.0, bbox=bbox, wind=no_wind,
            resolution_m=200.0,
        )

        order = {"safe": 0, "caution": 1, "danger": 2, "lethal": 3}
        small_max_severity = max(order[r.severity] for r in small)
        big_max_severity = max(order[r.severity] for r in big)
        assert big_max_severity >= small_max_severity


class TestGridGeneration:
    def test_grid_count_matches_bbox(self):
        from der02.zones import _grid_nodes

        bbox = BBox(min_lat=0.0, min_lon=0.0, max_lat=0.01, max_lat_dummy=0.0) if False else \
               BBox(min_lat=0.0, min_lon=0.0, max_lat=0.01, max_lon=0.01)  # noqa
        # 0.01° lat ≈ 1.1 km. At 500 m resolution: ~3 nodes per side.
        nodes = _grid_nodes(bbox, resolution_m=500.0)
        assert 4 <= len(nodes) <= 16

    def test_grid_resolution_invalid_raises(self):
        from der02.zones import _grid_nodes

        bbox = BBox(min_lat=0.0, min_lon=0.0, max_lat=0.01, max_lon=0.01)
        with pytest.raises(ValueError, match="resolution_m"):
            _grid_nodes(bbox, resolution_m=0.0)
        with pytest.raises(ValueError, match="resolution_m"):
            _grid_nodes(bbox, resolution_m=-100.0)


class TestModuleConstants:
    def test_default_efficiency_in_range(self):
        assert 0 < DEFAULT_COMBUSTION_EFFICIENCY <= 1
