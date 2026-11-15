"""Prosty cache w pamięci z czasem życia wpisów (wątkowo bezpieczny)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any


class TTLCache:
    def __init__(self, ttl_s: float, clock: Callable[[], float] = time.monotonic):
        self.ttl_s = ttl_s
        self._clock = clock
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires, value = item
            if self._clock() >= expires:
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            now = self._clock()
            self._data = {k: v for k, v in self._data.items() if v[0] > now}
            self._data[key] = (now + self.ttl_s, value)
