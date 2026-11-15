import { useState } from "react";
import type { GeocodeMatch, TravelMode } from "../../api/client";
import { MeetupMap } from "../../components/MeetupMap";
import { Button } from "../../components/ui/Button";

/** Potwierdzenie pinezki: jeden wynik albo wybór z kilku, z podglądem na mini-mapie. */
export function AddressConfirm({
  name,
  mode,
  matches,
  saving,
  onConfirm,
  onCancel,
}: {
  name: string;
  mode: TravelMode;
  matches: GeocodeMatch[];
  saving: boolean;
  onConfirm: (m: GeocodeMatch) => void;
  onCancel: () => void;
}) {
  const [index, setIndex] = useState(0);
  const selected = matches[index] ?? matches[0]!;

  return (
    <div className="space-y-3 rounded-lg border border-indigo-200 bg-indigo-50/50 p-3">
      <p className="text-sm font-medium">
        {matches.length > 1 ? "O który adres chodzi?" : "Czy to dobre miejsce?"}
      </p>
      {matches.length > 1 ? (
        <fieldset className="space-y-1">
          <legend className="sr-only">Wybierz adres</legend>
          {matches.map((m, i) => (
            <label key={`${m.lat},${m.lon},${i}`} className="flex items-start gap-2 text-sm">
              <input
                type="radio"
                name="address-choice"
                checked={i === index}
                onChange={() => setIndex(i)}
                className="mt-1"
              />
              <span>{m.label}</span>
            </label>
          ))}
        </fieldset>
      ) : (
        <p className="text-sm text-slate-700">{selected.label}</p>
      )}
      <div className="h-40 overflow-hidden rounded-md">
        <MeetupMap
          participants={[
            {
              id: -1,
              name,
              start_label: selected.label,
              lat: selected.lat,
              lon: selected.lon,
              mode,
            },
          ]}
        />
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={onCancel}>
          Popraw adres
        </Button>
        <Button onClick={() => onConfirm(selected)} disabled={saving}>
          Zgadza się — zapisz
        </Button>
      </div>
    </div>
  );
}
