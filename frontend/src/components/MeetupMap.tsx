import L, { type LatLngBoundsExpression } from "leaflet";
import { useEffect, useMemo } from "react";
import { MapContainer, Marker, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";
import type { CandidateRead, ChosenVenue, ParticipantRead } from "../api/client";
import { initials } from "../lib/format";
import { MODES } from "../lib/modes";

const TRICITY: [number, number] = [54.44, 18.57];

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

function badge(text: string, bg: string, size: number, extra = ""): L.DivIcon {
  return L.divIcon({
    className: "",
    html: `<div style="background:${bg};width:${size}px;height:${size}px;${extra}" class="flex items-center justify-center rounded-full border-2 border-white text-xs font-bold text-white shadow-md">${escapeHtml(text)}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap();
  const key = JSON.stringify(points);
  useEffect(() => {
    if (points.length === 0) return;
    if (points.length === 1) map.setView(points[0]!, 14);
    else map.fitBounds(points as LatLngBoundsExpression, { padding: [40, 40], maxZoom: 15 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, map]);
  return null;
}

export function MeetupMap({
  participants,
  candidates = [],
  chosen = null,
  highlightedId = null,
  className = "h-full w-full",
}: {
  participants: ParticipantRead[];
  candidates?: CandidateRead[];
  chosen?: ChosenVenue | null;
  highlightedId?: string | null;
  className?: string;
}) {
  const highlighted =
    candidates.find((c) => c.osm_id === highlightedId) ??
    (chosen && chosen.osm_id === highlightedId ? chosen : null);

  const points = useMemo(() => {
    const pts: [number, number][] = participants.map((p) => [p.lat, p.lon]);
    candidates.forEach((c) => pts.push([c.lat, c.lon]));
    if (chosen) pts.push([chosen.lat, chosen.lon]);
    return pts;
  }, [participants, candidates, chosen]);

  return (
    <MapContainer center={TRICITY} zoom={11} className={className} scrollWheelZoom>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      <FitBounds points={points} />
      {highlighted &&
        participants.map((p) => (
          <Polyline
            key={`line-${p.id}`}
            positions={[
              [p.lat, p.lon],
              [highlighted.lat, highlighted.lon],
            ]}
            pathOptions={{ color: MODES[p.mode].color, weight: 3, opacity: 0.8, dashArray: "6 6" }}
          />
        ))}
      {participants.map((p) => (
        <Marker
          key={`p-${p.id}`}
          position={[p.lat, p.lon]}
          icon={badge(initials(p.name), MODES[p.mode].color, 32)}
          keyboard={false}
        >
          <Tooltip>
            {p.name} — {MODES[p.mode].label.toLowerCase()}
            <br />
            {p.start_label}
          </Tooltip>
        </Marker>
      ))}
      {candidates.map((c, i) => {
        const active = c.osm_id === highlightedId;
        return (
          <Marker
            key={`c-${c.osm_id}`}
            position={[c.lat, c.lon]}
            icon={badge(String(i + 1), active ? "#be123c" : "#334155", active ? 34 : 26)}
            zIndexOffset={active ? 1000 : 0}
            keyboard={false}
          >
            <Tooltip>{c.name}</Tooltip>
          </Marker>
        );
      })}
      {chosen && !candidates.some((c) => c.osm_id === chosen.osm_id) && (
        <Marker
          position={[chosen.lat, chosen.lon]}
          icon={badge("★", "#be123c", 34)}
          zIndexOffset={1000}
          keyboard={false}
        >
          <Tooltip>{chosen.name}</Tooltip>
        </Marker>
      )}
    </MapContainer>
  );
}
