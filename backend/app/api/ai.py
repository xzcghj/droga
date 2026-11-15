from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_container
from app.api.schemas import ParseRequest, ParticipantDraft
from app.container import Container
from app.services.imports import ImportService

router = APIRouter(tags=["ai"])


@router.post("/ai/parse-participants", response_model=ParticipantDraft)
def parse_participants(
    data: ParseRequest, container: Container = Depends(get_container)
) -> ParticipantDraft:
    """Zamienia wiadomość z czatu na szkic uczestników. Nic nie zapisuje."""
    return ImportService(container.llm, container.geocoder).parse(data.text)
