"""Schematy Pydantic wejścia/wyjścia API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from app.domain.types import TravelMode, VenueCategory


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


def _coords_together(lat: float | None, lon: float | None) -> None:
    if (lat is None) != (lon is None):
        raise ValueError("Podaj obie współrzędne (lat i lon) albo żadnej.")


class ParticipantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    start_label: str = Field(min_length=1, max_length=200)
    mode: TravelMode
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def _check_coords(self) -> ParticipantCreate:
        _coords_together(self.lat, self.lon)
        return self


class ParticipantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    start_label: str | None = Field(default=None, min_length=1, max_length=200)
    mode: TravelMode | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def _check_coords(self) -> ParticipantUpdate:
        _coords_together(self.lat, self.lon)
        return self


class ParticipantBatchCreate(BaseModel):
    participants: list[ParticipantCreate] = Field(min_length=1, max_length=10)


class GeocodeRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)


class GeocodeMatch(BaseModel):
    label: str
    lat: float
    lon: float


class GeocodeResponse(BaseModel):
    results: list[GeocodeMatch]


class TravelRead(BaseModel):
    participant_id: int
    minutes: int
    mode: TravelMode
    data_source: Literal["osrm", "estimate"]


class CandidateRead(BaseModel):
    name: str
    osm_id: str
    lat: float
    lon: float
    max_minutes: int
    total_minutes: int
    spread_minutes: int
    travel: list[TravelRead]


class SuggestionsRead(BaseModel):
    candidates: list[CandidateRead]
    venue_source: Literal["overpass", "snapshot"]


class ParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    meetup_id: int | None = None


class DraftParticipant(BaseModel):
    name: str
    start_label: str
    mode: TravelMode | None
    note: str | None
    lat: float | None
    lon: float | None
    geocode_error: bool


class ParticipantDraft(BaseModel):
    participants: list[DraftParticipant]
    unparsed: list[str]
