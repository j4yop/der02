"""Tests for the folium map renderer."""

from __future__ import annotations

import folium
import pytest

from der02.map import MapRequest, render_map
from der02.zones import WindConfig, ZoneRecord


def _rec(lat: float, lon: float, severity: str, dist: float = 100.0) -> ZoneRecord:
    return ZoneRecord(
        lat=lat,
        lon=lon,
        severity=severity,
        blast_pa=50_000.0,
        thermal_kw_m2=8.0,
        distance_m=dist,
    )


@pytest.fixture
def synthetic_records() -> list[ZoneRecord]:
    """Build a small grid of synthetic zone records forming concentric
    squares around (0, 0)."""
    records = []
    for lat, lon in [
        (0.001, 0.001), (0.001, -0.001), (-0.001, -0.001), (-0.001, 0.001)
    ]:
        records.append(_rec(lat, lon, "lethal"))
    for lat, lon in [
        (0.003, 0.003), (0.003, -0.003), (-0.003, -0.003), (-0.003, 0.003)
    ]:
        records.append(_rec(lat, lon, "danger"))
    for lat, lon in [
        (0.005, 0.005), (0.005, -0.005), (-0.005, -0.005), (-0.005, 0.005)
    ]:
        records.append(_rec(lat, lon, "caution"))
    return records


@pytest.fixture
def map_request() -> MapRequest:
    return MapRequest(
        source_lat=0.0,
        source_lon=0.0,
        source_label="Propane 1000 m3",
        wind=WindConfig(speed_m_s=5.0, from_direction_deg=180.0),
    )


class TestRenderMapSmoke:
    def test_returns_folium_map(self, synthetic_records, map_request):
        m = render_map(synthetic_records, map_request)
        assert isinstance(m, folium.Map)

    def test_empty_records_raises(self, map_request):
        with pytest.raises(ValueError, match="non-empty"):
            render_map([], map_request)

    def test_save_to_html(self, synthetic_records, map_request, tmp_path):
        m = render_map(synthetic_records, map_request)
        path = tmp_path / "test_map.html"
        m.save(str(path))
        assert path.exists()
        assert path.stat().st_size > 1000


class TestRenderMapContents:
    def test_tank_marker_present(self, synthetic_records, map_request):
        m = render_map(synthetic_records, map_request)
        rendered_html = m.get_root().render()
        assert "Propane" in rendered_html or "1000" in rendered_html

    def test_zone_polygons_present(self, synthetic_records, map_request):
        m = render_map(synthetic_records, map_request)
        rendered_html = m.get_root().render()
        for severity in ("Lethal", "Danger", "Caution"):
            assert severity in rendered_html

    def test_wind_arrow_present(self, synthetic_records, map_request):
        m = render_map(synthetic_records, map_request)
        rendered_html = m.get_root().render()
        assert "Wind" in rendered_html
        assert "180" in rendered_html

    def test_disclaimer_present(self, synthetic_records, map_request):
        m = render_map(synthetic_records, map_request)
        rendered_html = m.get_root().render()
        assert "Not for life-safety" in rendered_html


class TestConvexHull:
    def test_handles_single_band(self, map_request):
        records = [
            _rec(0.005, 0.005, "caution"),
            _rec(-0.005, -0.005, "caution"),
            _rec(0.005, -0.005, "caution"),
        ]
        m = render_map(records, map_request)
        rendered_html = m.get_root().render()
        assert "Caution" in rendered_html

    def test_renders_with_only_lethal(self, map_request):
        records = [
            _rec(0.001, 0.001, "lethal"),
            _rec(0.001, -0.001, "lethal"),
            _rec(-0.001, -0.001, "lethal"),
        ]
        m = render_map(records, map_request)
        assert isinstance(m, folium.Map)
