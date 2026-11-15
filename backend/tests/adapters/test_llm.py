from types import SimpleNamespace

import anthropic
import httpx
import pytest
from google.genai import errors as genai_errors

from app.adapters.llm.base import LLMBadOutputError, LLMUnavailableError, ToolSpec
from app.adapters.llm.claude import ClaudeClient
from app.adapters.llm.factory import DEFAULT_CLAUDE_MODEL, DEFAULT_GEMINI_MODEL, build_llm
from app.adapters.llm.gemini import GeminiClient
from app.config import Settings

TOOL = ToolSpec(
    name="submit_x",
    description="Zwróć x.",
    parameters={"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]},
)


def settings(**kw) -> Settings:
    return Settings(_env_file=None, **kw)


# --- fabryka -----------------------------------------------------------------


def test_factory_none_when_no_key():
    assert build_llm(settings(llm_provider="gemini")) == (None, None)
    assert build_llm(settings(llm_provider="claude", gemini_api_key="g")) == (None, None)


def test_factory_none_when_provider_none():
    assert build_llm(settings(llm_provider="none", gemini_api_key="g")) == (None, None)


def test_factory_selects_gemini_by_default_model():
    llm, provider = build_llm(settings(gemini_api_key="g"))
    assert provider == "gemini" and isinstance(llm, GeminiClient)
    assert llm.model == DEFAULT_GEMINI_MODEL == "gemini-3.5-flash-lite"


def test_factory_selects_claude_when_configured():
    llm, provider = build_llm(settings(llm_provider="claude", anthropic_api_key="a"))
    assert provider == "claude" and isinstance(llm, ClaudeClient)
    assert llm.model == DEFAULT_CLAUDE_MODEL == "claude-haiku-5-5"


def test_factory_uses_model_override():
    llm, _ = build_llm(settings(gemini_api_key="g", llm_model="gemini-3.6-flash"))
    assert llm.model == "gemini-3.6-flash"


# --- Gemini --------------------------------------------------------------------


class FakeGeminiModels:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.kwargs = response, error, None

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.response


def gemini(response=None, error=None):
    models = FakeGeminiModels(response, error)
    return GeminiClient("key", "gemini-test", sdk_client=SimpleNamespace(models=models)), models


def test_gemini_forces_tool_and_returns_args():
    resp = SimpleNamespace(function_calls=[SimpleNamespace(name="submit_x", args={"x": 3})])
    client, models = gemini(resp)
    assert client.call_tool("system!", "user text", TOOL) == {"x": 3}
    kw = models.kwargs
    assert kw["model"] == "gemini-test" and kw["contents"] == "user text"
    cfg = kw["config"]
    assert cfg.system_instruction == "system!"
    assert cfg.temperature == 0
    fcc = cfg.tool_config.function_calling_config
    assert fcc.mode == "ANY" and fcc.allowed_function_names == ["submit_x"]
    decl = cfg.tools[0].function_declarations[0]
    assert decl.name == "submit_x" and decl.parameters_json_schema == TOOL.parameters


def test_gemini_without_function_call_raises_bad_output():
    client, _ = gemini(SimpleNamespace(function_calls=None))
    with pytest.raises(LLMBadOutputError):
        client.call_tool("s", "u", TOOL)


def test_sdk_rate_limit_maps_to_unavailable():
    client, _ = gemini(error=genai_errors.ClientError(429, {"error": {"message": "quota"}}))
    with pytest.raises(LLMUnavailableError):
        client.call_tool("s", "u", TOOL)


def test_gemini_network_error_maps_to_unavailable():
    client, _ = gemini(error=httpx.ConnectError("down"))
    with pytest.raises(LLMUnavailableError):
        client.call_tool("s", "u", TOOL)


# --- Claude --------------------------------------------------------------------


class FakeClaudeMessages:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.kwargs = response, error, None

    def create(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.response


def claude(response=None, error=None):
    messages = FakeClaudeMessages(response, error)
    return ClaudeClient(
        "key", "claude-test", sdk_client=SimpleNamespace(messages=messages)
    ), messages


def test_claude_forces_tool_and_returns_input():
    resp = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="ok"),
            SimpleNamespace(type="tool_use", name="submit_x", input={"x": 5}),
        ]
    )
    client, messages = claude(resp)
    assert client.call_tool("sys", "usr", TOOL) == {"x": 5}
    kw = messages.kwargs
    assert kw["model"] == "claude-test" and kw["system"] == "sys" and kw["temperature"] == 0
    assert kw["tool_choice"] == {"type": "tool", "name": "submit_x"}
    assert kw["tools"] == [
        {"name": "submit_x", "description": "Zwróć x.", "input_schema": TOOL.parameters}
    ]
    assert kw["messages"] == [{"role": "user", "content": "usr"}]


def test_claude_without_tool_use_raises_bad_output():
    client, _ = claude(SimpleNamespace(content=[SimpleNamespace(type="text", text="nie")]))
    with pytest.raises(LLMBadOutputError):
        client.call_tool("s", "u", TOOL)


def test_claude_rate_limit_maps_to_unavailable():
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    err = anthropic.RateLimitError("429", response=httpx.Response(429, request=req), body=None)
    client, _ = claude(error=err)
    with pytest.raises(LLMUnavailableError):
        client.call_tool("s", "u", TOOL)


# --- kontener / meta -----------------------------------------------------------


def test_container_takes_provider_from_factory():
    from app.container import build_container

    c = build_container(settings(gemini_api_key="g"))
    assert c.ai_provider == "gemini" and isinstance(c.llm, GeminiClient)
    c = build_container(settings(llm_provider="gemini"))
    assert c.ai_provider is None and c.llm is None


def test_sdk_clients_are_built_with_timeouts(monkeypatch):
    import app.adapters.llm.claude as claude_mod
    import app.adapters.llm.gemini as gemini_mod

    seen = {}
    monkeypatch.setattr(gemini_mod.genai, "Client", lambda **kw: seen.setdefault("gemini", kw))
    monkeypatch.setattr(
        claude_mod.anthropic, "Anthropic", lambda **kw: seen.setdefault("claude", kw)
    )
    GeminiClient("k", "m")
    ClaudeClient("k", "m")
    assert 0 < seen["gemini"]["http_options"].timeout <= 30_000  # ms
    assert 0 < seen["claude"]["timeout"] <= 30 and seen["claude"]["max_retries"] <= 1
