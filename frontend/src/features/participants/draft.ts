import type { TravelMode } from "../../api/client";

export interface DraftRow {
  key: number;
  name: string;
  start_label: string;
  mode: TravelMode | null;
  note: string | null;
  lat: number | null;
  lon: number | null;
  /** Adres trzeba (ponownie) wyszukać. */
  needsGeocode: boolean;
  searching?: boolean;
  searchError?: string;
}

export function rowReady(r: DraftRow): boolean {
  return (
    r.name.trim() !== "" &&
    r.start_label.trim() !== "" &&
    r.mode !== null &&
    r.lat !== null &&
    r.lon !== null &&
    !r.needsGeocode
  );
}
