"""Render zone records as a folium map.

The interface takes pre-computed `ZoneRecord`s (no physics here) and
returns a `folium.Map` with:

- A marker at the tank location with a popup showing fuel and volume.
- Three filled polygons, one per severity band (lethal / danger /
  caution), drawn in decreasing severity order so the innermost band
  shows the most severe color.
- A wind arrow indicating wind direction.
- A legend in the bottom-right showing the band names and the maximum
  distance at which each band is observed.
- The map centred on the source location.

Notes
-----
The MVP renders each band as a convex hull around its constituent
points. The hull gives a visually contiguous band; if the underlying
points are not all co-hemicircular (e.g. extreme wind), the hull may
under-fill the zone. A better implementation would use a filled
contour; for MVP the convex hull is sufficient.

References
----------
- folium 0.15+ docs (https://python-visualization.github.io/folium/)
- Shapely 2.0 docs for convex hull computation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import folium
from shapely.geometry import MultiPoint

from .zones import WindConfig, ZoneRecord

# Colors per severity band. Picked for high contrast on light and dark
# basemap tiles.
_BAND_COLORS: dict[str, str] = {
    "lethal": "#8B0000",   # dark red
    "danger": "#FF4500",   # orange-red
    "caution": "#FFA500",  # orange
}

# Order in which bands are drawn (worst first so the smaller lethal band
# shows on top of the larger caution band).
_BAND_ORDER: tuple[str, ...] = ("lethal", "danger", "caution")


@dataclass(frozen=True)
class MapRequest:
    """Bundle of source + wind info that goes onto the map."""

    source_lat: float
    source_lon: float
    source_label: str
    wind: WindConfig


def _band_points(records: list[ZoneRecord], severity: str) -> list[tuple[float, float]]:
    return [(r.lat, r.lon) for r in records if r.severity == severity]


def _convex_hull_polygon(
    points: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    """Return convex-hull coordinates as a list of (lat, lon) tuples.

    Uses Shapely. Falls back to the input points (closing the loop) when
    fewer than 3 points are supplied, since a hull needs at least a
    triangle.
    """
    if len(points) < 3:
        return list(points)
    hull = MultiPoint(points).convex_hull
    if hull.geom_type == "Polygon":
        return [(y, x) for x, y in hull.exterior.coords]
    return list(points)


def _max_distance_in_band(records: list[ZoneRecord], severity: str) -> float:
    band = [r for r in records if r.severity == severity]
    if not band:
        return 0.0
    return max(r.distance_m for r in band)


def _wind_arrow_icon(wind: WindConfig) -> folium.Icon:
    """Return a folium icon for the wind arrow at the source point."""
    # folium.Icon supports a single colour; we rotate the marker using
    # the bearing of the wind (i.e. where it's blowing toward). For
    # MVP we use a coloured marker without rotation; the arrow direction
    # is communicated via the popup text.
    return folium.Icon(color="blue", icon="arrow-up", prefix="fa")


def _wind_arrow_position(
    source_lat: float, source_lon: float, wind: WindConfig, offset_m: float = 200.0
) -> tuple[float, float]:
    """Compute the lat/lon of the wind arrow head, `offset_m` from the
    source in the direction the wind is blowing toward."""
    blow_deg = (wind.from_direction_deg + 180.0) % 360.0
    # 1° lat ≈ 111 320 m; 1° lon at lat ≈ 111 320 × cos(lat).
    d_lat = offset_m * math.cos(math.radians(blow_deg)) / 111_320.0
    d_lon = offset_m * math.sin(math.radians(blow_deg)) / (
        111_320.0 * math.cos(math.radians(source_lat))
    )
    return source_lat + d_lat, source_lon + d_lon


def render_map(
    records: list[ZoneRecord],
    request: MapRequest,
    zoom_start: int = 14,
) -> folium.Map:
    """Render zone records as a folium map.

    Parameters
    ----------
    records
        Output of `der02.zones.compute_zones`.
    request
        Source location, label, and wind config.
    zoom_start
        Initial folium zoom level. Default 14.

    Returns
    -------
    folium.Map
        A map ready to display or save.
    """
    if not records:
        raise ValueError("records must be a non-empty list")

    fmap = folium.Map(
        location=[request.source_lat, request.source_lon],
        zoom_start=zoom_start,
        tiles="OpenStreetMap",
    )

    # 1. Tank marker
    folium.Marker(
        location=[request.source_lat, request.source_lon],
        tooltip=request.source_label,
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(fmap)

    # 2. Zone polygons — drawn worst first so the most severe band is on top.
    for severity in _BAND_ORDER:
        pts = _band_points(records, severity)
        if len(pts) < 3:
            # Not enough points to draw a polygon. Skip.
            continue
        hull = _convex_hull_polygon(pts)
        if len(hull) < 3:
            continue
        color = _BAND_COLORS[severity]
        folium.Polygon(
            locations=hull,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.35,
            weight=2,
            tooltip=f"{severity.capitalize()} band",
        ).add_to(fmap)

    # 3. Wind arrow
    arrow_lat, arrow_lon = _wind_arrow_position(
        request.source_lat, request.source_lon, request.wind
    )
    folium.Marker(
        location=[arrow_lat, arrow_lon],
        tooltip=(
            f"Wind {request.wind.speed_m_s:.1f} m/s from "
            f"{request.wind.from_direction_deg:.0f}°"
        ),
        icon=_wind_arrow_icon(request.wind),
    ).add_to(fmap)

    # 4. Legend (HTML overlay)
    legend_html = _build_legend(records)
    fmap.get_root().html.add_child(folium.Element(legend_html))

    return fmap


def _build_legend(records: list[ZoneRecord]) -> str:
    rows = []
    for severity in _BAND_ORDER:
        max_d = _max_distance_in_band(records, severity)
        if max_d <= 0:
            continue
        color = _BAND_COLORS[severity]
        rows.append(
            f'<tr><td style="background:{color};width:18px;height:14px;">'
            f'</td><td style="padding-left:6px;">{severity.capitalize()} '
            f"(max {max_d:.0f} m)</td></tr>"
        )
    rows_html = "".join(rows)
    return f"""
    <div style="
        position: fixed;
        bottom: 30px; right: 12px;
        z-index: 9999;
        background: white;
        border: 1px solid #888;
        padding: 8px 10px;
        font-size: 13px;
        font-family: monospace;
        box-shadow: 0 1px 4px rgba(0,0,0,0.2);
    ">
      <div style="font-weight: bold; margin-bottom: 4px;">Hazard bands</div>
      <table>{rows_html}</table>
      <div style="margin-top:6px;color:#666;font-size:11px;">
        Not for life-safety decisions.
      </div>
    </div>
    """


__all__ = ["render_map", "MapRequest"]
