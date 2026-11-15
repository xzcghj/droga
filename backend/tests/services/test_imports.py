import pytest
from sqlmodel import select

from app.adapters.llm.base import LLMBadOutputError, LLMUnavailableError
from app.api.errors import AppError
from app.db.models import Participant
from app.services.imports import PARSE_SYSTEM_PROMPT, PARSE_TOOL, ImportService
from tests.fakes import FakeGeocoder, FakeLLM


def row(name, where, mode=None, note=None):
    return {"name": name, "start_location_text": where, "mode": mode, "note": note}


def service(result=None, error=None, geocoder=None):
    llm = FakeLLM(result=result, error=error)
    return ImportService(llm, geocoder or FakeGeocoder()), llm


def test_parse_returns_geocoded_draft():
    svc, llm = service({"participants": [row("Ola", "Gdynia", "transit")], "unparsed": []})
    draft = svc.parse("Ola z Gdyni SKM-ką")
    [p] = draft.participants
    assert (p.name, p.start_label, p.mode, p.geocode_error) == ("Ola", "Gdynia", "transit", False)
    assert (p.lat, p.lon) == (54.3797, 18.6070)
    assert llm.calls[0]["user"] == "Ola z Gdyni SKM-ką"
    assert llm.calls[0]["tool"] is PARSE_TOOL


def test_parse_keeps_null_mode():
    svc, _ = service({"participants": [row("Kuba", "Oliwa")], "unparsed": []})
    assert svc.parse("Kuba z Oliwy").participants[0].mode is None


def test_parse_marks_geocode_error_per_row():
    geo = FakeGeocoder()
    geo.missing.add("Atlantyda")
    svc, _ = service(
        {"participants": [row("A", "Atlantyda", "walk"), row("B", "Sopot", "car")], "unparsed": []},
        geocoder=geo,
    )
    a, b = svc.parse("...").participants
    assert a.geocode_error and a.lat is None and a.lon is None
    assert not b.geocode_error and b.lat is not None


def test_parse_geocoder_down_marks_rows_instead_of_failing():
    geo = FakeGeocoder()
    geo.fail = True
    svc, _ = service({"participants": [row("A", "Sopot", "walk")], "unparsed": []}, geocoder=geo)
    assert svc.parse("...").participants[0].geocode_error


def test_parse_empty_result_is_valid_draft():
    svc, _ = service({"participants": [], "unparsed": ["haha 😂"]})
    draft = svc.parse("haha 😂")
    assert draft.participants == [] and draft.unparsed == ["haha 😂"]


def test_parse_missing_unparsed_defaults_to_empty():
    svc, _ = service({"participants": []})
    assert svc.parse("x").unparsed == []


def test_parse_truncates_to_ten():
    people = [row(f"P{i}", "Sopot", "walk") for i in range(13)]
    svc, _ = service({"participants": people, "unparsed": ["?"]})
    draft = svc.parse("...")
    assert len(draft.participants) == 10
    assert draft.unparsed == ["?", "Pominięto 3 osoby — limit to 10."]


def test_parse_invalid_llm_output_502():
    svc, _ = service({"participants": [row("A", "Sopot", "rakieta")], "unparsed": []})
    with pytest.raises(AppError) as e:
        svc.parse("...")
    assert e.value.status == 502 and e.value.code == "ai_bad_output"


def test_parse_bad_output_error_502():
    svc, _ = service(error=LLMBadOutputError("brak narzędzia"))
    with pytest.raises(AppError) as e:
        svc.parse("...")
    assert e.value.status == 502


def test_parse_llm_unavailable_503():
    svc, _ = service(error=LLMUnavailableError("429"))
    with pytest.raises(AppError) as e:
        svc.parse("...")
    assert e.value.status == 503 and e.value.code == "ai_unavailable"


def test_prompt_contains_rules():
    for needle in ["SKM", "Mevo", "null", "Ja", "dane", "nie wymyślaj"]:
        assert needle in PARSE_SYSTEM_PROMPT
    schema = PARSE_TOOL.parameters
    mode = schema["properties"]["participants"]["items"]["properties"]["mode"]
    assert set(mode["enum"]) == {"walk", "bike", "transit", "car", None}


# --- API -----------------------------------------------------------------------


def test_parse_without_llm_503(client):
    r = client.post("/api/v1/ai/parse-participants", json={"text": "Ola z Gdyni"})
    assert r.status_code == 503 and r.json()["error"]["code"] == "ai_unavailable"


def test_parse_text_too_long_422(client):
    r = client.post("/api/v1/ai/parse-participants", json={"text": "x" * 2001})
    assert r.status_code == 422


def test_parse_endpoint_returns_draft(client_factory):
    llm = FakeLLM({"participants": [row("Łukasz", "Gdańsk Wrzeszcz", "bike")], "unparsed": []})
    client = client_factory(llm=llm, provider="gemini")
    r = client.post("/api/v1/ai/parse-participants", json={"text": "Łukasz z Wrzeszcza rowerem"})
    assert r.status_code == 200, r.text
    [p] = r.json()["participants"]
    assert p["name"] == "Łukasz" and p["start_label"] == "Gdańsk Wrzeszcz" and p["mode"] == "bike"
    assert set(p) == {"name", "start_label", "mode", "note", "lat", "lon", "geocode_error"}


def test_parse_does_not_write_to_db(client_factory):
    from sqlmodel import Session

    llm = FakeLLM({"participants": [row("Ola", "Gdynia", "transit")], "unparsed": []})
    client = client_factory(llm=llm, provider="gemini")
    client.post(
        "/api/v1/meetups",
        json={"title": "K", "scheduled_at": "2026-11-21T18:00:00+01:00", "venue_category": "cafe"},
    )
    client.post("/api/v1/ai/parse-participants", json={"text": "Ola z Gdyni"})
    with Session(client.app.state.engine) as s:
        assert s.exec(select(Participant)).all() == []
