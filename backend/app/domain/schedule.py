"""Godziny wyjścia i formatowanie dat w polskiej strefie czasowej."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo("Europe/Warsaw")

_WEEKDAYS = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
_MONTHS = [
    "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
]  # fmt: skip


def departure_time(scheduled_at: datetime, travel_minutes: int, buffer_min: int = 5) -> datetime:
    """Termin − dojazd − zapas, zaokrąglone w dół do pełnych 5 minut."""
    t = scheduled_at - timedelta(minutes=travel_minutes + buffer_min)
    t = t.replace(second=0, microsecond=0)
    return t - timedelta(minutes=t.minute % 5)


def to_warsaw(dt: datetime) -> datetime:
    return dt.astimezone(WARSAW)


def format_hhmm(dt: datetime) -> str:
    return to_warsaw(dt).strftime("%H:%M")


def format_pl_datetime(dt: datetime) -> str:
    local = to_warsaw(dt)
    return (
        f"{_WEEKDAYS[local.weekday()]}, {local.day} {_MONTHS[local.month - 1]}, {format_hhmm(dt)}"
    )
