"""Obszar poszukiwań i tani prefiltr kandydatów."""

from __future__ import annotations

import math

from app.domain.travel_estimate import estimate_minutes
from app.domain.types import BBox, ParticipantPoint, Point, Venue

KM_PER_DEG_LAT = 111.32
MIN_MARGIN_KM = 1.0
MARGIN_RATIO = 0.15


def search_bbox(points: list[Point]) -> BBox:
    """Prostokąt uczestników poszerzony o max(1 km, 15% rozpiętości) z każdej strony.

    Rozpiętość = dłuższy z boków prostokąta (N–S lub W–E) w km.
    """
    south, north = min(p.lat for p in points), max(p.lat for p in points)
    west, east = min(p.lon for p in points), max(p.lon for p in points)
    km_per_deg_lon = KM_PER_DEG_LAT * math.cos(math.radians((south + north) / 2))
    span_km = max((north - south) * KM_PER_DEG_LAT, (east - west) * km_per_deg_lon)
    margin_km = max(MIN_MARGIN_KM, MARGIN_RATIO * span_km)
    dlat = margin_km / KM_PER_DEG_LAT
    dlon = margin_km / km_per_deg_lon
    return BBox(south=south - dlat, west=west - dlon, north=north + dlat, east=east + dlon)


def prefilter(venues: list[Venue], people: list[ParticipantPoint], keep: int = 25) -> list[Venue]:
    """Zostawia `keep` lokali o najniższym szacowanym czasie maksymalnym (sortowanie stabilne)."""

    def worst(venue: Venue) -> float:
        return max(estimate_minutes(p.point, venue.point, p.mode) for p in people)

    return sorted(venues, key=worst)[:keep]
