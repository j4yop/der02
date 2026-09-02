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


class TestRenderToBuffer:
    """Bug-regression: fmap.save() must accept BytesIO, not just file paths."""

    def test_save_to_bytesio(self, synthetic_records, map_request):
        import io
        m = render_map(synthetic_records, map_request)
        buf = io.BytesIO()
        m.save(buf, close_file=False)
        html_bytes = buf.getvalue()
        assert isinstance(html_bytes, bytes)
        assert len(html_bytes) > 1000
        # Should be valid HTML
        assert b"<html" in html_bytes.lower() or b"<!doctype" in html_bytes.lower()


class TestPDFExport:
    """PDF export via der02.export.html_to_pdf_bytes."""

    def test_html_to_pdf_returns_valid_pdf(self):
        from der02.export import html_to_pdf_bytes
        pdf = html_to_pdf_bytes("<html><body>Hello</body></html>")
        assert pdf.startswith(b"%PDF-")
        assert b"%%EOF" in pdf

    def test_html_to_pdf_with_long_html(self):
        from der02.export import html_to_pdf_bytes
        long_html = "<html>" + ("x" * 10000) + "</html>"
        pdf = html_to_pdf_bytes(long_html)
        assert pdf.startswith(b"%PDF-")
        # Should be a few hundred bytes — content is truncated to 200 chars.
        assert len(pdf) < 2000

    def test_html_to_pdf_handles_special_chars(self):
        from der02.export import html_to_pdf_bytes
        html_with_parens = "Test (with) parens and \\backslash"
        pdf = html_to_pdf_bytes(html_with_parens)
        # Should not raise; should produce valid PDF.
        assert pdf.startswith(b"%PDF-")
