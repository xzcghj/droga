import { useState, type FormEvent } from "react";
import { ApiError, fieldErrors, type GeocodeMatch, type TravelMode } from "../../api/client";
import { useAddParticipant, useGeocode } from "../../api/queries";
import { FieldError } from "../../components/FieldError";
import { ModePicker } from "../../components/ModePicker";
import { Button } from "../../components/ui/Button";
import { useToast } from "../../components/ui/Toast";
import { AddressConfirm } from "./AddressConfirm";

const inputCls =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-200 aria-[invalid=true]:border-red-600";

export function ParticipantForm({ meetupId, onDone }: { meetupId: number; onDone?: () => void }) {
  const [name, setName] = useState("");
  const [start, setStart] = useState("");
  const [mode, setMode] = useState<TravelMode | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [matches, setMatches] = useState<GeocodeMatch[] | null>(null);
  const geocode = useGeocode();
  const add = useAddParticipant(meetupId);
  const toast = useToast();

  function reset() {
    setName("");
    setStart("");
    setMode(null);
    setMatches(null);
    setErrors({});
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    const local: Record<string, string> = {};
    if (!name.trim()) local.name = "Podaj imię.";
    if (!start.trim()) local.start_label = "Podaj, skąd jedzie.";
    if (!mode) local.mode = "Wybierz środek transportu.";
    setErrors(local);
    if (Object.keys(local).length) return;
    try {
      const { results } = await geocode.mutateAsync(start.trim());
      if (results.length === 0) {
        setErrors({ start_label: "Nie znaleziono adresu — dopisz miasto" });
        return;
      }
      setMatches(results);
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : "Nie udało się wyszukać adresu.", "error");
    }
  }

  async function save(match: GeocodeMatch) {
    if (!mode) return;
    try {
      await add.mutateAsync({
        name: name.trim(),
        start_label: start.trim(),
        mode,
        lat: match.lat,
        lon: match.lon,
      });
      toast.show(`Dodano: ${name.trim()}`, "success");
      reset();
      onDone?.();
    } catch (err) {
      const fields = fieldErrors(err);
      setMatches(null);
      setErrors(fields);
      if (!Object.keys(fields).length) {
        toast.show(err instanceof ApiError ? err.message : "Nie udało się dodać osoby.", "error");
      }
    }
  }

  return (
    <form onSubmit={submit} noValidate className="space-y-3">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="p-name" className="mb-1 block text-sm font-medium">
            Imię
          </label>
          <input
            id="p-name"
            className={inputCls}
            value={name}
            maxLength={50}
            onChange={(e) => setName(e.target.value)}
            aria-invalid={Boolean(errors.name)}
            aria-describedby={errors.name ? "p-name-error" : undefined}
          />
          <FieldError id="p-name-error" message={errors.name} />
        </div>
        <div>
          <label htmlFor="p-start" className="mb-1 block text-sm font-medium">
            Skąd
          </label>
          <input
            id="p-start"
            className={inputCls}
            value={start}
            maxLength={200}
            placeholder="np. Gdańsk Wrzeszcz"
            onChange={(e) => {
              setStart(e.target.value);
              setMatches(null);
            }}
            aria-invalid={Boolean(errors.start_label)}
            aria-describedby={errors.start_label ? "p-start-error" : undefined}
          />
          <FieldError id="p-start-error" message={errors.start_label} />
        </div>
      </div>
      <div>
        <ModePicker
          name="p-mode"
          value={mode}
          onChange={setMode}
          invalid={Boolean(errors.mode)}
          describedBy={errors.mode ? "p-mode-error" : undefined}
        />
        <FieldError id="p-mode-error" message={errors.mode} />
      </div>
      {matches && mode ? (
        <AddressConfirm
          name={name}
          mode={mode}
          matches={matches}
          saving={add.isPending}
          onConfirm={save}
          onCancel={() => setMatches(null)}
        />
      ) : (
        <div className="flex justify-end">
          <Button type="submit" disabled={geocode.isPending}>
            {geocode.isPending ? "Szukam adresu…" : "Dodaj osobę"}
          </Button>
        </div>
      )}
    </form>
  );
}
