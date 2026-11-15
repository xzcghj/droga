from app.domain.types import Point

KM_PER_DEG_LAT = 111.32


def km_apart(d: float, lat: float = 54.4, lon: float = 18.6) -> tuple[Point, Point]:
    """Dwa punkty na tym samym południku odległe o `d` km."""
    return Point(lat, lon), Point(lat + d / KM_PER_DEG_LAT, lon)
