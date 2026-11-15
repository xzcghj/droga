from datetime import datetime

BASE = {"title": "Kawa", "scheduled_at": "2026-11-21T18:00:00+01:00", "venue_category": "cafe"}
VENUE = {"name": "Kawiarnia X", "lat": 54.44, "lon": 18.56, "osm_id": "node/123"}


def create(client, **overrides):
    r = client.post("/api/v1/meetups", json={**BASE, **overrides})
    assert r.status_code == 201, r.text
    return r.json()


def test_create_returns_201_with_location(client):
    r = client.post("/api/v1/meetups", json=BASE)
    assert r.status_code == 201
    assert r.headers["location"] == f"/api/v1/meetups/{r.json()['id']}"
    assert r.json()["participants"] == [] and r.json()["chosen_venue"] is None


def test_scheduled_at_roundtrips_as_same_instant(client):
    m = create(client)
    got = client.get(f"/api/v1/meetups/{m['id']}").json()["scheduled_at"]
    assert datetime.fromisoformat(got) == datetime.fromisoformat("2026-11-21T17:00:00+00:00")
    assert datetime.fromisoformat(got).utcoffset() is not None


def test_naive_datetime_rejected_422(client):
    r = client.post("/api/v1/meetups", json={**BASE, "scheduled_at": "2026-11-21T18:00:00"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_meetup_title_with_polish_characters_roundtrips(client):
    title = "Spotkanie w Gdańsku — Łódź?"
    m = create(client, title=title)
    assert client.get(f"/api/v1/meetups/{m['id']}").json()["title"] == title


def test_list_returns_summaries_sorted_by_date(client):
    create(client, title="Późne", scheduled_at="2026-12-01T18:00:00+01:00")
    create(client, title="Wczesne", scheduled_at="2026-11-01T18:00:00+01:00")
    r = client.get("/api/v1/meetups")
    assert r.status_code == 200
    items = r.json()
    assert [i["title"] for i in items] == ["Wczesne", "Późne"]
    assert items[0]["participant_count"] == 0
    assert items[0]["chosen_venue_name"] is None


def test_get_missing_returns_404_meetup_not_found(client):
    r = client.get("/api/v1/meetups/999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "meetup_not_found"


def test_patch_sets_and_clears_chosen_venue(client):
    m = create(client)
    r = client.patch(f"/api/v1/meetups/{m['id']}", json={"chosen_venue": VENUE})
    assert r.status_code == 200
    assert r.json()["chosen_venue"] == VENUE
    r = client.patch(f"/api/v1/meetups/{m['id']}", json={"title": "Nowa"})
    assert r.json()["chosen_venue"] == VENUE and r.json()["title"] == "Nowa"
    r = client.patch(f"/api/v1/meetups/{m['id']}", json={"chosen_venue": None})
    assert r.json()["chosen_venue"] is None


def test_patch_partial_chosen_venue_rejected_422(client):
    m = create(client)
    bad = {k: v for k, v in VENUE.items() if k != "lat"}
    r = client.patch(f"/api/v1/meetups/{m['id']}", json={"chosen_venue": bad})
    assert r.status_code == 422


def test_patch_invite_message_too_long_422(client):
    m = create(client)
    r = client.patch(f"/api/v1/meetups/{m['id']}", json={"invite_message": "x" * 1001})
    assert r.status_code == 422


def test_delete_returns_204_then_404(client):
    m = create(client)
    assert client.delete(f"/api/v1/meetups/{m['id']}").status_code == 204
    assert client.get(f"/api/v1/meetups/{m['id']}").status_code == 404


def test_title_too_long_422_with_field_detail(client):
    r = client.post("/api/v1/meetups", json={**BASE, "title": "x" * 101})
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["field"] == "title"


def test_changing_venue_or_time_clears_saved_invite(client):
    m = create(client)
    url = f"/api/v1/meetups/{m['id']}"
    client.patch(url, json={"chosen_venue": VENUE, "invite_message": "Stare"})
    assert client.get(url).json()["invite_message"] == "Stare"
    other = {**VENUE, "osm_id": "node/999", "name": "Inna"}
    assert client.patch(url, json={"chosen_venue": other}).json()["invite_message"] is None
    client.patch(url, json={"invite_message": "Nowe"})
    r = client.patch(url, json={"scheduled_at": "2026-11-22T18:00:00+01:00"})
    assert r.json()["invite_message"] is None


def test_title_change_keeps_saved_invite(client):
    m = create(client)
    url = f"/api/v1/meetups/{m['id']}"
    client.patch(url, json={"chosen_venue": VENUE, "invite_message": "Zostaje"})
    assert client.patch(url, json={"title": "Nowy"}).json()["invite_message"] == "Zostaje"
