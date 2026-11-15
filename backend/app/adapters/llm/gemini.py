from __future__ import annotations

from typing import Any

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.adapters.llm.base import LLMBadOutputError, LLMUnavailableError, ToolSpec

LLM_TIMEOUT_MS = 20_000


class GeminiClient:
    def __init__(self, api_key: str, model: str, sdk_client: Any = None):
        self.model = model
        self._sdk = sdk_client or genai.Client(
            api_key=api_key, http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS)
        )

    def call_tool(self, system: str, user: str, tool: ToolSpec) -> dict:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0,
            tools=[
                types.Tool(
                    function_declarations=[
                        types.FunctionDeclaration(
                            name=tool.name,
                            description=tool.description,
                            parameters_json_schema=tool.parameters,
                        )
                    ]
                )
            ],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="ANY", allowed_function_names=[tool.name]
                )
            ),
        )
        try:
            response = self._sdk.models.generate_content(
                model=self.model, contents=user, config=config
            )
        except genai_errors.APIError as exc:
            raise LLMUnavailableError(f"Gemini: HTTP {exc.code}") from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailableError(f"Gemini: {exc}") from exc
        calls = [c for c in (response.function_calls or []) if c.name == tool.name]
        if not calls or calls[0].args is None:
            raise LLMBadOutputError("Gemini nie wywołał narzędzia.")
        return dict(calls[0].args)
