"""Jednorazowo buduje snapshot lokali Trójmiasta z Overpass API.

Uruchom z katalogu backend:  python scripts/build_venue_snapshot.py
Dane: © OpenStreetMap contributors, licencja ODbL.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.adapters.http import AdapterError, request_json  # noqa: E402
from app.adapters.venues import CATEGORY_TAGS  # noqa: E402
from app.config import Settings  # noqa: E402
from app.domain.types import VenueCategory  # noqa: E402

BOX = "54.30,18.40,54.60,18.80"
PER_CATEGORY = 40
OUT = Path(__file__).resolve().parents[1] / "data" / "venues_trojmiasto.json"
ATTRIBUTION = "© OpenStreetMap contributors, ODbL"


def fetch(client: httpx.Client, urls: list[str], category: VenueCategory) -> list[dict]:
    parts = "".join(f'nwr["{k}"="{v}"]["name"]({BOX});' for k, v in CATEGORY_TAGS[category])
    query = f"[out:json][timeout:60];({parts});out center tags;"
    for url in urls:
        try:
            return request_json(client, "POST", url, data={"data": query})["elements"]
        except (AdapterError, KeyError):
            continue
    raise SystemExit(f"Overpass niedostępny dla kategorii {category} — plik nie został zmieniony.")


def main() -> None:
    settings = Settings()
    rows: list[dict] = []
    with httpx.Client(timeout=90, headers={"User-Agent": settings.osm_user_agent}) as client:
        for category in VenueCategory:
            elements = fetch(client, settings.overpass_urls, category)
            # Najpierw obiekty z website/opening_hours — zwykle lepiej opisane i aktywne.
            elements.sort(
                key=lambda e: -sum(k in e.get("tags", {}) for k in ("website", "opening_hours"))
            )
            picked = 0
            for el in elements:
                src = el if "lat" in el else el.get("center")
                name = el.get("tags", {}).get("name")
                if not src or not name:
                    continue
                rows.append(
                    {
                        "name": name,
                        "osm_id": f"{el['type']}/{el['id']}",
                        "lat": round(src["lat"], 6),
                        "lon": round(src["lon"], 6),
                        "category": category.value,
                    }
                )
                picked += 1
                if picked >= PER_CATEGORY:
                    break
            print(f"{category}: {picked}")
            time.sleep(2)  # uprzejmie dla publicznego serwera
    OUT.write_text(
        json.dumps({"attribution": ATTRIBUTION, "venues": rows}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"Zapisano {len(rows)} lokali do {OUT}")


if __name__ == "__main__":
    main()
