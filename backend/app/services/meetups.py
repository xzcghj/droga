from __future__ import annotations

from sqlalchemy import func
from sqlmodel import Session, select

from app.api.errors import AppError
from app.api.schemas import (
    ChosenVenue,
    MeetupCreate,
    MeetupRead,
    MeetupSummary,
    MeetupUpdate,
    ParticipantRead,
)
from app.db.models import Meetup, Participant, utcnow


def chosen_venue_of(m: Meetup) -> ChosenVenue | None:
    if m.chosen_venue_name is None:
        return None
    return ChosenVenue(
        name=m.chosen_venue_name,
        lat=m.chosen_venue_lat,
        lon=m.chosen_venue_lon,
        osm_id=m.chosen_venue_osm_id,
    )


def to_read(m: Meetup) -> MeetupRead:
    return MeetupRead(
        id=m.id,
        title=m.title,
        scheduled_at=m.scheduled_at,
        venue_category=m.venue_category,
        chosen_venue=chosen_venue_of(m),
        invite_message=m.invite_message,
        participants=[ParticipantRead.model_validate(p) for p in m.participants],
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class MeetupService:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[MeetupSummary]:
        count = (
            select(Participant.meetup_id, func.count().label("n"))
            .group_by(Participant.meetup_id)
            .subquery()
        )
        rows = self.session.exec(
            select(Meetup, func.coalesce(count.c.n, 0))
            .outerjoin(count, count.c.meetup_id == Meetup.id)
            .order_by(Meetup.scheduled_at, Meetup.id)
        ).all()
        return [
            MeetupSummary(
                id=m.id,
                title=m.title,
                scheduled_at=m.scheduled_at,
                venue_category=m.venue_category,
                participant_count=n,
                chosen_venue_name=m.chosen_venue_name,
            )
            for m, n in rows
        ]

    def get(self, meetup_id: int) -> Meetup:
        meetup = self.session.get(Meetup, meetup_id)
        if meetup is None:
            raise AppError(404, "meetup_not_found", f"Spotkanie o id {meetup_id} nie istnieje.")
        return meetup

    def create(self, data: MeetupCreate) -> Meetup:
        meetup = Meetup(**data.model_dump())
        self.session.add(meetup)
        self.session.commit()
        self.session.refresh(meetup)
        return meetup

    def update(self, meetup_id: int, data: MeetupUpdate) -> Meetup:
        meetup = self.get(meetup_id)
        changes = data.model_dump(exclude_unset=True)
        old_venue_id = meetup.chosen_venue_osm_id
        if "chosen_venue" in changes:
            venue = data.chosen_venue
            meetup.chosen_venue_name = venue.name if venue else None
            meetup.chosen_venue_lat = venue.lat if venue else None
            meetup.chosen_venue_lon = venue.lon if venue else None
            meetup.chosen_venue_osm_id = venue.osm_id if venue else None
            changes.pop("chosen_venue")
        for field in ("title", "scheduled_at", "venue_category"):
            if field in changes and changes[field] is None:
                raise AppError(
                    422,
                    "validation_error",
                    "Niepoprawne dane wejściowe.",
                    [{"field": field, "message": "Pole nie może być puste."}],
                )
        facts_changed = "chosen_venue" in data.model_fields_set and (
            data.chosen_venue is None or data.chosen_venue.osm_id != old_venue_id
        )
        if "scheduled_at" in changes and changes["scheduled_at"] != meetup.scheduled_at:
            facts_changed = True
        if facts_changed and "invite_message" not in changes:
            meetup.invite_message = None  # stare zaproszenie ma nieaktualne miejsce/godziny
        for key, value in changes.items():
            setattr(meetup, key, value)
        meetup.updated_at = utcnow()
        self.session.add(meetup)
        self.session.commit()
        self.session.refresh(meetup)
        return meetup

    def delete(self, meetup_id: int) -> None:
        meetup = self.get(meetup_id)
        self.session.delete(meetup)
        self.session.commit()
