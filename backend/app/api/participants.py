from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.api.deps import get_container, get_session
from app.api.schemas import (
    ParticipantBatchCreate,
    ParticipantCreate,
    ParticipantRead,
    ParticipantUpdate,
)
from app.container import Container
from app.services.participants import ParticipantService

router = APIRouter(prefix="/meetups/{meetup_id}/participants", tags=["participants"])


def get_service(
    session: Session = Depends(get_session), container: Container = Depends(get_container)
) -> ParticipantService:
    return ParticipantService(session, container.geocoder)


@router.get("", response_model=list[ParticipantRead])
def list_participants(meetup_id: int, svc: ParticipantService = Depends(get_service)):
    return svc.list(meetup_id)


@router.post("", response_model=ParticipantRead, status_code=201)
def add_participant(
    meetup_id: int,
    data: ParticipantCreate,
    response: Response,
    svc: ParticipantService = Depends(get_service),
):
    p = svc.add(meetup_id, data)
    response.headers["Location"] = f"/api/v1/meetups/{meetup_id}/participants/{p.id}"
    return p


@router.post("/batch", response_model=list[ParticipantRead], status_code=201)
def add_participants(
    meetup_id: int, data: ParticipantBatchCreate, svc: ParticipantService = Depends(get_service)
):
    return svc.add_many(meetup_id, data.participants)


@router.patch("/{pid}", response_model=ParticipantRead)
def update_participant(
    meetup_id: int,
    pid: int,
    data: ParticipantUpdate,
    svc: ParticipantService = Depends(get_service),
):
    return svc.update(meetup_id, pid, data)


@router.delete("/{pid}", status_code=204)
def delete_participant(
    meetup_id: int, pid: int, svc: ParticipantService = Depends(get_service)
) -> Response:
    svc.delete(meetup_id, pid)
    return Response(status_code=204)
