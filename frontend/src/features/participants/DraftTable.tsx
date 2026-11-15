import { Search, Trash2 } from "lucide-react";
import type { TravelMode } from "../../api/client";
import { rowReady, type DraftRow } from "./draft";
import { MODE_ORDER, MODES } from "../../lib/modes";

const cell =
  "w-full rounded-md border border-slate-300 px-2 py-1 text-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-200";

export function DraftTable({
  rows,
  onChange,
  onRemove,
  onSearch,
}: {
  rows: DraftRow[];
  onChange: (key: number, patch: Partial<DraftRow>) => void;
  onRemove: (key: number) => void;
  onSearch: (key: number) => void;
}) {
  return (
    <ul className="space-y-2">
      {rows.map((r, i) => {
        const n = i + 1;
        const missingMode = r.mode === null;
        return (
          <li
            key={r.key}
            className={`rounded-lg border p-2 ${
              rowReady(r) ? "border-slate-200 bg-white" : "border-amber-400 bg-amber-50"
            }`}
          >
            <div className="grid grid-cols-[1fr_auto] gap-2">
              <div className="grid grid-cols-2 gap-2">
                <input
                  aria-label={`Imię (wiersz ${n})`}
                  className={cell}
                  value={r.name}
                  maxLength={50}
                  onChange={(e) => onChange(r.key, { name: e.target.value })}
                />
                <select
                  aria-label={`Środek transportu (wiersz ${n})`}
                  className={`${cell} ${missingMode ? "border-amber-500 text-amber-900" : ""}`}
                  value={r.mode ?? ""}
                  onChange={(e) =>
                    onChange(r.key, { mode: (e.target.value || null) as TravelMode | null })
                  }
                >
                  <option value="">— wybierz —</option>
                  {MODE_ORDER.map((m) => (
                    <option key={m} value={m}>
                      {MODES[m].label}
                    </option>
                  ))}
                </select>
                <div className="col-span-2 flex gap-2">
                  <input
                    aria-label={`Skąd (wiersz ${n})`}
                    className={`${cell} ${r.needsGeocode ? "border-amber-500" : ""}`}
                    value={r.start_label}
                    maxLength={200}
                    onChange={(e) =>
                      onChange(r.key, {
                        start_label: e.target.value,
                        needsGeocode: true,
                        lat: null,
                        lon: null,
                        searchError: undefined,
                      })
                    }
                  />
                  {r.needsGeocode && (
                    <button
                      type="button"
                      onClick={() => onSearch(r.key)}
                      disabled={r.searching || !r.start_label.trim()}
                      aria-label={`Szukaj adresu (wiersz ${n})`}
                      className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-2 text-sm hover:bg-slate-100 disabled:opacity-50"
                    >
                      <Search size={14} aria-hidden /> Szukaj
                    </button>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={() => onRemove(r.key)}
                aria-label={`Usuń wiersz ${n}`}
                className="self-start rounded p-1.5 text-slate-500 hover:bg-red-50 hover:text-red-700"
              >
                <Trash2 size={16} />
              </button>
            </div>
            {(missingMode || r.needsGeocode || r.note || r.searchError) && (
              <p className="mt-1 text-xs text-slate-700">
                {missingMode && (
                  <span className="mr-2 text-amber-900">Wybierz środek transportu.</span>
                )}
                {r.needsGeocode && !r.searchError && (
                  <span className="mr-2 text-amber-900">Popraw adres i kliknij „Szukaj”.</span>
                )}
                {r.searchError && <span className="mr-2 text-red-700">{r.searchError}</span>}
                {r.note && <span className="text-slate-600">Uwaga: {r.note}</span>}
              </p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
