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
