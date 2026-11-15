import json

import httpx
import pytest

from app.adapters.http import AdapterError
from app.adapters.venues import FallbackVenues, OverpassVenues, SnapshotVenues
from app.domain.types import BBox, Point, Venue, VenueCategory

BOX = BBox(south=54.30, west=18.40, north=54.60, east=18.80)

OVERPASS_JSON = {
    "elements": [
        {"type": "node", "id": 1, "lat": 54.44, "lon": 18.56, "tags": {"name": "Kawiarnia A"}},
        {
            "type": "way",
            "id": 2,
            "center": {"lat": 54.40, "lon": 18.60},
            "tags": {"name": "Park B"},
        },
        {"type": "node", "id": 3, "lat": 54.41, "lon": 18.57, "tags": {}},
    ]
}


def overpass_with(handlers):
    calls = []
    it = iter(handlers)

    def wrapped(request):
        calls.append(request)
        return next(it)(request)

    client = httpx.Client(transport=httpx.MockTransport(wrapped))
    return OverpassVenues(client, ["https://op1.test/api", "https://op2.test/api"]), calls


def query_of(request: httpx.Request) -> str:
    return httpx.QueryParams(request.content.decode()).get("data")


def test_overpass_query_contains_category_tags_and_bbox():
    src, calls = overpass_with([lambda r: httpx.Response(200, json={"elements": []})])
    src.find(VenueCategory.bar, BOX)
    q = query_of(calls[0])
    assert q.startswith("[out:json][timeout:25];")
    assert '["amenity"="bar"]["name"](54.3,18.4,54.6,18.8)' in q
    assert '["amenity"="pub"]["name"](54.3,18.4,54.6,18.8)' in q
    assert "out center 300;" in q


def test_overpass_park_uses_leisure_tag():
    src, calls = overpass_with([lambda r: httpx.Response(200, json={"elements": []})])
    src.find(VenueCategory.park, BOX, limit=50)
    q = query_of(calls[0])
    assert '["leisure"="park"]["name"]' in q and "out center 50;" in q


def test_overpass_uses_center_for_ways():
    src, _ = overpass_with([lambda r: httpx.Response(200, json=OVERPASS_JSON)])
    venues = src.find(VenueCategory.cafe, BOX)
    assert venues == [
        Venue("Kawiarnia A", "node/1", Point(54.44, 18.56)),
        Venue("Park B", "way/2", Point(54.40, 18.60)),
    ]


def test_overpass_tries_second_url_on_failure():
    src, calls = overpass_with(
        [
            lambda r: httpx.Response(504),
            lambda r: httpx.Response(504),
            lambda r: httpx.Response(200, json=OVERPASS_JSON),
        ]
    )
    assert len(src.find(VenueCategory.cafe, BOX)) == 2
    assert calls[-1].url.host == "op2.test"


def test_overpass_all_urls_fail_raises():
    src, _ = overpass_with([lambda r: httpx.Response(500)] * 4)
    with pytest.raises(AdapterError):
        src.find(VenueCategory.cafe, BOX)


def write_snapshot(tmp_path):
    path = tmp_path / "venues.json"
    path.write_text(
        json.dumps(
            {
                "attribution": "© OpenStreetMap contributors, ODbL",
                "venues": [
                    {
                        "name": "Café Ł",
                        "osm_id": "node/1",
                        "lat": 54.44,
                        "lon": 18.56,
                        "category": "cafe",
                    },
                    {
                        "name": "Daleko",
                        "osm_id": "node/2",
                        "lat": 52.0,
                        "lon": 21.0,
                        "category": "cafe",
                    },
                    {
                        "name": "Bar",
                        "osm_id": "node/3",
                        "lat": 54.44,
                        "lon": 18.56,
                        "category": "bar",
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def test_snapshot_filters_by_category_and_bbox(tmp_path):
    src = SnapshotVenues(write_snapshot(tmp_path))
    assert src.find(VenueCategory.cafe, BOX) == [Venue("Café Ł", "node/1", Point(54.44, 18.56))]


def test_snapshot_missing_file_is_empty(tmp_path):
    assert SnapshotVenues(tmp_path / "nope.json").find(VenueCategory.cafe, BOX) == []


class Static:
    def __init__(self, venues=None, error=None):
        self.venues, self.error = venues or [], error

    def find(self, category, bbox, limit=300):
        if self.error:
            raise self.error
        return self.venues


V = Venue("X", "node/9", Point(54.4, 18.6))


def test_fallback_venues_reports_primary_source():
    assert FallbackVenues(Static([V]), Static([])).find_with_source(VenueCategory.cafe, BOX) == (
        [V],
        "overpass",
    )


def test_fallback_venues_reports_snapshot_source():
    src = FallbackVenues(Static(error=AdapterError("down")), Static([V]))
    assert src.find_with_source(VenueCategory.cafe, BOX) == ([V], "snapshot")


def test_fallback_venues_uses_snapshot_on_empty_primary():
    src = FallbackVenues(Static([]), Static([V]))
    assert src.find_with_source(VenueCategory.cafe, BOX) == ([V], "snapshot")
