from app.adapters.routing import HaversineRouter, OsrmRouter
from app.adapters.venues import FallbackVenues
from app.config import Settings
from app.container import SNAPSHOT_PATH, build_container


def test_build_container_wires_real_adapters():
    c = build_container(Settings(_env_file=None, llm_provider="none"))
    assert set(c.routers) == {"walk", "bike", "car"}
    assert all(isinstance(r, OsrmRouter) for r in c.routers.values())
    assert isinstance(c.fallback_router, HaversineRouter)
    assert isinstance(c.venues, FallbackVenues)
    assert SNAPSHOT_PATH.exists()


def test_shared_http_client_identifies_app_to_osm_services():
    s = Settings(_env_file=None, llm_provider="none", osm_user_agent="pol-drogi/1.0 (ja@x.pl)")
    c = build_container(s)
    for client in (c.venues.primary.client, c.routers["car"].client, c.geocoder.client):
        assert client.headers["User-Agent"] == "pol-drogi/1.0 (ja@x.pl)"
        assert client.headers["Referer"].startswith("https://github.com/")


def test_settings_read_root_env_when_run_from_backend(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("OSM_USER_AGENT=z-glownego (a@b.pl)\n", encoding="utf-8")
    backend = tmp_path / "backend"
    backend.mkdir()
    monkeypatch.chdir(backend)
    monkeypatch.delenv("OSM_USER_AGENT", raising=False)
    assert Settings().osm_user_agent == "z-glownego (a@b.pl)"
