import httpx
import pytest

from app.adapters.http import AdapterError, request_json


def test_request_json_retries_once_on_5xx_then_succeeds():
    responses = iter([httpx.Response(502), httpx.Response(200, json={"ok": 1})])
    client = httpx.Client(transport=httpx.MockTransport(lambda r: next(responses)))
    assert request_json(client, "GET", "https://x.test/") == {"ok": 1}


def test_request_json_raises_after_retry_on_429():
    calls = []

    def handler(r):
        calls.append(r)
        return httpx.Response(429)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(AdapterError):
        request_json(client, "GET", "https://x.test/")
    assert len(calls) == 2


def test_request_json_no_retry_on_4xx():
    calls = []

    def handler(r):
        calls.append(r)
        return httpx.Response(400)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(AdapterError):
        request_json(client, "GET", "https://x.test/")
    assert len(calls) == 1


def test_request_json_network_error_is_adapter_error():
    def handler(r):
        raise httpx.ConnectError("down")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(AdapterError):
        request_json(client, "GET", "https://x.test/", retries=0)


def test_request_json_does_not_retry_timeouts():
    calls = []

    def handler(r):
        calls.append(r)
        raise httpx.ReadTimeout("slow")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(AdapterError):
        request_json(client, "GET", "https://x.test/")
    assert len(calls) == 1
