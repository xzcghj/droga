from __future__ import annotations

from fastapi import APIRouter, Depends

from app.adapters.http import AdapterError
from app.api.deps import get_container
from app.api.errors import AppError
from app.api.schemas import GeocodeMatch, GeocodeRequest, GeocodeResponse
from app.container import Container

router = APIRouter(tags=["geocode"])


@router.post("/geocode", response_model=GeocodeResponse)
def geocode(data: GeocodeRequest, container: Container = Depends(get_container)):
    try:
        results = container.geocoder.search(data.query, limit=5)
    except AdapterError as exc:
        raise AppError(
            503,
            "geocoding_unavailable",
            "Usługa wyszukiwania adresów jest chwilowo niedostępna. Spróbuj za chwilę.",
        ) from exc
    return GeocodeResponse(
        results=[GeocodeMatch(label=r.label, lat=r.point.lat, lon=r.point.lon) for r in results]
    )
