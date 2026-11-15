"""Wspólny interfejs modeli językowych: jedno wymuszone wywołanie narzędzia."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)  # JSON Schema


class LLMUnavailableError(Exception):
    """Brak klucza, limit (429), błąd sieci lub usługi."""


class LLMBadOutputError(Exception):
    """Model nie wywołał wymaganego narzędzia."""


class LLMClient(Protocol):
    def call_tool(self, system: str, user: str, tool: ToolSpec) -> dict: ...
