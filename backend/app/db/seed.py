"""Przykładowe spotkanie, żeby demo działało od pierwszego uruchomienia (bez sieci)."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

from sqlmodel import Session, select

from app.db.models import Meetup, Participant
from app.domain.schedule import WARSAW
from app.domain.types import TravelMode, VenueCategory

DEMO_PEOPLE = [
    ("Ola", "Gdynia Główna", 54.5203, 18.5302, TravelMode.transit),
    ("Kuba", "Gdańsk Oliwa", 54.4109, 18.5655, TravelMode.bike),
    ("Ja", "Sopot, Monte Cassino", 54.4446, 18.5664, TravelMode.walk),
    ("Marta", "Gdańsk Wrzeszcz", 54.3797, 18.6070, TravelMode.car),
]


def next_saturday_15(now: datetime | None = None) -> datetime:
    """Najbliższa sobota 15:00 czasu polskiego (w przyszłości), zwracana w UTC."""
    local_now = (now or datetime.now(UTC)).astimezone(WARSAW)
    days = (5 - local_now.weekday()) % 7
    candidate = datetime.combine(local_now.date() + timedelta(days=days), time(15), WARSAW)
    if candidate <= local_now:
        candidate = datetime.combine(candidate.date() + timedelta(days=7), time(15), WARSAW)
    return candidate.astimezone(UTC)


def seed_demo(session: Session) -> None:
    if session.exec(select(Meetup.id).limit(1)).first() is not None:
        return
    meetup = Meetup(
        title="Kawa w sobotę",
        scheduled_at=next_saturday_15(),
        venue_category=VenueCategory.cafe,
    )
    meetup.participants = [
        Participant(name=n, start_label=label, lat=lat, lon=lon, mode=mode)
        for n, label, lat, lon, mode in DEMO_PEOPLE
    ]
    session.add(meetup)
    session.commit()
