from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_container, get_session
from app.api.schemas import ParseRequest, ParticipantDraft
from app.container import Container
from app.services.imports import ImportService
from app.services.invites import InviteRead, InviteService
from app.services.meetups import MeetupService

router = APIRouter(tags=["ai"])


@router.post("/ai/parse-participants", response_model=ParticipantDraft)
def parse_participants(
    data: ParseRequest, container: Container = Depends(get_container)
) -> ParticipantDraft:
    """Zamienia wiadomość z czatu na szkic uczestników. Nic nie zapisuje."""
    return ImportService(container.llm, container.geocoder).parse(data.text)


@router.post("/meetups/{meetup_id}/invite", response_model=InviteRead)
def generate_invite(
    meetup_id: int,
    session: Session = Depends(get_session),
    container: Container = Depends(get_container),
) -> InviteRead:
    """Generuje treść zaproszenia. Nie zapisuje — zapis przez PATCH /meetups/{id}."""
    meetup = MeetupService(session).get(meetup_id)
    return InviteService(container).generate(meetup)
