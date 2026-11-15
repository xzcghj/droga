"""Ranking sprawiedliwych miejsc spotkania (spec §7)."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass

from app.adapters.http import AdapterError
from app.api.errors import AppError
from app.container import Container
from app.db.models import Meetup
from app.domain.candidates import prefilter, search_bbox
from app.domain.fairness import rank
from app.domain.travel_estimate import transit_minutes
from app.domain.types import ParticipantPoint, Point, RankedCandidate, TravelMode, TravelTime

PREFILTER_KEEP = 25
OVERPASS_LIMIT = 300
ROUTED_PROFILES = (TravelMode.walk, TravelMode.bike, TravelMode.car)


@dataclass(frozen=True)
class SuggestionsResult:
    candidates: list[RankedCandidate]
    venue_source: str


def people_of(meetup: Meetup) -> list[ParticipantPoint]:
    return [
        ParticipantPoint(p.id, Point(p.lat, p.lon), TravelMode(p.mode)) for p in meetup.participants
    ]


def travel_times(
    container: Container, people: list[ParticipantPoint], destinations: list[Point]
) -> list[list[TravelTime]]:
    """Czasy dojazdu: wiersz = cel, kolumna = osoba (w kolejności `people`).

    OSRM tylko dla profili faktycznie użytych; awaria lub brak trasy → szacunek.
    Komunikacja miejska zawsze szacowana.
    """
    grid: list[list[TravelTime | None]] = [[None] * len(people) for _ in destinations]

    def put(d: int, col: int, minutes: float, source: str) -> None:
        p = people[col]
        grid[d][col] = TravelTime(p.id, math.ceil(minutes - 1e-9), p.mode, source)

    router_down = False
    for profile in ROUTED_PROFILES:
        cols = [i for i, p in enumerate(people) if p.mode == profile]
        if not cols or not destinations:
            continue
        sources = [people[i].point for i in cols]
        matrix, source = None, "estimate"
        if not router_down:
            try:
                matrix = container.routers[profile.value].matrix(
                    profile.value, sources, destinations
                )
                source = "osrm"
            except AdapterError:
                router_down = True  # nie czekamy na kolejne timeouty w tym samym żądaniu
        fallback = container.fallback_router.matrix(profile.value, sources, destinations)
        for s, col in enumerate(cols):
            for d in range(len(destinations)):
                value = matrix[s][d] if matrix is not None else None
                if value is None:
                    put(d, col, fallback[s][d], "estimate")
                else:
                    put(d, col, value, source)

    for col, p in enumerate(people):
        if p.mode == TravelMode.transit:
            for d, dest in enumerate(destinations):
                put(d, col, transit_minutes(p.point, dest), "estimate")

    return [[t for t in row if t is not None] for row in grid]


def cache_key(meetup: Meetup, people: list[ParticipantPoint], limit: int) -> str:
    items = sorted((p.id, p.point.lat, p.point.lon, p.mode.value) for p in people)
    raw = json.dumps([items, str(meetup.venue_category), limit])
    return hashlib.sha256(raw.encode()).hexdigest()


def _degraded(candidates: list[RankedCandidate], venue_source: str) -> bool:
    if venue_source != "overpass":
        return True
    return any(
        t.data_source == "estimate" and t.mode != TravelMode.transit
        for c in candidates
        for t in c.travel
    )


class SuggestionService:
    def __init__(self, container: Container):
        self.container = container

    def suggest(self, meetup: Meetup, limit: int) -> SuggestionsResult:
        people = people_of(meetup)
        if len(people) < 2:
            raise AppError(
                422,
                "not_enough_participants",
                "Dodaj co najmniej 2 osoby, żeby szukać miejsca.",
            )
        key = cache_key(meetup, people, limit)
        cache = self.container.suggestion_cache
        cached = cache.get(key) if cache is not None else None
        if cached is not None:
            return cached

        bbox = search_bbox([p.point for p in people])
        venues, venue_source = self.container.venues.find_with_source(
            meetup.venue_category, bbox, OVERPASS_LIMIT
        )
        shortlist = prefilter(venues, people, keep=PREFILTER_KEEP)
        times = travel_times(self.container, people, [v.point for v in shortlist])
        candidates = rank(list(zip(shortlist, times, strict=True)), limit)
        result = SuggestionsResult(candidates=candidates, venue_source=venue_source)
        # Wyniki zdegradowane (awaria usługi) nie trafiają do cache — kolejna próba może się udać.
        if cache is not None and not _degraded(candidates, venue_source):
            cache.set(key, result)
        return result
