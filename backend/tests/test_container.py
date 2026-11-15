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
