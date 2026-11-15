"""Globalny limiter zapytań (np. Nominatim: maks. 1 zapytanie/s na całą aplikację)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable


class RateLimiter:
    def __init__(
        self,
        min_interval_s: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.min_interval_s = min_interval_s
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.Lock()
        self._last: float | None = None

    def wait(self) -> None:
        with self._lock:
            now = self._clock()
            if self._last is not None:
                delay = self._last + self.min_interval_s - now
                if delay > 0:
                    self._sleep(delay)
                    now = self._clock()
            self._last = now
