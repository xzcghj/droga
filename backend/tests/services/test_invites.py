from datetime import UTC, datetime

import pytest

from app.adapters.cache import TTLCache
from app.adapters.llm.base import LLMBadOutputError, LLMUnavailableError
from app.adapters.routing import HaversineRouter
from app.api.errors import AppError
from app.container import Container
from app.db.models import Meetup, Participant
from app.domain.types import Point, TravelMode, VenueCategory
from app.services.invites import INVITE_SYSTEM_PROMPT, InviteService, build_facts, render_template
from app.services.suggestions import people_of, travel_times
from tests.fakes import FakeLLM, FakeRouter, FakeVenues

WINTER = datetime(2026, 11, 21, 17, 0, tzinfo=UTC)  # 18:00 w Polsce
SUMMER = datetime(2026, 7, 11, 16, 0, tzinfo=UTC)  # 18:00 w Polsce (UTC+2)


def meetup(when=WINTER, chosen=True, n=2) -> Meetup:
    m = Meetup(id=1, title="Kawa w sobotę", scheduled_at=when, venue_category=VenueCategory.cafe)
    if chosen:
        m.chosen_venue_name, m.chosen_venue_osm_id = "Kawiarnia Łąka", "node/1"
        m.chosen_venue_lat, m.chosen_venue_lon = 54.44, 18.56
    modes = [TravelMode.walk, TravelMode.car, TravelMode.bike]
    names = ["Łukasz", "Ola", "Kuba"]
    m.participants = [
        Participant(
            id=i + 1,
            meetup_id=1,
            name=names[i],
            start_label="x",
            lat=54.40,
            lon=18.57,
            mode=modes[i],
        )
        for i in range(n)
    ]
    return m


def container(llm=None) -> Container:
    router = FakeRouter(default=17.0)
    return Container(
        routers={"walk": router, "bike": router, "car": router},
        fallback_router=HaversineRouter(),
        venues=FakeVenues([]),
        suggestion_cache=TTLCache(600),
        llm=llm,
        ai_provider="gemini" if llm else None,
    )


def facts_of(m: Meetup):
    point = Point(m.chosen_venue_lat, m.chosen_venue_lon)
    [travel] = travel_times(container(), people_of(m), [point])
    return build_facts(m, travel)


def test_departure_lines_use_warsaw_time():
    for when in (WINTER, SUMMER):
        facts = facts_of(meetup(when))
        assert [line.depart_at for line in facts.people] == ["17:35", "17:35"]
        assert facts.when.endswith("18:00")


def test_facts_contain_minutes_and_mode_labels():
    facts = facts_of(meetup())
    assert [(p.name, p.mode_label, p.minutes) for p in facts.people] == [
        ("Łukasz", "pieszo", 17),
        ("Ola", "autem", 17),
    ]
    assert facts.venue == "Kawiarnia Łąka"


def test_template_contains_every_participant_and_venue():
    text = render_template(facts_of(meetup(n=3)))
    for needle in ["Kawiarnia Łąka", "Łukasz", "Ola", "Kuba", "17:35", "17 min", "18:00"]:
        assert needle in text
    assert len(text) <= 1000


@pytest.mark.parametrize("kw", [{"chosen": False}, {"n": 1}])
def test_invite_not_ready_422(kw):
    with pytest.raises(AppError) as e:
        InviteService(container()).generate(meetup(**kw))
    assert e.value.status == 422 and e.value.code == "invite_not_ready"


def test_invite_uses_ai_message():
    llm = FakeLLM({"message": "Hej, widzimy się w Kawiarni Łąka!"})
    out = InviteService(container(llm)).generate(meetup())
    assert out.source == "ai" and out.message == "Hej, widzimy się w Kawiarni Łąka!"


def test_invite_falls_back_to_template_without_llm():
    out = InviteService(container()).generate(meetup())
    assert out.source == "template" and "Kawiarnia Łąka" in out.message


def test_invite_falls_back_when_ai_message_too_long():
    out = InviteService(container(FakeLLM({"message": "x" * 601}))).generate(meetup())
    assert out.source == "template"


@pytest.mark.parametrize(
    "llm",
    [
        FakeLLM(error=LLMUnavailableError("429")),
        FakeLLM(error=LLMBadOutputError("brak")),
        FakeLLM({"wrong": 1}),
        FakeLLM({"message": "   "}),
    ],
)
def test_invite_falls_back_on_ai_errors(llm):
    assert InviteService(container(llm)).generate(meetup()).source == "template"


def test_invite_prompt_contains_computed_numbers():
    llm = FakeLLM({"message": "ok"})
    InviteService(container(llm)).generate(meetup())
    call = llm.calls[0]
    assert "17:35" in call["user"] and "17 min" in call["user"] and "Łukasz" in call["user"]
    assert call["system"] == INVITE_SYSTEM_PROMPT
    assert "nie zmieniaj" in INVITE_SYSTEM_PROMPT.lower()


def test_invite_endpoint(client):
    mid = client.post(
        "/api/v1/meetups",
        json={"title": "K", "scheduled_at": "2026-11-21T18:00:00+01:00", "venue_category": "cafe"},
    ).json()["id"]
    r = client.post(f"/api/v1/meetups/{mid}/invite")
    assert r.status_code == 422 and r.json()["error"]["code"] == "invite_not_ready"
    for i in range(2):
        client.post(
            f"/api/v1/meetups/{mid}/participants",
            json={"name": f"P{i}", "start_label": "x", "mode": "walk", "lat": 54.4, "lon": 18.57},
        )
    client.patch(
        f"/api/v1/meetups/{mid}",
        json={"chosen_venue": {"name": "Kawiarnia", "lat": 54.41, "lon": 18.58, "osm_id": "n/1"}},
    )
    r = client.post(f"/api/v1/meetups/{mid}/invite")
    assert r.status_code == 200, r.text
    assert r.json()["source"] == "template" and "Kawiarnia" in r.json()["message"]
    assert client.get(f"/api/v1/meetups/{mid}").json()["invite_message"] is None
