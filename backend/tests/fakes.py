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
