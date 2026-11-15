from datetime import UTC, datetime

from app.domain.schedule import departure_time, format_pl_datetime, to_warsaw


def test_departure_rounds_down_to_5_minutes():
    # 18:00 − 17 − 5 = 17:38 → 17:35
    got = departure_time(datetime(2026, 11, 21, 17, 0, tzinfo=UTC), 17)
    assert got == datetime(2026, 11, 21, 16, 35, tzinfo=UTC)


def test_departure_exact_multiple_unchanged():
    got = departure_time(datetime(2026, 11, 21, 17, 0, tzinfo=UTC), 25)
    assert got == datetime(2026, 11, 21, 16, 30, tzinfo=UTC)


def test_departure_drops_seconds():
    got = departure_time(datetime(2026, 11, 21, 17, 0, 30, tzinfo=UTC), 0)
    assert got == datetime(2026, 11, 21, 16, 55, tzinfo=UTC)


def test_warsaw_conversion_winter_and_summer():
    assert to_warsaw(datetime(2026, 11, 21, 17, 0, tzinfo=UTC)).strftime("%H:%M") == "18:00"
    assert to_warsaw(datetime(2026, 7, 11, 16, 0, tzinfo=UTC)).strftime("%H:%M") == "18:00"


def test_format_pl_datetime():
    assert format_pl_datetime(datetime(2026, 11, 21, 17, 0, tzinfo=UTC)) == (
        "sobota, 21 listopada, 18:00"
    )
