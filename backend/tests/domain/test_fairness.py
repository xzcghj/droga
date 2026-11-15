from app.domain.fairness import rank
from app.domain.types import Point, TravelMode, TravelTime, Venue


def v(name: str) -> Venue:
    return Venue(name, f"node/{name}", Point(54.4, 18.6))


def t(*minutes: int) -> list[TravelTime]:
    return [TravelTime(i + 1, m, TravelMode.walk, "osrm") for i, m in enumerate(minutes)]


def test_rank_prefers_minimax_over_sum():
    # A: czasy 5 i 40 (suma 45, max 40); B: 22 i 24 (suma 46, max 24) → B wygrywa
    out = rank([(v("A"), t(5, 40)), (v("B"), t(22, 24))], limit=5)
    assert [c.venue.name for c in out] == ["B", "A"]
    assert out[0].max_minutes == 24 and out[0].total_minutes == 46


def test_rank_tie_broken_by_total_then_name():
    out = rank(
        [(v("C"), t(20, 10)), (v("B"), t(20, 5)), (v("A"), t(20, 5))],
        limit=5,
    )
    assert [c.venue.name for c in out] == ["A", "B", "C"]


def test_rank_spread_and_limit():
    out = rank([(v(str(i)), t(10 + i, 4)) for i in range(8)], limit=3)
    assert len(out) == 3
    assert out[0].spread_minutes == 6
    assert out[0].travel == t(10, 4)


def test_rank_all_zero_times():
    out = rank([(v("A"), t(0, 0))], limit=5)
    assert out[0].max_minutes == 0 and out[0].spread_minutes == 0 and out[0].total_minutes == 0


def test_rank_skips_candidates_without_travel():
    assert rank([(v("A"), [])], limit=5) == []
