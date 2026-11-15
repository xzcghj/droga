import type { MeetupRead, ParticipantRead, SuggestionsRead } from "../api/client";

export const PEOPLE: ParticipantRead[] = [
  { id: 1, name: "Ola", start_label: "Gdynia", lat: 54.52, lon: 18.53, mode: "transit" },
  { id: 2, name: "Kuba", start_label: "Oliwa", lat: 54.41, lon: 18.56, mode: "bike" },
];

export function meetupFixture(over: Partial<MeetupRead> = {}): MeetupRead {
  return {
    id: 1,
    title: "Kawa",
    scheduled_at: "2026-11-21T17:00:00Z",
    venue_category: "cafe",
    chosen_venue: null,
    invite_message: null,
    participants: PEOPLE,
    created_at: "2026-11-15T10:00:00Z",
    updated_at: "2026-11-15T10:00:00Z",
    ...over,
  };
}

export const SUGGESTIONS: SuggestionsRead = {
  venue_source: "overpass",
  candidates: [
    {
      name: "Kawiarnia Łąka",
      osm_id: "node/1",
      lat: 54.44,
      lon: 18.56,
      max_minutes: 20,
      total_minutes: 30,
      spread_minutes: 10,
      travel: [
        { participant_id: 1, minutes: 20, mode: "transit", data_source: "estimate" },
        { participant_id: 2, minutes: 10, mode: "bike", data_source: "osrm" },
      ],
    },
    {
      name: "Bistro B",
      osm_id: "way/2",
      lat: 54.45,
      lon: 18.55,
      max_minutes: 25,
      total_minutes: 40,
      spread_minutes: 10,
      travel: [
        { participant_id: 1, minutes: 25, mode: "transit", data_source: "estimate" },
        { participant_id: 2, minutes: 15, mode: "bike", data_source: "osrm" },
      ],
    },
  ],
};
