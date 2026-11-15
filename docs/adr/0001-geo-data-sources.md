# ADR-001: Źródło danych geograficznych — publiczne usługi OSM z łańcuchem fallbacków

- **Status:** zaakceptowana
- **Data:** 2026-11-15

## Kontekst
Aplikacja potrzebuje geokodowania adresów, macierzy czasów przejazdu i listy lokali. Rekruter ma uruchomić projekt bez kluczy i bez karty płatniczej.

## Rozważane opcje
1. Tylko snapshot offline — zero zależności, ale wyniki nierealistyczne (brak prawdziwych tras).
2. Płatne API Google Maps / Mapbox — świetna jakość, ale wymaga klucza i karty u osoby uruchamiającej.
3. Publiczne usługi OSM (Nominatim, OSRM FOSSGIS, Overpass) z fallbackami.

## Decyzja
Opcja 3. Każda usługa stoi za interfejsem (`Geocoder`, `Router`, `VenueSource`); fallbacki to inne implementacje tego samego interfejsu: `HaversineRouter` zamiast OSRM, `SnapshotVenues` zamiast Overpass.

## Konsekwencje
- Zero konfiguracji i prawdziwe wyniki.
- Trzeba przestrzegać zasad usług: globalny limiter 1 zapytanie/s dla Nominatim, `User-Agent`, brak autouzupełniania, sekwencyjne zapytania do OSRM.
- Kod fallbacków i uczciwe oznaczanie szacunków w UI („≈”).
- Nadaje się do demo, nie do ruchu produkcyjnego (wtedy własny OSRM/Nominatim lub płatny dostawca).
