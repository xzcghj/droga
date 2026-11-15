"""Szacunkowe czasy dojazdu na podstawie odległości w linii prostej."""

from __future__ import annotations

import math

from app.domain.types import Point, TravelMode

EARTH_RADIUS_KM = 6371.0088
DETOUR_FACTOR = 1.3
SPEED_KMH = {TravelMode.walk: 4.8, TravelMode.bike: 15.0, TravelMode.car: 30.0}

TRANSIT_FIXED_MIN = 10.0  # 5 min dojścia + 5 min czekania
TRANSIT_DETOUR = 1.4
TRANSIT_SPEED_KMH = 22.0


def haversine_km(a: Point, b: Point) -> float:
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = lat2 - lat1
    dlon = math.radians(b.lon - a.lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(h)))


def transit_minutes(a: Point, b: Point) -> float:
    walk = estimate_minutes(a, b, TravelMode.walk)
    ride = TRANSIT_FIXED_MIN + haversine_km(a, b) * TRANSIT_DETOUR / TRANSIT_SPEED_KMH * 60
    return min(ride, walk)


def estimate_minutes(a: Point, b: Point, mode: TravelMode) -> float:
    if mode == TravelMode.transit:
        return transit_minutes(a, b)
    return haversine_km(a, b) * DETOUR_FACTOR / SPEED_KMH[mode] * 60
