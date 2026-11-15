from __future__ import annotations

from typing import Any

import anthropic

from app.adapters.llm.base import LLMBadOutputError, LLMUnavailableError, ToolSpec

LLM_TIMEOUT_S = 20.0


class ClaudeClient:
    def __init__(self, api_key: str, model: str, sdk_client: Any = None):
        self.model = model
        self._sdk = sdk_client or anthropic.Anthropic(
            api_key=api_key, timeout=LLM_TIMEOUT_S, max_retries=1
        )

    def call_tool(self, system: str, user: str, tool: ToolSpec) -> dict:
        try:
            response = self._sdk.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0,
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=[
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.parameters,
                    }
                ],
                tool_choice={"type": "tool", "name": tool.name},
            )
        except anthropic.APIError as exc:
            raise LLMUnavailableError(f"Claude: {type(exc).__name__}") from exc
        for block in response.content:
            if getattr(block, "type", None) == "tool_use" and block.name == tool.name:
                return dict(block.input)
        raise LLMBadOutputError("Claude nie wywołał narzędzia.")
