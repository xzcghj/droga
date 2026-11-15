from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db.models import Meetup
from app.db.seed import next_saturday_15, seed_demo
from app.main import create_app
from tests.conftest import make_container


def test_seed_runs_once_on_empty_db(test_settings):
    settings = test_settings.model_copy(update={"seed_demo": True})
    app = create_app(settings, make_container())
    with TestClient(app) as client:
        items = client.get("/api/v1/meetups").json()
        assert [m["title"] for m in items] == ["Kawa w sobotę"]
        assert items[0]["participant_count"] == 4
        detail = client.get(f"/api/v1/meetups/{items[0]['id']}").json()
        assert detail["venue_category"] == "cafe"
        assert [(p["name"], p["mode"]) for p in detail["participants"]] == [
            ("Ola", "transit"),
            ("Kuba", "bike"),
            ("Ja", "walk"),
            ("Marta", "car"),
        ]
        assert detail["participants"][0]["lat"] == 54.5203
    with Session(app.state.engine) as s:
        seed_demo(s)
        assert len(s.exec(select(Meetup)).all()) == 1


def test_seed_skipped_when_disabled(client):
    assert client.get("/api/v1/meetups").json() == []


def test_next_saturday_is_15_warsaw():
    # piątek 2026-11-20 12:00 UTC → sobota 21.11 15:00 PL = 14:00 UTC
    got = next_saturday_15(datetime(2026, 11, 20, 12, 0, tzinfo=UTC))
    assert got == datetime(2026, 11, 21, 14, 0, tzinfo=UTC)
    # sobota po 15:00 → następna sobota
    got = next_saturday_15(datetime(2026, 11, 21, 15, 0, tzinfo=UTC))
    assert got == datetime(2026, 11, 28, 14, 0, tzinfo=UTC)
