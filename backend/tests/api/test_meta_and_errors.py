def test_meta_without_llm(client):
    r = client.get("/api/v1/meta")
    assert r.status_code == 200
    assert r.json() == {"ai_enabled": False, "ai_provider": None}


def test_meta_with_llm(client_factory, fake_llm):
    client = client_factory(llm=fake_llm, provider="gemini")
    assert client.get("/api/v1/meta").json() == {"ai_enabled": True, "ai_provider": "gemini"}


def test_unknown_route_uses_error_format(client):
    r = client.get("/api/v1/nope")
    assert r.status_code == 404
    assert set(r.json()["error"]) == {"code", "message", "details"}


def test_cors_allows_configured_origin(client):
    r = client.options(
        "/api/v1/meta",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_other_origin(client):
    r = client.options(
        "/api/v1/meta",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in r.headers


def test_settings_parse_comma_separated_cors_and_blank_keys(monkeypatch):
    from app.config import Settings

    monkeypatch.setenv("CORS_ORIGINS", "http://a.example, http://b.example")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("LLM_MODEL", "")
    s = Settings(_env_file=None)
    assert s.cors_origins == ["http://a.example", "http://b.example"]
    assert s.gemini_api_key is None
    assert s.llm_model is None
