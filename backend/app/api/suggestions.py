from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.api.deps import get_container, get_session
from app.api.schemas import CandidateRead, SuggestionsRead, TravelRead
from app.container import Container
from app.services.meetups import MeetupService
from app.services.suggestions import SuggestionService

router = APIRouter(tags=["suggestions"])


@router.get("/meetups/{meetup_id}/suggestions", response_model=SuggestionsRead)
def get_suggestions(
    meetup_id: int,
    limit: int = Query(5, ge=1, le=10),
    session: Session = Depends(get_session),
    container: Container = Depends(get_container),
) -> SuggestionsRead:
    meetup = MeetupService(session).get(meetup_id)
    result = SuggestionService(container).suggest(meetup, limit)
    return SuggestionsRead(
        venue_source=result.venue_source,
        candidates=[
            CandidateRead(
                name=c.venue.name,
                osm_id=c.venue.osm_id,
                lat=c.venue.point.lat,
                lon=c.venue.point.lon,
                max_minutes=c.max_minutes,
                total_minutes=c.total_minutes,
                spread_minutes=c.spread_minutes,
                travel=[
                    TravelRead(
                        participant_id=t.participant_id,
                        minutes=t.minutes,
                        mode=t.mode,
                        data_source=t.data_source,
                    )
                    for t in c.travel
                ],
            )
            for c in result.candidates
        ],
    )
