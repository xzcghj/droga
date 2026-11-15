"""Zaproszenie na czat grupy: fakty liczy kod, AI tylko redaguje tekst."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.adapters.llm.base import LLMBadOutputError, LLMUnavailableError, ToolSpec
from app.api.errors import AppError
from app.container import Container
from app.db.models import Meetup
from app.domain.schedule import departure_time, format_hhmm, format_pl_datetime
from app.domain.types import Point, TravelMode, TravelTime
from app.services.suggestions import people_of, travel_times

MAX_AI_MESSAGE = 600

MODE_LABEL_PL = {
    TravelMode.walk: "pieszo",
    TravelMode.bike: "rowerem",
    TravelMode.transit: "komunikacją",
    TravelMode.car: "autem",
}


@dataclass(frozen=True)
class PersonLine:
    name: str
    mode_label: str
    minutes: int
    depart_at: str  # HH:MM, Europe/Warsaw
    estimate: bool


@dataclass(frozen=True)
class InviteFacts:
    title: str
    venue: str
    when: str  # np. "sobota, 21 listopada, 18:00"
    people: list[PersonLine]


class InviteRead(BaseModel):
    message: str
    source: Literal["ai", "template"]


def build_facts(meetup: Meetup, travel: list[TravelTime]) -> InviteFacts:
    by_id = {t.participant_id: t for t in travel}
    lines = []
    for p in meetup.participants:
        t = by_id[p.id]
        lines.append(
            PersonLine(
                name=p.name,
                mode_label=MODE_LABEL_PL[TravelMode(p.mode)],
                minutes=t.minutes,
                depart_at=format_hhmm(departure_time(meetup.scheduled_at, t.minutes)),
                estimate=t.data_source == "estimate",
            )
        )
    return InviteFacts(
        title=meetup.title,
        venue=meetup.chosen_venue_name or "",
        when=format_pl_datetime(meetup.scheduled_at),
        people=lines,
    )


def render_template(facts: InviteFacts) -> str:
    lines = [
        f"Hej! {facts.title} — {facts.when}, {facts.venue}.",
        "Kto i kiedy wychodzi:",
    ]
    for p in facts.people:
        approx = "≈" if p.estimate else ""
        lines.append(
            f"• {p.name} ({p.mode_label}): {approx}{p.minutes} min, wyjście o {p.depart_at}"
        )
    lines.append("Do zobaczenia!")
    return "\n".join(lines)


def facts_as_prompt(facts: InviteFacts) -> str:
    people = "\n".join(
        f"- {p.name}: {p.mode_label}, dojazd {p.minutes} min"
        f"{' (szacunek)' if p.estimate else ''}, wyjście o {p.depart_at}"
        for p in facts.people
    )
    return (
        f"Nazwa spotkania: {facts.title}\n"
        f"Miejsce: {facts.venue}\n"
        f"Termin: {facts.when}\n"
        f"Uczestnicy:\n{people}"
    )


INVITE_TOOL = ToolSpec(
    name="submit_invite",
    description="Zwróć gotową wiadomość z zaproszeniem.",
    parameters={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": f"Treść zaproszenia po polsku, maks. {MAX_AI_MESSAGE} znaków.",
            }
        },
        "required": ["message"],
    },
)

INVITE_SYSTEM_PROMPT = f"""\
Piszesz krótkie, swobodne zaproszenie na spotkanie, gotowe do wklejenia na grupowy czat.
Pisz po polsku, w tonie luźnym i życzliwym, możesz użyć 1–2 emoji.
Używaj wyłącznie podanych faktów: nazwy miejsca, terminu, imion, czasów dojazdu i godzin wyjścia.
Nie zmieniaj ani nie zaokrąglaj liczb i godzin, nie wymyślaj adresów, cen ani innych szczegółów.
Wymień każdą osobę z jej godziną wyjścia. Maksymalnie {MAX_AI_MESSAGE} znaków.
Wywołaj narzędzie submit_invite z gotową wiadomością.
"""


class _AIInvite(BaseModel):
    message: str = Field(max_length=MAX_AI_MESSAGE)

    @field_validator("message")
    @classmethod
    def _not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("pusta wiadomość")
        return v.strip()


_HHMM = re.compile(r"\b([01]?\d|2[0-3])[:.]([0-5]\d)\b")


def respects_facts(message: str, facts: InviteFacts) -> bool:
    """Tekst AI musi zawierać miejsce, każdą osobę i jej godzinę wyjścia
    oraz nie może podawać godzin spoza faktów (żadna liczba nie pochodzi z modelu)."""
    allowed = {p.depart_at for p in facts.people} | {facts.when[-5:]}
    times = {f"{int(h):02d}:{m}" for h, m in _HHMM.findall(message)}
    return (
        facts.venue in message
        and all(p.name in message for p in facts.people)
        and {p.depart_at for p in facts.people} <= times
        and times <= allowed
    )


class InviteService:
    def __init__(self, container: Container):
        self.container = container

    def generate(self, meetup: Meetup) -> InviteRead:
        if meetup.chosen_venue_name is None or len(meetup.participants) < 2:
            raise AppError(
                422,
                "invite_not_ready",
                "Zaproszenie wymaga wybranego miejsca i co najmniej 2 uczestników.",
            )
        venue = Point(meetup.chosen_venue_lat, meetup.chosen_venue_lon)
        [travel] = travel_times(self.container, people_of(meetup), [venue])
        facts = build_facts(meetup, travel)

        llm = self.container.llm
        if llm is not None:
            try:
                raw = llm.call_tool(INVITE_SYSTEM_PROMPT, facts_as_prompt(facts), INVITE_TOOL)
                message = _AIInvite.model_validate(raw).message
                if respects_facts(message, facts):
                    return InviteRead(message=message, source="ai")
            except (LLMUnavailableError, LLMBadOutputError, ValidationError):
                pass  # tryb bez AI: ta sama treść z szablonu
        return InviteRead(message=render_template(facts), source="template")
