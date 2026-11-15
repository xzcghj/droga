import httpx
import pytest

from app.adapters.geocoding import NominatimGeocoder
from app.adapters.http import AdapterError
from app.adapters.throttle import RateLimiter
from app.domain.types import Point

UA = "pol-drogi-test/1.0 (test@example.com)"


def make(handler):
    calls: list[httpx.Request] = []

    def wrapped(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    client = httpx.Client(transport=httpx.MockTransport(wrapped))
    geo = NominatimGeocoder(client, "https://nominatim.test", UA, RateLimiter(0))
    return geo, calls


def ok(_request):
    return httpx.Response(
        200,
        json=[{"display_name": "Wrzeszcz, Gdańsk", "lat": "54.3797", "lon": "18.6070"}],
    )


def test_geocode_sends_policy_params_and_user_agent():
    geo, calls = make(ok)
    geo.search("Wrzeszcz")
    req = calls[0]
    assert req.url.path == "/search"
    assert req.headers["user-agent"] == UA
    params = req.url.params
    assert params["countrycodes"] == "pl"
    assert params["viewbox"] == "18.40,54.60,18.80,54.30"
    assert params["bounded"] == "0"
    assert params["format"] == "jsonv2"
    assert params["limit"] == "5"


def test_geocode_query_keeps_polish_characters():
    geo, calls = make(ok)
    geo.search("Gdańsk Wrzeszcz, Łąkowa 5")
    assert calls[0].url.params["q"] == "Gdańsk Wrzeszcz, Łąkowa 5"


def test_geocode_maps_results():
    geo, _ = make(ok)
    [res] = geo.search("Wrzeszcz")
    assert res.label == "Wrzeszcz, Gdańsk"
    assert res.point == Point(54.3797, 18.6070)


def test_geocode_http_error_raises_adapter_error_without_retry():
    geo, calls = make(lambda r: httpx.Response(503))
    with pytest.raises(AdapterError):
        geo.search("Wrzeszcz")
    assert len(calls) == 1


def test_geocode_bad_json_raises_adapter_error():
    geo, _ = make(lambda r: httpx.Response(200, text="<html>"))
    with pytest.raises(AdapterError):
        geo.search("Wrzeszcz")


def test_rate_limiter_spaces_calls_by_one_second():
    now = [100.0]
    slept: list[float] = []

    def sleep(s: float) -> None:
        slept.append(s)
        now[0] += s

    limiter = RateLimiter(1.0, clock=lambda: now[0], sleep=sleep)
    limiter.wait()
    now[0] += 0.25
    limiter.wait()
    assert slept == [pytest.approx(0.75)]
