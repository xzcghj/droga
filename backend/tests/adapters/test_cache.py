from app.adapters.cache import TTLCache


def test_ttl_cache_hit_and_expiry():
    now = [0.0]
    cache = TTLCache(600, clock=lambda: now[0])
    cache.set("k", 1)
    now[0] = 599.9
    assert cache.get("k") == 1
    now[0] = 600.1
    assert cache.get("k") is None


def test_ttl_cache_miss():
    assert TTLCache(10).get("nope") is None
