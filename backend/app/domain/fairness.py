"""Metryka sprawiedliwości: minimax z rozstrzyganiem remisów sumą, potem nazwą."""

from __future__ import annotations

from app.domain.types import RankedCandidate, TravelTime, Venue


def rank(candidates: list[tuple[Venue, list[TravelTime]]], limit: int) -> list[RankedCandidate]:
    ranked: list[RankedCandidate] = []
    for venue, travel in candidates:
        if not travel:
            continue
        minutes = [t.minutes for t in travel]
        ranked.append(
            RankedCandidate(
                venue=venue,
                travel=list(travel),
                max_minutes=max(minutes),
                total_minutes=sum(minutes),
                spread_minutes=max(minutes) - min(minutes),
            )
        )
    ranked.sort(key=lambda c: (c.max_minutes, c.total_minutes, c.venue.name))
    return ranked[:limit]
