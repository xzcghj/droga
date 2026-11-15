import pytest

from app.adapters.cache import TTLCache
from app.adapters.routing import HaversineRouter
from app.api.errors import AppError
from app.container import Container
from app.db.models import Meetup, Participant
from app.domain.types import Point, TravelMode, Venue, VenueCategory
from app.services.suggestions import SuggestionService, travel_times
from tests.fakes import FailingRouter, FakeRouter, FakeVenues

NEAR = Venue("Blisko", "node/1", Point(54.41, 18.58))
FAR = Venue("Daleko", "node/2", Point(54.50, 18.50))


def meetup(*modes: str, category: str = "cafe") -> Meetup:
    m = Meetup(id=1, title="T", scheduled_at=None, venue_category=VenueCategory(category))
    m.participants = [
        Participant(
            id=i + 1,
            meetup_id=1,
            name=f"P{i}",
            start_label="x",
            lat=54.40 + i * 0.01,
            lon=18.57,
            mode=TravelMode(mode),
        )
        for i, mode in enumerate(modes)
    ]
    return m


def container(router=None, venues=None, **kw) -> Container:
    router = router or FakeRouter()
    return Container(
        routers={"walk": router, "bike": router, "car": router},
        fallback_router=HaversineRouter(),
        venues=venues if venues is not None else FakeVenues([NEAR, FAR]),
        suggestion_cache=TTLCache(600),
        **kw,
    )


def test_returns_ranked_candidates_with_per_person_travel():
    router = FakeRouter(minutes_by_dest={NEAR.point: 7.2, FAR.point: 30.0})
    res = SuggestionService(container(router)).suggest(meetup("walk", "car"), limit=5)
    assert res.venue_source == "overpass"
    assert [c.venue.name for c in res.candidates] == ["Blisko", "Daleko"]
    first = res.candidates[0]
    assert [t.participant_id for t in first.travel] == [1, 2]
    assert [t.minutes for t in first.travel] == [8, 8]  # ceil(7.2)
    assert {t.data_source for t in first.travel} == {"osrm"}
    assert first.max_minutes == 8 and first.total_minutes == 16 and first.spread_minutes == 0


def test_limit_applies():
    res = SuggestionService(container()).suggest(meetup("walk", "car"), limit=1)
    assert len(res.candidates) == 1


def test_less_than_two_participants_422():
    with pytest.raises(AppError) as e:
        SuggestionService(container()).suggest(meetup("walk"), limit=5)
    assert e.value.status == 422 and e.value.code == "not_enough_participants"


def test_router_failure_falls_back_to_estimate():
    res = SuggestionService(container(FailingRouter())).suggest(meetup("walk", "bike"), limit=5)
    assert res.candidates
    assert all(t.data_source == "estimate" for c in res.candidates for t in c.travel)


def test_none_in_matrix_falls_back_per_pair():
    router = FakeRouter(minutes_by_dest={NEAR.point: None, FAR.point: 12.0})
    res = SuggestionService(container(router)).suggest(meetup("walk", "car"), limit=5)
    by_name = {c.venue.name: c for c in res.candidates}
    assert {t.data_source for t in by_name["Blisko"].travel} == {"estimate"}
    assert {t.data_source for t in by_name["Daleko"].travel} == {"osrm"}


def test_only_used_profiles_are_queried():
    router = FakeRouter()
    SuggestionService(container(router)).suggest(meetup("walk", "transit"), limit=5)
    assert [c[0] for c in router.calls] == ["walk"]
    assert router.calls[0][1] == 1  # tylko osoba idąca pieszo jako źródło


def test_transit_is_always_estimate():
    res = SuggestionService(container()).suggest(meetup("transit", "car"), limit=5)
    transit = [t for c in res.candidates for t in c.travel if t.mode == TravelMode.transit]
    assert transit and all(t.data_source == "estimate" for t in transit)


def test_overpass_down_uses_snapshot_source():
    res = SuggestionService(container(venues=FakeVenues([NEAR], "snapshot"))).suggest(
        meetup("walk", "car"), limit=5
    )
    assert res.venue_source == "snapshot" and len(res.candidates) == 1


def test_no_venues_returns_empty_list():
    res = SuggestionService(container(venues=FakeVenues([]))).suggest(meetup("walk", "car"), 5)
    assert res.candidates == []


def test_prefilter_limits_routed_destinations():
    venues = [Venue(f"V{i}", f"node/{i}", Point(54.40 + i * 0.001, 18.57)) for i in range(40)]
    router = FakeRouter()
    SuggestionService(container(router, FakeVenues(venues))).suggest(meetup("walk", "car"), 5)
    assert all(c[2] == 25 for c in router.calls)


def test_cache_hit_skips_router():
    router = FakeRouter()
    c = container(router)
    SuggestionService(c).suggest(meetup("walk", "car"), limit=5)
    n = len(router.calls)
    SuggestionService(c).suggest(meetup("walk", "car"), limit=5)
    assert len(router.calls) == n


def test_cache_invalidated_by_participant_change():
    router = FakeRouter()
    c = container(router)
    SuggestionService(c).suggest(meetup("walk", "car"), limit=5)
    n = len(router.calls)
    SuggestionService(c).suggest(meetup("walk", "bike"), limit=5)
    assert len(router.calls) > n


def test_cache_key_includes_participant_ids():
    c = container()
    m1 = meetup("walk", "car")
    SuggestionService(c).suggest(m1, limit=5)
    m2 = meetup("walk", "car")
    for p in m2.participants:
        p.id += 100
    res = SuggestionService(c).suggest(m2, limit=5)
    assert {t.participant_id for t in res.candidates[0].travel} == {101, 102}


def test_degraded_result_is_not_cached():
    router = FailingRouter()
    c = container(router)
    SuggestionService(c).suggest(meetup("walk", "car"), limit=5)
    first = router.calls
    SuggestionService(c).suggest(meetup("walk", "car"), limit=5)
    assert router.calls == 2 * first


def test_travel_times_rows_are_destinations():
    from app.domain.types import ParticipantPoint

    people = [
        ParticipantPoint(1, Point(54.4, 18.57), TravelMode.walk),
        ParticipantPoint(2, Point(54.41, 18.57), TravelMode.transit),
    ]
    rows = travel_times(container(), people, [NEAR.point, FAR.point])
    assert len(rows) == 2 and all(len(r) == 2 for r in rows)
    assert [t.participant_id for t in rows[0]] == [1, 2]
