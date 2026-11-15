"""Geokodowanie: interfejs + implementacja Nominatim (zgodna z polityką użycia OSM)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from app.adapters.http import AdapterError, request_json
from app.adapters.throttle import RateLimiter
from app.domain.types import Point

TRICITY_VIEWBOX = "18.40,54.60,18.80,54.30"


@dataclass(frozen=True)
class GeocodeResult:
    label: str
    point: Point


class Geocoder(Protocol):
    def search(self, query: str, limit: int = 5) -> list[GeocodeResult]: ...


class NominatimGeocoder:
    def __init__(self, client: httpx.Client, base_url: str, user_agent: str, limiter: RateLimiter):
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.limiter = limiter

    def search(self, query: str, limit: int = 5) -> list[GeocodeResult]:
        self.limiter.wait()
        data = request_json(
            self.client,
            "GET",
            f"{self.base_url}/search",
            retries=0,  # polityka Nominatim: bez ponowień
            params={
                "q": query,
                "format": "jsonv2",
                "limit": limit,
                "countrycodes": "pl",
                "viewbox": TRICITY_VIEWBOX,
                "bounded": 0,
            },
            headers={"User-Agent": self.user_agent},
        )
        try:
            return [
                GeocodeResult(
                    label=item["display_name"], point=Point(float(item["lat"]), float(item["lon"]))
                )
                for item in data
            ]
        except (KeyError, TypeError, ValueError) as exc:
            raise AdapterError("Nominatim: nieoczekiwany format odpowiedzi") from exc
