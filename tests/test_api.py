"""End-to-end tests for the FastAPI backend in app.py.

These tests use FastAPI's TestClient to exercise the full request
stack without a running server.
"""

from __future__ import annotations

import os
import sys

import pytest

# Add src/ to sys.path so the test can import the `der02` package the
# same way app.py does.
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_HERE), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app import app  # the FastAPI module (top-level at project root)
    return TestClient(app)


class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "version" in body


class TestFuels:
    def test_fuels_list(self, client):
        r = client.get("/api/fuels")
        assert r.status_code == 200
        fuels = r.json()
        assert len(fuels) == 9
        names = {f["name"] for f in fuels}
        assert "propane" in names
        assert "diesel" in names
        assert "methanol" in names

    def test_each_fuel_has_required_fields(self, client):
        fuels = client.get("/api/fuels").json()
        for f in fuels:
            assert f["lhv_kj_kg"] > 0
            assert f["flame_temperature_k"] > 1000
            assert 0 < f["emissivity"] <= 1


class TestSeverityBands:
    def test_bands_endpoint(self, client):
        r = client.get("/api/severity-bands")
        assert r.status_code == 200
        body = r.json()
        assert {b["severity"] for b in body["blast"]} == {"lethal", "danger", "caution"}
        assert {b["severity"] for b in body["thermal"]} == {"lethal", "danger", "caution"}


class TestStrengthClasses:
    def test_returns_10_classes(self, client):
        r = client.get("/api/strength-classes")
        assert r.status_code == 200
        classes = r.json()
        assert len(classes) == 10
        assert [c["class"] for c in classes] == list(range(1, 11))

    def test_class_7_is_default(self, client):
        c7 = next(c for c in client.get("/api/strength-classes").json() if c["class"] == 7)
        assert c7["amplitude_factor"] == 1.0


class TestZones:
    BASE_REQUEST = {
        "fuel": "propane",
        "volume_m3": 1000.0,
        "source_lat": 0.0,
        "source_lon": 0.0,
        "bbox_half_extent_deg": 0.02,
        "wind_speed_m_s": 0.0,
        "wind_from_direction_deg": 180.0,
        "resolution_m": 100.0,
    }

    def test_basic_zone_request(self, client):
        r = client.post("/api/zones", json=self.BASE_REQUEST)
        assert r.status_code == 200
        body = r.json()
        assert body["n_records"] > 0
        assert body["fuel"] == "propane"
        assert "records" in body
        assert "band_distances" in body

    def test_records_have_valid_severity(self, client):
        r = client.post("/api/zones", json=self.BASE_REQUEST)
        body = r.json()
        for rec in body["records"]:
            assert rec["severity"] in {"safe", "caution", "danger", "lethal"}
            assert rec["blast_pa"] >= 0
            assert rec["thermal_kw_m2"] >= 0

    def test_wind_extends_downwind(self, client):
        # No-wind: zones are radially symmetric.
        no_wind = client.post(
            "/api/zones", json={**self.BASE_REQUEST, "wind_speed_m_s": 0.0}
        ).json()
        # Strong wind: zones grow on the downwind side.
        windy = client.post(
            "/api/zones",
            json={**self.BASE_REQUEST, "wind_speed_m_s": 15.0, "wind_from_direction_deg": 0.0},
        ).json()
        # Caution band extends further with wind.
        assert windy["band_distances"].get("caution", 0) >= no_wind["band_distances"].get("caution", 0)

    def test_invalid_fuel_rejected(self, client):
        r = client.post(
            "/api/zones", json={**self.BASE_REQUEST, "fuel": "unicornium"}
        )
        # Pydantic validator returns 422.
        assert r.status_code == 422

    def test_negative_volume_rejected(self, client):
        r = client.post(
            "/api/zones", json={**self.BASE_REQUEST, "volume_m3": -1.0}
        )
        assert r.status_code == 422

    def test_invalid_strength_class_rejected(self, client):
        r = client.post(
            "/api/zones", json={**self.BASE_REQUEST, "strength_class": 99}
        )
        assert r.status_code == 422


class TestZonesMulti:
    def test_multi_tank(self, client):
        body = {
            "tanks": [
                {
                    "fuel": "propane", "volume_m3": 1000.0,
                    "source_lat": 0.0, "source_lon": 0.0,
                    "bbox_half_extent_deg": 0.02,
                    "wind_speed_m_s": 5.0, "wind_from_direction_deg": 180.0,
                    "resolution_m": 100.0,
                },
                {
                    "fuel": "propane", "volume_m3": 1000.0,
                    "source_lat": 0.001, "source_lon": 0.001,
                    "bbox_half_extent_deg": 0.02,
                    "wind_speed_m_s": 5.0, "wind_from_direction_deg": 180.0,
                    "resolution_m": 100.0,
                },
            ],
            "bbox_half_extent_deg": 0.02,
            "wind_speed_m_s": 5.0,
            "wind_from_direction_deg": 180.0,
            "resolution_m": 100.0,
        }
        r = client.post("/api/zones-multi", json=body)
        assert r.status_code == 200
        result = r.json()
        assert result["n_records"] > 0

    def test_empty_tanks_rejected(self, client):
        r = client.post(
            "/api/zones-multi",
            json={"tanks": [], "bbox_half_extent_deg": 0.02, "wind_speed_m_s": 0.0,
                  "wind_from_direction_deg": 180.0, "resolution_m": 100.0},
        )
        # Pydantic's min_length=1 catches the empty list as a validation
        # error (422) before our HTTPException fires.
        assert r.status_code == 422


class TestExport:
    BASE_REQUEST = {
        "fuel": "propane",
        "volume_m3": 1000.0,
        "source_lat": 0.0,
        "source_lon": 0.0,
        "bbox_half_extent_deg": 0.02,
        "wind_speed_m_s": 5.0,
        "wind_from_direction_deg": 180.0,
        "resolution_m": 100.0,
    }

    def test_html_export(self, client):
        r = client.post("/api/zones-html", json=self.BASE_REQUEST)
        assert r.status_code == 200
        body = r.json()
        assert "html" in body
        assert body["html"].startswith("<")
        assert len(body["html"]) > 1000

    def test_pdf_export(self, client):
        r = client.post("/api/zones-pdf", json=self.BASE_REQUEST)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content.startswith(b"%PDF-")
        assert b"%%EOF" in r.content
