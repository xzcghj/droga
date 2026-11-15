"""Atrapy adapterów — testy nigdy nie korzystają z sieci."""

from __future__ import annotations

from typing import Any


class FakeLLM:
    """Zwraca zaprogramowany wynik narzędzia i zapamiętuje ostatni prompt."""

    def __init__(self, result: dict | None = None, error: Exception | None = None):
        self.result = result or {}
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def call_tool(self, system: str, user: str, tool: Any) -> dict:
        self.calls.append({"system": system, "user": user, "tool": tool})
        if self.error is not None:
            raise self.error
        return self.result


class FakeGeocoder:
    """Każde zapytanie → jeden wynik w stałym punkcie, chyba że jest w `missing`."""

    def __init__(self):
        from app.domain.types import Point

        self.point = Point(54.3797, 18.6070)
        self.missing: set[str] = set()
        self.fail = False
        self.queries: list[str] = []

    def search(self, query: str, limit: int = 5):
        from app.adapters.geocoding import GeocodeResult
        from app.adapters.http import AdapterError

        self.queries.append(query)
        if self.fail:
            raise AdapterError("geokoder niedostępny")
        if query in self.missing:
            return []
        return [GeocodeResult(label=query, point=self.point)]


class FakeRouter:
    """Czas = stała na punkt docelowy z `minutes_by_dest` albo `default`; zapisuje wywołania."""

    def __init__(self, default: float = 10.0, minutes_by_dest: dict | None = None):
        self.default = default
        self.minutes_by_dest = minutes_by_dest or {}
        self.calls: list[tuple[str, int, int]] = []

    def matrix(self, profile, sources, destinations):
        self.calls.append((profile, len(sources), len(destinations)))
        return [[self.minutes_by_dest.get(d, self.default) for d in destinations] for _ in sources]


class FailingRouter:
    def __init__(self):
        self.calls = 0

    def matrix(self, profile, sources, destinations):
        from app.adapters.http import AdapterError

        self.calls += 1
        raise AdapterError("OSRM niedostępny")


class FakeVenues:
    """Udaje FallbackVenues: stała lista i deklarowane źródło."""

    def __init__(self, venues=None, source: str = "overpass"):
        self.venues = venues or []
        self.source = source
        self.calls = 0

    def find_with_source(self, category, bbox, limit: int = 300):
        self.calls += 1
        return list(self.venues), self.source
