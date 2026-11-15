"""Schematy Pydantic wejścia/wyjścia API."""

from __future__ import annotations

from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.domain.types import TravelMode, VenueCategory

Title = Field(min_length=1, max_length=100)


class ChosenVenue(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    osm_id: str = Field(min_length=1, max_length=50)


class MeetupCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    scheduled_at: AwareDatetime
    venue_category: VenueCategory


class MeetupUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    scheduled_at: AwareDatetime | None = None
    venue_category: VenueCategory | None = None
    chosen_venue: ChosenVenue | None = None
    invite_message: str | None = Field(default=None, max_length=1000)


class ParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_label: str
    lat: float
    lon: float
    mode: TravelMode


class MeetupRead(BaseModel):
    id: int
    title: str
    scheduled_at: datetime
    venue_category: VenueCategory
    chosen_venue: ChosenVenue | None
    invite_message: str | None
    participants: list[ParticipantRead]
    created_at: datetime
    updated_at: datetime


class MeetupSummary(BaseModel):
    id: int
    title: str
    scheduled_at: datetime
    venue_category: VenueCategory
    participant_count: int
    chosen_venue_name: str | None
