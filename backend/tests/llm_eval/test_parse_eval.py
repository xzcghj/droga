"""Ewaluacja promptu importu na prawdziwym modelu.

Uruchom:  pytest -m llm   (wymaga GEMINI_API_KEY lub ANTHROPIC_API_KEY w .env)
Porównujemy imiona i środki transportu; geokoder to atrapa.
"""

import json
from pathlib import Path

import pytest

from app.adapters.llm.factory import build_llm
from app.config import Settings
from app.services.imports import ImportService
from tests.fakes import FakeGeocoder

CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def llm():
    client, _ = build_llm(Settings())
    if client is None:
        pytest.skip("Brak klucza API — ewaluacja AI pominięta.")
    return client


@pytest.mark.llm
@pytest.mark.parametrize("case", CASES, ids=[c["text"][:30] for c in CASES])
def test_parse_eval(llm, case):
    draft = ImportService(llm, FakeGeocoder()).parse(case["text"])
    got = sorted((p.name, p.mode.value if p.mode else None) for p in draft.participants)
    want = sorted((e["name"], e["mode"]) for e in case["expected"])
    assert got == want, f"unparsed={draft.unparsed}"
