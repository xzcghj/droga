"""Wspólne wywołania HTTP: timeout z klienta, jedno ponowienie przy 429/5xx."""

from __future__ import annotations

from typing import Any

import httpx


class AdapterError(Exception):
    """Awaria usługi zewnętrznej (timeout, błąd HTTP, niepoprawny JSON)."""


def _retryable(status: int) -> bool:
    return status == 429 or status >= 500


def request_json(
    client: httpx.Client, method: str, url: str, *, retries: int = 1, **kwargs: Any
) -> Any:
    attempt = 0
    while True:
        try:
            response = client.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            # Bez ponowień przy timeoucie/błędzie sieci — spec §8 ponawia tylko 429/5xx,
            # a każda próba to do 8 s czekania użytkownika.
            raise AdapterError(f"{method} {url}: {exc}") from exc
        if response.is_success:
            try:
                return response.json()
            except ValueError as exc:
                raise AdapterError(f"{method} {url}: niepoprawny JSON") from exc
        if _retryable(response.status_code) and attempt < retries:
            attempt += 1
            continue
        raise AdapterError(f"{method} {url}: HTTP {response.status_code}")
