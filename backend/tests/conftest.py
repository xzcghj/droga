from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import Settings
from app.container import Container
from app.main import create_app
from tests.fakes import FakeGeocoder, FakeLLM


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        _env_file=None,
        llm_provider="none",
        database_url="sqlite://",
        cors_origins=["http://localhost:5173"],
        seed_demo=False,
    )


def make_container(**overrides) -> Container:
    provider = overrides.pop("provider", None)
    c = Container(
        geocoder=FakeGeocoder(),
        routers={},
        fallback_router=None,
        venues=None,
        llm=None,
        ai_provider=provider,
        suggestion_cache=None,
    )
    for key, value in overrides.items():
        setattr(c, key, value)
    return c


@pytest.fixture
def fake_geocoder() -> FakeGeocoder:
    return FakeGeocoder()


@pytest.fixture
def container(fake_geocoder) -> Container:
    return make_container(geocoder=fake_geocoder)


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def client_factory(test_settings):
    clients: list[TestClient] = []

    def factory(**overrides) -> TestClient:
        c = TestClient(create_app(test_settings, make_container(**overrides)))
        c.__enter__()
        clients.append(c)
        return c

    yield factory
    for c in clients:
        c.__exit__(None, None, None)


@pytest.fixture
def client(test_settings, container):
    with TestClient(create_app(test_settings, container)) as c:
        yield c


@pytest.fixture
def session(client):
    with Session(client.app.state.engine) as s:
        yield s
