from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.api.deps import get_session
from app.api.schemas import MeetupCreate, MeetupRead, MeetupSummary, MeetupUpdate
from app.services.meetups import MeetupService, to_read

router = APIRouter(prefix="/meetups", tags=["meetups"])


@router.get("", response_model=list[MeetupSummary])
def list_meetups(session: Session = Depends(get_session)) -> list[MeetupSummary]:
    return MeetupService(session).list()


@router.post("", response_model=MeetupRead, status_code=201)
def create_meetup(
    data: MeetupCreate, response: Response, session: Session = Depends(get_session)
) -> MeetupRead:
    meetup = MeetupService(session).create(data)
    response.headers["Location"] = f"/api/v1/meetups/{meetup.id}"
    return to_read(meetup)


@router.get("/{meetup_id}", response_model=MeetupRead)
def get_meetup(meetup_id: int, session: Session = Depends(get_session)) -> MeetupRead:
    return to_read(MeetupService(session).get(meetup_id))


@router.patch("/{meetup_id}", response_model=MeetupRead)
def update_meetup(
    meetup_id: int, data: MeetupUpdate, session: Session = Depends(get_session)
) -> MeetupRead:
    return to_read(MeetupService(session).update(meetup_id, data))


@router.delete("/{meetup_id}", status_code=204)
def delete_meetup(meetup_id: int, session: Session = Depends(get_session)) -> Response:
    MeetupService(session).delete(meetup_id)
    return Response(status_code=204)
