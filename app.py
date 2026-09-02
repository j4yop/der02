"""FastAPI backend for der02 — Vercel-deployable.

Exposes the der02 physics as a JSON API. The Streamlit app
(`streamlit_app.py`) remains the local-development UI; this FastAPI
app serves the same package over HTTP for Vercel deployment.

The static HTML frontend lives in `public/index.html` and is
served by Vercel's CDN automatically (the FastAPI app does not
serve it — Vercel handles the `public/` directory at the edge).

Vercel deployment note
----------------------
Vercel's Python runtime does NOT install the local `der02` package
(`src/der02/`) automatically — it only installs the third-party
dependencies from `pyproject.toml` / `requirements.txt`. To make the
`der02` package importable in the Vercel function, we add `src/` to
`sys.path` at the top of this file. This avoids the need for a
local-package install step.

API:
    GET  /api/fuels            — list available fuels with constants.
    GET  /api/strength-classes — TNO Multi-Energy strength classes 1-10.
    GET  /api/severity-bands   — CCPS blast + thermal severity bands.
    POST /api/zones            — compute zone records for given inputs.
    POST /api/zones-html       — return rendered Folium HTML for the zones.
    POST /api/zones-pdf        — return a text-only PDF summary.
    POST /api/zones-multi      — multi-tank worst-of-per-point union.
    GET  /api/health          — health check.

Run locally:
    uvicorn app:app --reload --port 8000
"""

from __future__ import annotations

# Make the `der02` package importable when running as a Vercel function.
# In Vercel, only the entrypoint file (`app.py`) is on sys.path; the
# `src/` directory (which contains the `der02` package) is not. We add
# it explicitly so the import statements below work both locally and
# on Vercel.
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse, Response  # noqa: E402
from pydantic import BaseModel, Field, field_validator  # noqa: E402

from der02 import __version__  # noqa: E402
from der02.blast import CLASS_AMPLITUDE_FACTORS
from der02.export import html_to_pdf_bytes
from der02.fuels import FUELS, get_fuel
from der02.map import MapRequest, render_map
from der02.thresholds import BLAST_BANDS, THERMAL_BANDS
from der02.zones import (
    DEFAULT_COMBUSTION_EFFICIENCY,
    DEFAULT_TRANSMISSIVITY,
    BBox,
    Tank,
    WindConfig,
    compute_zones,
    compute_zones_multi,
)

app = FastAPI(
    title="der02 — Threat Zone Estimator",
    version=__version__,
    description=(
        "TNO Multi-Energy blast + solid-flame thermal radiation, "
        "with wind distortion. See /docs for the interactive API."
    ),
)

# CORS open by default — this API is meant to be called from the
# bundled static frontend on the same origin. Lock down CORS in
# production if you put the frontend on a different domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schema: fuel info ────────────────────────────────────────────────
class FuelInfo(BaseModel):
    name: str
    formula: str
    cas: str
    lhv_kj_kg: float
    flame_temperature_k: float
    liquid_density_kg_m3: float | None
    vapor_density_kg_m3: float
    vapor_relative_to_air: float
    emissivity: float
    nist_webbook_url: str


@app.get("/api/fuels", response_model=list[FuelInfo])
def list_fuels() -> list[FuelInfo]:
    return [
        FuelInfo(
            name=f.name,
            formula=f.formula,
            cas=f.cas,
            lhv_kj_kg=f.lhv_kj_kg,
            flame_temperature_k=f.flame_temperature_k,
            liquid_density_kg_m3=f.liquid_density_kg_m3,
            vapor_density_kg_m3=f.vapor_density_kg_m3,
            vapor_relative_to_air=f.vapor_relative_to_air,
            emissivity=f.emissivity,
            nist_webbook_url=f.nist_webbook_url,
        )
        for f in FUELS.values()
    ]


# ── Schema: severity bands ───────────────────────────────────────────
class SeverityBand(BaseModel):
    threshold: float
    severity: str


class SeverityBands(BaseModel):
    blast: list[SeverityBand]
    thermal: list[SeverityBand]


@app.get("/api/severity-bands", response_model=SeverityBands)
def severity_bands() -> SeverityBands:
    return SeverityBands(
        blast=[SeverityBand(threshold=t, severity=s) for t, s in BLAST_BANDS],
        thermal=[SeverityBand(threshold=t, severity=s) for t, s in THERMAL_BANDS],
    )


# ── Schema: strength classes ─────────────────────────────────────────
class StrengthClassInfo(BaseModel):
    class_: int = Field(alias="class")
    amplitude_factor: float
    description: str

    model_config = {"populate_by_name": True}


_STRENGTH_CLASS_DESCRIPTIONS = {
    1: "Unconfined deflagration (very weak)",
    2: "Unconfined deflagration",
    3: "Partial confinement, low congestion",
    4: "Partial confinement",
    5: "Moderate confinement",
    6: "Heavy congestion",
    7: "Heavily congested on-shore module (default, TNO/CCPS/GAME)",
    8: "Very heavy congestion",
    9: "Near-detonative",
    10: "Detonative",
}


@app.get("/api/strength-classes", response_model=list[StrengthClassInfo])
def strength_classes() -> list[StrengthClassInfo]:
    return [
        StrengthClassInfo(
            **{"class": c},
            amplitude_factor=CLASS_AMPLITUDE_FACTORS[c],
            description=_STRENGTH_CLASS_DESCRIPTIONS[c],
        )
        for c in range(1, 11)
    ]


# ── Schema: zone computation ─────────────────────────────────────────
class ZoneRequest(BaseModel):
    fuel: str
    volume_m3: float = Field(gt=0)
    source_lat: float = Field(ge=-90, le=90)
    source_lon: float = Field(ge=-180, le=180)
    bbox_half_extent_deg: float = Field(default=0.02, gt=0, le=1.0)
    wind_speed_m_s: float = Field(default=5.0, ge=0, le=50)
    wind_from_direction_deg: float = Field(default=180, ge=0, lt=360)
    resolution_m: float = Field(default=100, ge=10, le=2000)
    combustion_efficiency: float = Field(default=DEFAULT_COMBUSTION_EFFICIENCY, gt=0, le=1)
    burn_duration_s: float = Field(default=600, gt=0)
    tank_diameter_m: float | None = Field(default=None, gt=0)
    tank_height_m: float | None = Field(default=None, gt=0)
    transmissivity: float = Field(default=DEFAULT_TRANSMISSIVITY, gt=0, le=1)
    strength_class: int = Field(default=7, ge=1, le=10)

    @field_validator("fuel")
    @classmethod
    def _check_fuel(cls, v: str) -> str:
        try:
            get_fuel(v)
        except KeyError as e:
            raise ValueError(str(e)) from e
        return v


class ZoneRecordOut(BaseModel):
    lat: float
    lon: float
    severity: str
    blast_pa: float
    thermal_kw_m2: float
    distance_m: float


class ZoneResponse(BaseModel):
    records: list[ZoneRecordOut]
    source_label: str
    bbox: dict
    wind: dict
    fuel: str
    volume_m3: float
    strength_class: int
    n_records: int
    band_distances: dict


def _records_to_out(records):
    return [
        ZoneRecordOut(
            lat=r.lat, lon=r.lon, severity=r.severity,
            blast_pa=r.blast_pa, thermal_kw_m2=r.thermal_kw_m2,
            distance_m=r.distance_m,
        )
        for r in records
    ]


def _band_distances(records):
    by_sev: dict[str, float] = {}
    for r in records:
        if r.severity not in by_sev or r.distance_m > by_sev[r.severity]:
            by_sev[r.severity] = r.distance_m
    return by_sev


def _compute_zones_for_request(req: ZoneRequest):
    fuel = get_fuel(req.fuel)
    bbox = BBox(
        min_lat=req.source_lat - req.bbox_half_extent_deg,
        min_lon=req.source_lon - req.bbox_half_extent_deg,
        max_lat=req.source_lat + req.bbox_half_extent_deg,
        max_lon=req.source_lon + req.bbox_half_extent_deg,
    )
    wind = WindConfig(
        speed_m_s=req.wind_speed_m_s,
        from_direction_deg=req.wind_from_direction_deg,
    )
    records = compute_zones(
        fuel=fuel,
        volume_m3=req.volume_m3,
        source_lat=req.source_lat,
        source_lon=req.source_lon,
        bbox=bbox,
        wind=wind,
        resolution_m=req.resolution_m,
        combustion_efficiency=req.combustion_efficiency,
        burn_duration_s=req.burn_duration_s,
        tank_diameter_m=req.tank_diameter_m,
        tank_height_m=req.tank_height_m,
        transmissivity=req.transmissivity,
        strength_class=req.strength_class,
    )
    return fuel, bbox, wind, records


@app.post("/api/zones", response_model=ZoneResponse)
def compute(req: ZoneRequest) -> ZoneResponse:
    fuel, bbox, wind, records = _compute_zones_for_request(req)
    return ZoneResponse(
        records=_records_to_out(records),
        source_label=f"{req.fuel.title()} {req.volume_m3:.0f} m³",
        bbox={
            "min_lat": bbox.min_lat, "min_lon": bbox.min_lon,
            "max_lat": bbox.max_lat, "max_lon": bbox.max_lon,
        },
        wind={"speed_m_s": wind.speed_m_s, "from_direction_deg": wind.from_direction_deg},
        fuel=req.fuel,
        volume_m3=req.volume_m3,
        strength_class=req.strength_class,
        n_records=len(records),
        band_distances=_band_distances(records),
    )


# ── Schema: multi-tank ──────────────────────────────────────────────
class MultiTankRequest(BaseModel):
    tanks: list[ZoneRequest] = Field(min_length=1, max_length=10)
    bbox_half_extent_deg: float = Field(default=0.02, gt=0, le=1.0)
    wind_speed_m_s: float = Field(default=5.0, ge=0, le=50)
    wind_from_direction_deg: float = Field(default=180, ge=0, lt=360)
    resolution_m: float = Field(default=100, ge=10, le=2000)
    combustion_efficiency: float = Field(default=DEFAULT_COMBUSTION_EFFICIENCY, gt=0, le=1)
    burn_duration_s: float = Field(default=600, gt=0)
    transmissivity: float = Field(default=DEFAULT_TRANSMISSIVITY, gt=0, le=1)
    strength_class: int = Field(default=7, ge=1, le=10)


@app.post("/api/zones-multi", response_model=ZoneResponse)
def compute_multi(req: MultiTankRequest) -> ZoneResponse:
    """Multi-tank worst-of-per-point union."""
    if not req.tanks:
        raise HTTPException(status_code=400, detail="At least one tank required.")
    tanks = [
        Tank(
            fuel=get_fuel(t.fuel),
            volume_m3=t.volume_m3,
            lat=t.source_lat,
            lon=t.source_lon,
            tank_diameter_m=t.tank_diameter_m,
            tank_height_m=t.tank_height_m,
            label=f"{t.fuel.title()} {t.volume_m3:.0f} m³",
        )
        for t in req.tanks
    ]
    # All tanks share a single bbox centered on the tank centroid.
    cx = sum(t.lat for t in tanks) / len(tanks)
    cy = sum(t.lon for t in tanks) / len(tanks)
    bbox = BBox(
        min_lat=cx - req.bbox_half_extent_deg,
        min_lon=cy - req.bbox_half_extent_deg,
        max_lat=cx + req.bbox_half_extent_deg,
        max_lon=cy + req.bbox_half_extent_deg,
    )
    wind = WindConfig(
        speed_m_s=req.wind_speed_m_s,
        from_direction_deg=req.wind_from_direction_deg,
    )
    records = compute_zones_multi(
        tanks=tanks, bbox=bbox, wind=wind,
        resolution_m=req.resolution_m,
        combustion_efficiency=req.combustion_efficiency,
        burn_duration_s=req.burn_duration_s,
        transmissivity=req.transmissivity,
        strength_class=req.strength_class,
    )
    return ZoneResponse(
        records=_records_to_out(records),
        source_label=f"{len(tanks)} tanks",
        bbox={
            "min_lat": bbox.min_lat, "min_lon": bbox.min_lon,
            "max_lat": bbox.max_lat, "max_lon": bbox.max_lon,
        },
        wind={"speed_m_s": req.wind_speed_m_s, "from_direction_deg": req.wind_from_direction_deg},
        fuel=", ".join(t.fuel for t in req.tanks),
        volume_m3=sum(t.volume_m3 for t in req.tanks),
        strength_class=req.strength_class,
        n_records=len(records),
        band_distances=_band_distances(records),
    )


# ── HTML / PDF export ───────────────────────────────────────────────
def _render_html(records, req) -> str:
    import io
    fmap = render_map(
        records,
        MapRequest(
            source_lat=req.source_lat, source_lon=req.source_lon,
            source_label=f"{req.fuel.title()} {req.volume_m3:.0f} m³",
            wind=WindConfig(
                speed_m_s=req.wind_speed_m_s,
                from_direction_deg=req.wind_from_direction_deg,
            ),
        ),
    )
    buf = io.BytesIO()
    fmap.save(buf, close_file=False)
    return buf.getvalue().decode("utf-8")


@app.post("/api/zones-html")
def zones_html(req: ZoneRequest) -> JSONResponse:
    _, _, _, records = _compute_zones_for_request(req)
    html = _render_html(records, req)
    return JSONResponse({"html": html, "filename": "der02_map.html"})


@app.post("/api/zones-pdf", response_class=Response)
def zones_pdf(req: ZoneRequest) -> Response:
    """Return a text-only PDF embedding the rendered HTML.

    For a rendered-map PDF, use /api/zones-html to download the HTML
    and use the browser's print-to-PDF.
    """
    _, _, _, records = _compute_zones_for_request(req)
    html = _render_html(records, req)
    pdf_bytes = html_to_pdf_bytes(html)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=der02_map.pdf"},
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


__all__ = ["app"]
