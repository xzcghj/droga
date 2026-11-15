MEETUP = {"title": "Kawa", "scheduled_at": "2026-11-21T18:00:00+01:00", "venue_category": "cafe"}


def setup_meetup(client, n_people: int) -> int:
    mid = client.post("/api/v1/meetups", json=MEETUP).json()["id"]
    for i in range(n_people):
        client.post(
            f"/api/v1/meetups/{mid}/participants",
            json={
                "name": f"P{i}",
                "start_label": "x",
                "mode": "walk",
                "lat": 54.4 + i / 100,
                "lon": 18.57,
            },
        )
    return mid


def test_api_returns_spec_shape(client):
    mid = setup_meetup(client, 2)
    r = client.get(f"/api/v1/meetups/{mid}/suggestions")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["venue_source"] == "overpass"
    c = body["candidates"][0]
    assert set(c) == {
        "name",
        "osm_id",
        "lat",
        "lon",
        "max_minutes",
        "total_minutes",
        "spread_minutes",
        "travel",
    }
    assert set(c["travel"][0]) == {"participant_id", "minutes", "mode", "data_source"}


def test_api_limit_bounds_422(client):
    mid = setup_meetup(client, 2)
    assert client.get(f"/api/v1/meetups/{mid}/suggestions?limit=0").status_code == 422
    assert client.get(f"/api/v1/meetups/{mid}/suggestions?limit=11").status_code == 422


def test_api_not_enough_participants_422(client):
    mid = setup_meetup(client, 1)
    r = client.get(f"/api/v1/meetups/{mid}/suggestions")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "not_enough_participants"


def test_api_missing_meetup_404(client):
    assert client.get("/api/v1/meetups/999/suggestions").status_code == 404
