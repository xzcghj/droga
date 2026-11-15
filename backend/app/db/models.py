"""Modele SQLModel. Daty przechowywane jako UTC.

Bez `from __future__ import annotations` — SQLModel potrzebuje rozwiązywalnych adnotacji relacji.
"""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.types import DateTime, TypeDecorator
from sqlmodel import Field, Relationship, SQLModel

from app.domain.types import TravelMode, VenueCategory


def utcnow() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator):
    """Zapisuje naiwny czas UTC (SQLite nie zna stref), oddaje czas świadomy strefy."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Wymagany czas ze strefą.")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        return None if value is None else value.replace(tzinfo=UTC)


class Meetup(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=100)
    scheduled_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False))
    venue_category: VenueCategory
    chosen_venue_name: str | None = None
    chosen_venue_lat: float | None = None
    chosen_venue_lon: float | None = None
    chosen_venue_osm_id: str | None = None
    invite_message: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(
        default_factory=utcnow, sa_column=Column(UTCDateTime(), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=utcnow, sa_column=Column(UTCDateTime(), nullable=False)
    )

    participants: list["Participant"] = Relationship(
        back_populates="meetup",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "order_by": "Participant.id",
            "passive_deletes": True,
        },
    )


class Participant(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    meetup_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("meetup.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    name: str = Field(max_length=50)
    start_label: str = Field(max_length=200)
    lat: float
    lon: float
    mode: TravelMode
    created_at: datetime = Field(
        default_factory=utcnow, sa_column=Column(UTCDateTime(), nullable=False)
    )

    meetup: Optional["Meetup"] = Relationship(back_populates="participants")
