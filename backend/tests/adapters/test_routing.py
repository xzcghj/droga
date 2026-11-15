import httpx
import pytest

from app.adapters.http import AdapterError
from app.adapters.routing import HaversineRouter, OsrmRouter
from app.domain.travel_estimate import estimate_minutes
from app.domain.types import Point, TravelMode

A, B, C = Point(54.52, 18.53), Point(54.41, 18.56), Point(54.38, 18.60)


def router_with(handler):
    calls = []

    def wrapped(request):
        calls.append(request)
        return handler(request)

    return OsrmRouter(
        httpx.Client(transport=httpx.MockTransport(wrapped)), "https://osrm.test"
    ), calls


def ok(durations):
    return lambda r: httpx.Response(200, json={"code": "Ok", "durations": durations})


def test_osrm_builds_foss_gis_url_with_lon_lat_order():
    router, calls = router_with(ok([[600.0, 1200.0]]))
    router.matrix("bike", [A], [B, C])
    url = calls[0].url
    assert url.path == "/routed-bike/table/v1/driving/18.53,54.52;18.56,54.41;18.6,54.38"
    assert url.params["sources"] == "0"
    assert url.params["destinations"] == "1;2"
    assert url.params["annotations"] == "duration"


@pytest.mark.parametrize("profile,prefix", [("walk", "routed-foot"), ("car", "routed-car")])
def test_osrm_profile_prefixes(profile, prefix):
    router, calls = router_with(ok([[60.0]]))
    router.matrix(profile, [A], [B])
    assert calls[0].url.path.startswith(f"/{prefix}/")


def test_osrm_converts_seconds_to_minutes_and_keeps_none():
    router, _ = router_with(ok([[600.0, None], [90.0, 30.0]]))
    assert router.matrix("car", [A, B], [B, C]) == [[10.0, None], [1.5, 0.5]]


def test_osrm_non_ok_code_raises():
    router, _ = router_with(lambda r: httpx.Response(200, json={"code": "NoTable"}))
    with pytest.raises(AdapterError):
        router.matrix("car", [A], [B])


def test_osrm_wrong_shape_raises():
    router, _ = router_with(ok([[60.0]]))
    with pytest.raises(AdapterError):
        router.matrix("car", [A], [B, C])


def test_haversine_router_matches_estimate():
    m = HaversineRouter().matrix("bike", [A, B], [C])
    assert m == [
        [pytest.approx(estimate_minutes(A, C, TravelMode.bike))],
        [pytest.approx(estimate_minutes(B, C, TravelMode.bike))],
    ]
