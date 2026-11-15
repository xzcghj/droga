import pytest
from sqlmodel import Session, select

from app.db.models import Participant

MEETUP = {"title": "Kawa", "scheduled_at": "2026-11-21T18:00:00+01:00", "venue_category": "cafe"}


def person(i: int = 0, **kw):
    return {"name": f"Osoba {i}", "start_label": f"Gdańsk {i}", "mode": "walk", **kw}


def new_meetup(client) -> int:
    return client.post("/api/v1/meetups", json=MEETUP).json()["id"]


@pytest.fixture
def meetup_id(client) -> int:
    return new_meetup(client)


def url(mid: int, suffix: str = "") -> str:
    return f"/api/v1/meetups/{mid}/participants{suffix}"


def test_add_participant_geocodes_label(client, meetup_id, fake_geocoder):
    r = client.post(url(meetup_id), json=person(name="Łukasz", start_label="Gdańsk Wrzeszcz"))
    assert r.status_code == 201, r.text
    body = r.json()
    assert r.headers["location"] == f"/api/v1/meetups/{meetup_id}/participants/{body['id']}"
    assert (body["lat"], body["lon"]) == (fake_geocoder.point.lat, fake_geocoder.point.lon)
    assert body["name"] == "Łukasz"
    assert fake_geocoder.queries == ["Gdańsk Wrzeszcz"]


def test_add_participant_with_coords_skips_geocoder(client, meetup_id, fake_geocoder):
    r = client.post(url(meetup_id), json=person(lat=54.5, lon=18.5))
    assert r.status_code == 201
    assert (r.json()["lat"], r.json()["lon"]) == (54.5, 18.5)
    assert fake_geocoder.queries == []


def test_add_participant_with_only_lat_422(client, meetup_id):
    assert client.post(url(meetup_id), json=person(lat=54.5)).status_code == 422


def test_add_participant_unknown_address_422(client, meetup_id, fake_geocoder):
    fake_geocoder.missing.add("Atlantyda")
    r = client.post(url(meetup_id), json=person(start_label="Atlantyda"))
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "address_not_found"
    assert r.json()["error"]["details"] == {"start_label": "Atlantyda"}


def test_geocoder_down_503(client, meetup_id, fake_geocoder):
    fake_geocoder.fail = True
    r = client.post(url(meetup_id), json=person())
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "geocoding_unavailable"


def test_list_participants(client, meetup_id):
    client.post(url(meetup_id), json=person(1))
    client.post(url(meetup_id), json=person(2))
    r = client.get(url(meetup_id))
    assert [p["name"] for p in r.json()] == ["Osoba 1", "Osoba 2"]
    assert client.get(f"/api/v1/meetups/{meetup_id}").json()["participants"][1]["name"] == "Osoba 2"


def test_eleventh_participant_409(client, meetup_id):
    for i in range(10):
        assert client.post(url(meetup_id), json=person(i)).status_code == 201
    r = client.post(url(meetup_id), json=person(11))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "participant_limit"


def test_batch_adds_all(client, meetup_id):
    r = client.post(url(meetup_id, "/batch"), json={"participants": [person(1), person(2)]})
    assert r.status_code == 201
    assert [p["name"] for p in r.json()] == ["Osoba 1", "Osoba 2"]


def test_batch_over_limit_saves_nothing(client, meetup_id):
    for i in range(8):
        client.post(url(meetup_id), json=person(i))
    batch = {"participants": [person(i) for i in range(20, 23)]}
    r = client.post(url(meetup_id, "/batch"), json=batch)
    assert r.status_code == 409
    assert len(client.get(url(meetup_id)).json()) == 8


def test_batch_unknown_address_saves_nothing(client, meetup_id, fake_geocoder):
    fake_geocoder.missing.add("Atlantyda")
    batch = {"participants": [person(1), person(2, start_label="Atlantyda")]}
    r = client.post(url(meetup_id, "/batch"), json=batch)
    assert r.status_code == 422
    assert client.get(url(meetup_id)).json() == []


def test_update_participant_mode_and_regeocode(client, meetup_id, fake_geocoder):
    pid = client.post(url(meetup_id), json=person(lat=1.0, lon=2.0)).json()["id"]
    r = client.patch(url(meetup_id, f"/{pid}"), json={"mode": "bike"})
    assert r.json()["mode"] == "bike" and r.json()["lat"] == 1.0
    r = client.patch(url(meetup_id, f"/{pid}"), json={"start_label": "Oliwa"})
    assert r.json()["start_label"] == "Oliwa"
    assert r.json()["lat"] == fake_geocoder.point.lat
    assert fake_geocoder.queries == ["Oliwa"]


def test_delete_participant_204(client, meetup_id):
    pid = client.post(url(meetup_id), json=person()).json()["id"]
    assert client.delete(url(meetup_id, f"/{pid}")).status_code == 204
    assert client.get(url(meetup_id)).json() == []


def test_participant_of_other_meetup_404(client):
    a, b = new_meetup(client), new_meetup(client)
    pid = client.post(url(a), json=person()).json()["id"]
    r = client.patch(url(b, f"/{pid}"), json={"mode": "car"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "participant_not_found"
    assert client.delete(url(b, f"/{pid}")).status_code == 404


def test_participants_of_missing_meetup_404(client):
    assert client.post(url(999), json=person()).json()["error"]["code"] == "meetup_not_found"


def test_deleting_meetup_cascades_participants(client, session, meetup_id):
    client.post(url(meetup_id), json=person())
    client.delete(f"/api/v1/meetups/{meetup_id}")
    assert session.exec(select(Participant)).all() == []


def test_geocode_endpoint_returns_matches(client, fake_geocoder):
    r = client.post("/api/v1/geocode", json={"query": "Sopot"})
    assert r.status_code == 200
    assert r.json() == {
        "results": [
            {"label": "Sopot", "lat": fake_geocoder.point.lat, "lon": fake_geocoder.point.lon}
        ]
    }


def test_geocode_endpoint_empty_query_422(client):
    assert client.post("/api/v1/geocode", json={"query": ""}).status_code == 422


def test_session_fixture_is_same_db(client, session):
    assert isinstance(session, Session)
