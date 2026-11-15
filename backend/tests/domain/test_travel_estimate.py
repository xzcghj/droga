import pytest

from app.domain.travel_estimate import estimate_minutes, haversine_km, transit_minutes
from app.domain.types import Point, TravelMode
from tests.domain.helpers import km_apart

GDYNIA, GDANSK = Point(54.5203, 18.5302), Point(54.3520, 18.6466)


def test_haversine_gdynia_gdansk():
    assert 19.5 < haversine_km(GDYNIA, GDANSK) < 21.0


def test_walk_speed():
    # 1 km linii prostej → 1.3 km / 4.8 km/h = 16.25 min
    assert estimate_minutes(*km_apart(1.0), TravelMode.walk) == pytest.approx(16.25, abs=0.2)


def test_bike_and_car_speeds():
    a, b = km_apart(1.0)
    assert estimate_minutes(a, b, TravelMode.bike) == pytest.approx(5.2, abs=0.1)
    assert estimate_minutes(a, b, TravelMode.car) == pytest.approx(2.6, abs=0.1)


def test_transit_never_slower_than_walk():
    a, b = km_apart(0.3)
    assert transit_minutes(a, b) == pytest.approx(estimate_minutes(a, b, TravelMode.walk))


def test_transit_long_distance():
    a, b = km_apart(20.0)
    assert transit_minutes(a, b) == pytest.approx(10 + 28 / 22 * 60, abs=0.3)
    assert estimate_minutes(a, b, TravelMode.transit) == pytest.approx(transit_minutes(a, b))


def test_same_point_is_zero_minutes():
    p = Point(54.4, 18.6)
    for mode in TravelMode:
        assert estimate_minutes(p, p, mode) == 0
