"""Kontener zależności — jedno miejsce, w którym składamy adaptery.

W testach podmieniany na atrapy (tests/conftest.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from app.adapters.geocoding import NominatimGeocoder
from app.adapters.throttle import RateLimiter
from app.config import Settings


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
    return Container(
        geocoder=NominatimGeocoder(
            client, settings.nominatim_url, settings.osm_user_agent, nominatim_limiter
        ),
    )
