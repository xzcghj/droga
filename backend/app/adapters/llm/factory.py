from __future__ import annotations

from app.adapters.llm.base import LLMClient
from app.config import Settings

# Sprawdzone 2026-11-15 w dokumentacji Google AI Studio: stabilny Flash-Lite z darmowym progiem.
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
DEFAULT_CLAUDE_MODEL = "claude-haiku-5-5"


def build_llm(settings: Settings) -> tuple[LLMClient | None, str | None]:
    """Zwraca (klient, nazwa dostawcy) albo (None, None), gdy AI jest wyłączone."""
    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        from app.adapters.llm.gemini import GeminiClient

        model = settings.llm_model or DEFAULT_GEMINI_MODEL
        return GeminiClient(settings.gemini_api_key, model), "gemini"
    if settings.llm_provider == "claude" and settings.anthropic_api_key:
        from app.adapters.llm.claude import ClaudeClient

        model = settings.llm_model or DEFAULT_CLAUDE_MODEL
        return ClaudeClient(settings.anthropic_api_key, model), "claude"
    return None, None
