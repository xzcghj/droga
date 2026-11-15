"""Źródła lokali: Overpass API (na żywo) i snapshot z repozytorium (fallback)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Protocol

import httpx

from app.adapters.http import AdapterError, request_json
from app.domain.types import BBox, Point, Venue, VenueCategory

CATEGORY_TAGS: dict[VenueCategory, list[tuple[str, str]]] = {
    VenueCategory.cafe: [("amenity", "cafe")],
    VenueCategory.bar: [("amenity", "bar"), ("amenity", "pub")],
    VenueCategory.restaurant: [("amenity", "restaurant")],
    VenueCategory.park: [("leisure", "park")],
}


class VenueSource(Protocol):
    def find(self, category: VenueCategory, bbox: BBox, limit: int = 300) -> list[Venue]: ...


def _num(x: float) -> str:
    return repr(round(x, 6))


def overpass_query(category: VenueCategory, bbox: BBox, limit: int) -> str:
    box = ",".join(_num(v) for v in (bbox.south, bbox.west, bbox.north, bbox.east))
    parts = "".join(f'nwr["{k}"="{v}"]["name"]({box});' for k, v in CATEGORY_TAGS[category])
    return f"[out:json][timeout:25];({parts});out center {limit};"


def parse_elements(data: object) -> list[Venue]:
    if not isinstance(data, dict) or not isinstance(data.get("elements"), list):
        raise AdapterError("Overpass: nieoczekiwany format odpowiedzi")
    venues: list[Venue] = []
    for el in data["elements"]:
        name = (el.get("tags") or {}).get("name")
        src = el if "lat" in el else el.get("center")
        if not name or not src or "lat" not in src:
            continue
        venues.append(
            Venue(name=name, osm_id=f"{el['type']}/{el['id']}", point=Point(src["lat"], src["lon"]))
        )
    return venues


class OverpassVenues:
    def __init__(self, client: httpx.Client, urls: list[str]):
        self.client = client
        self.urls = urls

    def find(self, category: VenueCategory, bbox: BBox, limit: int = 300) -> list[Venue]:
        query = overpass_query(category, bbox, limit)
        last: AdapterError | None = None
        for url in self.urls:
            try:
                data = request_json(self.client, "POST", url, data={"data": query})
                return parse_elements(data)
            except AdapterError as exc:
                last = exc
        raise last or AdapterError("Overpass: brak skonfigurowanych adresów")


class SnapshotVenues:
    """Lokale zapisane w repozytorium. Dane © OpenStreetMap contributors, ODbL."""

    def __init__(self, path: Path):
        self.path = path
        self._rows: list[dict] | None = None

    def _load(self) -> list[dict]:
        if self._rows is None:
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                self._rows = list(raw.get("venues", []))
            except (OSError, ValueError, AttributeError):
                self._rows = []
        return self._rows

    def find(self, category: VenueCategory, bbox: BBox, limit: int = 300) -> list[Venue]:
        out = [
            Venue(r["name"], r["osm_id"], Point(r["lat"], r["lon"]))
            for r in self._load()
            if r.get("category") == category
            and bbox.south <= r["lat"] <= bbox.north
            and bbox.west <= r["lon"] <= bbox.east
        ]
        return out[:limit]


class FallbackVenues:
    def __init__(self, primary: VenueSource, fallback: VenueSource):
        self.primary = primary
        self.fallback = fallback

    def find_with_source(
        self, category: VenueCategory, bbox: BBox, limit: int = 300
    ) -> tuple[list[Venue], Literal["overpass", "snapshot"]]:
        primary_answered = False
        try:
            venues = self.primary.find(category, bbox, limit)
            if venues:
                return venues, "overpass"
            primary_answered = True
        except AdapterError:
            pass
        fallback = self.fallback.find(category, bbox, limit)
        if not fallback and primary_answered:
            return [], "overpass"
        return fallback, "snapshot"
