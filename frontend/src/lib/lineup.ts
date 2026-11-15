import type { MeetupRead } from "../api/client";

/** Podpis składu grupy: osoby, ich środki transportu, punkty startu i kategoria lokalu.
 *  Ranking w cache jest przypisany do podpisu, więc po zmianie składu nie da się pokazać
 *  rankingu liczonego dla starego składu. */
export function lineupKey(m: MeetupRead): string {
  return (
    m.participants.map((p) => `${p.id}:${p.mode}:${p.lat}:${p.lon}`).join("|") +
    `#${m.venue_category}`
  );
}
