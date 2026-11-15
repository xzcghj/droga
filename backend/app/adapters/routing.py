"""Macierze czasów przejazdu: OSRM (FOSSGIS) i szacunek w linii prostej (fallback)."""

from __future__ import annotations

from typing import Literal, Protocol

import httpx

from app.adapters.http import AdapterError, request_json
from app.domain.travel_estimate import estimate_minutes
from app.domain.types import Point, TravelMode

Profile = Literal["walk", "bike", "car"]

OSRM_PROFILES: dict[str, str] = {"walk": "routed-foot", "bike": "routed-bike", "car": "routed-car"}


class Router(Protocol):
    def matrix(
        self, profile: Profile, sources: list[Point], destinations: list[Point]
    ) -> list[list[float | None]]:
        """Minuty [źródło][cel]; None, gdy brak trasy."""
        ...


class OsrmRouter:
    def __init__(self, client: httpx.Client, base_url: str):
        self.client = client
        self.base_url = base_url.rstrip("/")

    def matrix(
        self, profile: Profile, sources: list[Point], destinations: list[Point]
    ) -> list[list[float | None]]:
        points = [*sources, *destinations]
        coords = ";".join(f"{p.lon},{p.lat}" for p in points)
        n = len(sources)
        url = f"{self.base_url}/{OSRM_PROFILES[profile]}/table/v1/driving/{coords}"
        data = request_json(
            self.client,
            "GET",
            url,
            params={
                "sources": ";".join(str(i) for i in range(n)),
                "destinations": ";".join(str(i) for i in range(n, len(points))),
                "annotations": "duration",
            },
        )
        if not isinstance(data, dict) or data.get("code") != "Ok":
            raise AdapterError(f"OSRM: kod {data.get('code') if isinstance(data, dict) else '?'}")
        durations = data.get("durations")
        if (
            not isinstance(durations, list)
            or len(durations) != n
            or any(not isinstance(row, list) or len(row) != len(destinations) for row in durations)
        ):
            raise AdapterError("OSRM: nieoczekiwany kształt macierzy")
        return [[None if s is None else float(s) / 60 for s in row] for row in durations]


class HaversineRouter:
    def matrix(
        self, profile: Profile, sources: list[Point], destinations: list[Point]
    ) -> list[list[float | None]]:
        mode = TravelMode(profile)
        return [[estimate_minutes(s, d, mode) for d in destinations] for s in sources]
