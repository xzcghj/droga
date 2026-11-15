"""Kontener zależności — jedno miejsce, w którym składamy adaptery.

W testach podmieniany na atrapy (tests/conftest.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from app.adapters.geocoding import NominatimGeocoder
from app.adapters.routing import HaversineRouter, OsrmRouter
from app.adapters.throttle import RateLimiter
from app.adapters.venues import FallbackVenues, OverpassVenues, SnapshotVenues
from app.config import Settings

SNAPSHOT_PATH = Path(__file__).resolve().parents[1] / "data" / "venues_trojmiasto.json"


@dataclass
class Container:
    geocoder: Any = None
    routers: dict[str, Any] = field(default_factory=dict)
    fallback_router: Any = None
    venues: Any = None
    llm: Any = None
    ai_provider: str | None = None
    suggestion_cache: Any = None


def build_container(settings: Settings) -> Container:
    client = httpx.Client(timeout=settings.http_timeout_s)
    nominatim_limiter = RateLimiter(1.0)
    osrm = OsrmRouter(client, settings.osrm_base_url)
    return Container(
        geocoder=NominatimGeocoder(
            client, settings.nominatim_url, settings.osm_user_agent, nominatim_limiter
        ),
        routers={"walk": osrm, "bike": osrm, "car": osrm},
        fallback_router=HaversineRouter(),
        venues=FallbackVenues(
            OverpassVenues(client, settings.overpass_urls), SnapshotVenues(SNAPSHOT_PATH)
        ),
    )
