# ADR-004: Endpointy synchroniczne

- **Status:** zaakceptowana
- **Data:** 2026-11-15

## Kontekst
FastAPI pozwala pisać endpointy `async def` albo `def`.

## Decyzja
Endpointy synchroniczne (`def`). Limity usług zewnętrznych (Nominatim 1 zapytanie/s, uprzejme sekwencyjne zapytania do OSRM) wymuszają zapytania sekwencyjne, więc `async` nie przyspieszy obliczeń, a mieszałby się z synchronicznym SQLite/SQLModel. FastAPI wykonuje `def` w puli wątków; współdzielone elementy (limiter, cache) są wątkowo bezpieczne.

## Konsekwencje
Prostszy kod i testy; przepustowość ograniczona pulą wątków — wystarczająca dla MVP.
