import math

import pytest

from app.domain.candidates import prefilter, search_bbox
from app.domain.types import ParticipantPoint, Point, TravelMode, Venue

KM_LAT = 111.32


def test_search_bbox_expands_by_15_percent():
    # rozpiętość 20 km (N–S) → +3 km z każdej strony
    a, b = Point(54.30, 18.60), Point(54.30 + 20 / KM_LAT, 18.60)
    box = search_bbox([a, b])
    assert (a.lat - box.south) * KM_LAT == pytest.approx(3.0, abs=0.01)
    assert (box.north - b.lat) * KM_LAT == pytest.approx(3.0, abs=0.01)
    lon_km = KM_LAT * math.cos(math.radians((a.lat + b.lat) / 2))
    assert (a.lon - box.west) * lon_km == pytest.approx(3.0, abs=0.01)


def test_search_bbox_degenerate_points_expands_by_1km():
    p = Point(54.4, 18.6)
    box = search_bbox([p, p])
    lon_km = KM_LAT * math.cos(math.radians(54.4))
    assert (box.north - box.south) * KM_LAT == pytest.approx(2.0, abs=0.01)
    assert (box.east - box.west) * lon_km == pytest.approx(2.0, abs=0.01)


def test_prefilter_keeps_closest_by_max_time():
    people = [
        ParticipantPoint(1, Point(54.40, 18.60), TravelMode.walk),
        ParticipantPoint(2, Point(54.42, 18.60), TravelMode.car),
    ]
    venues = [Venue(f"V{i}", f"node/{i}", Point(54.41 + i * 0.002, 18.60)) for i in range(30)]
    kept = prefilter(venues, people, keep=25)
    assert len(kept) == 25
    assert venues[29] not in kept
    assert venues[0] in kept


def test_prefilter_fewer_than_keep_returns_all():
    people = [ParticipantPoint(1, Point(54.4, 18.6), TravelMode.walk)]
    venues = [Venue("A", "node/1", Point(54.41, 18.6))]
    assert prefilter(venues, people) == venues
