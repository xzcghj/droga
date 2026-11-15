"""Typy domenowe — czyste dane, bez zależności od bazy i HTTP."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class TravelMode(StrEnum):
    walk = "walk"
    bike = "bike"
    transit = "transit"
    car = "car"


class VenueCategory(StrEnum):
    cafe = "cafe"
    bar = "bar"
    restaurant = "restaurant"
    park = "park"


@dataclass(frozen=True)
class Point:
    lat: float
    lon: float


@dataclass(frozen=True)
class Venue:
    name: str
    osm_id: str
    point: Point


@dataclass(frozen=True)
class ParticipantPoint:
    id: int
    point: Point
    mode: TravelMode


@dataclass(frozen=True)
class TravelTime:
    participant_id: int
    minutes: int
    mode: TravelMode
    data_source: Literal["osrm", "estimate"]


@dataclass(frozen=True)
class RankedCandidate:
    venue: Venue
    travel: list[TravelTime]
    max_minutes: int
    total_minutes: int
    spread_minutes: int


@dataclass(frozen=True)
class BBox:
    south: float
    west: float
    north: float
    east: float
