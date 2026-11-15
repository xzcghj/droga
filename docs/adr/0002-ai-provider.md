# ADR-002: Dostawca AI — Gemini (darmowy próg) domyślnie, Claude opcjonalnie, za interfejsem `LLMClient`

- **Status:** zaakceptowana
- **Data:** 2026-11-15

## Kontekst
Funkcje AI (import uczestników z czatu, redakcja zaproszenia) mają działać za darmo, także podczas nagrywania demo. Aplikacja musi działać również bez żadnego klucza.

## Decyzja
`LLMClient.call_tool(system, user, tool)` z dwiema implementacjami:
- `GeminiClient` (domyślnie, model `gemini-3.5-flash-lite` z darmowego progu Google AI Studio),
- `ClaudeClient` (opcjonalnie; Claude API wymaga przedpłaconych kredytów).

Obie wymuszają wywołanie jednego narzędzia (Gemini: function calling w trybie `ANY`; Claude: `tool_choice`), a wynik zawsze przechodzi walidację Pydantic. Brak klucza ⇒ `LLM_PROVIDER` efektywnie `none`.

## Konsekwencje
- Abstrakcja i tak była potrzebna (testy na atrapach, tryb bez AI), więc druga implementacja kosztuje mało.
- Na darmowym progu Gemini dane mogą być użyte przez Google do ulepszania usług — w demie używamy tylko przykładowych adresów.
