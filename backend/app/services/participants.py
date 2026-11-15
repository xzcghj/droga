from __future__ import annotations

from sqlalchemy import func
from sqlmodel import Session, select

from app.adapters.geocoding import Geocoder
from app.adapters.http import AdapterError
from app.api.errors import AppError
from app.api.schemas import ParticipantCreate, ParticipantUpdate
from app.db.models import Participant
from app.domain.types import Point
from app.services.meetups import MeetupService

MAX_PARTICIPANTS = 10


def geocode_first(geocoder: Geocoder, label: str) -> Point:
    try:
        results = geocoder.search(label, limit=1)
    except AdapterError as exc:
        raise AppError(
            503,
            "geocoding_unavailable",
            "Usługa wyszukiwania adresów jest chwilowo niedostępna. Spróbuj za chwilę.",
        ) from exc
    if not results:
        raise AppError(
            422,
            "address_not_found",
            f"Nie znaleziono adresu „{label}” — dopisz miasto lub ulicę.",
            {"start_label": label},
        )
    return results[0].point


class ParticipantService:
    def __init__(self, session: Session, geocoder: Geocoder):
        self.session = session
        self.geocoder = geocoder
        self.meetups = MeetupService(session)

    def list(self, meetup_id: int) -> list[Participant]:
        self.meetups.get(meetup_id)
        return list(
            self.session.exec(
                select(Participant)
                .where(Participant.meetup_id == meetup_id)
                .order_by(Participant.id)
            ).all()
        )

    def _count(self, meetup_id: int) -> int:
        return self.session.exec(
            select(func.count()).select_from(Participant).where(Participant.meetup_id == meetup_id)
        ).one()

    def _ensure_room(self, meetup_id: int, adding: int) -> None:
        if self._count(meetup_id) + adding > MAX_PARTICIPANTS:
            raise AppError(
                409,
                "participant_limit",
                f"Spotkanie może mieć maksymalnie {MAX_PARTICIPANTS} uczestników.",
            )

    def _build(self, meetup_id: int, data: ParticipantCreate) -> Participant:
        if data.lat is None or data.lon is None:
            point = geocode_first(self.geocoder, data.start_label)
        else:
            point = Point(data.lat, data.lon)
        return Participant(
            meetup_id=meetup_id,
            name=data.name,
            start_label=data.start_label,
            mode=data.mode,
            lat=point.lat,
            lon=point.lon,
        )

    def add(self, meetup_id: int, data: ParticipantCreate) -> Participant:
        return self.add_many(meetup_id, [data])[0]

    def add_many(self, meetup_id: int, items: list[ParticipantCreate]) -> list[Participant]:
        """Atomowo: albo wszyscy zapisani, albo nikt."""
        self.meetups.get(meetup_id)
        self._ensure_room(meetup_id, len(items))
        built = [self._build(meetup_id, item) for item in items]
        self.session.add_all(built)
        self.session.commit()
        for p in built:
            self.session.refresh(p)
        return built

    def get(self, meetup_id: int, pid: int) -> Participant:
        self.meetups.get(meetup_id)
        p = self.session.get(Participant, pid)
        if p is None or p.meetup_id != meetup_id:
            raise AppError(
                404,
                "participant_not_found",
                f"Uczestnik o id {pid} nie należy do spotkania {meetup_id}.",
            )
        return p

    def update(self, meetup_id: int, pid: int, data: ParticipantUpdate) -> Participant:
        p = self.get(meetup_id, pid)
        changes = data.model_dump(exclude_unset=True)
        for field in ("name", "start_label", "mode"):
            if field in changes and changes[field] is None:
                raise AppError(
                    422,
                    "validation_error",
                    "Niepoprawne dane wejściowe.",
                    [{"field": field, "message": "Pole nie może być puste."}],
                )
        if data.lat is not None and data.lon is not None:
            p.lat, p.lon = data.lat, data.lon
        elif "start_label" in changes and changes["start_label"] != p.start_label:
            point = geocode_first(self.geocoder, changes["start_label"])
            p.lat, p.lon = point.lat, point.lon
        for field in ("name", "start_label", "mode"):
            if field in changes:
                setattr(p, field, changes[field])
        self.session.add(p)
        self.session.commit()
        self.session.refresh(p)
        return p

    def delete(self, meetup_id: int, pid: int) -> None:
        p = self.get(meetup_id, pid)
        self.session.delete(p)
        self.session.commit()
