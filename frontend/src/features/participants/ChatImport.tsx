import { MessageSquareText } from "lucide-react";
import { useState } from "react";
import { ApiError } from "../../api/client";
import { useAddParticipants, useGeocode, useMeta, useParseParticipants } from "../../api/queries";
import { Button } from "../../components/ui/Button";
import { useToast } from "../../components/ui/Toast";
import { osobyAcc } from "../../lib/format";
import { rowReady, type DraftRow } from "./draft";
import { DraftTable } from "./DraftTable";

const MAX = 2000;
let nextKey = 1;

export function ChatImport({ meetupId }: { meetupId: number }) {
  const meta = useMeta();
  const parse = useParseParticipants();
  const addMany = useAddParticipants(meetupId);
  const geocode = useGeocode();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [rows, setRows] = useState<DraftRow[] | null>(null);
  const [unparsed, setUnparsed] = useState<string[]>([]);

  if (!meta.data?.ai_enabled) return null;

  const fail = (err: unknown, fallback: string) =>
    toast.show(err instanceof ApiError ? err.message : fallback, "error");

  async function recognize() {
    try {
      const draft = await parse.mutateAsync(text);
      setRows(
        draft.participants.map((p) => ({
          key: nextKey++,
          name: p.name,
          start_label: p.start_label,
          mode: p.mode ?? null,
          note: p.note ?? null,
          lat: p.lat ?? null,
          lon: p.lon ?? null,
          needsGeocode: p.geocode_error || p.lat == null || p.lon == null,
        })),
      );
      setUnparsed(draft.unparsed);
    } catch (err) {
      fail(err, "AI nie poradziło sobie z tym tekstem — dodaj osoby ręcznie.");
    }
  }

  const patch = (key: number, p: Partial<DraftRow>) =>
    setRows((all) => all?.map((r) => (r.key === key ? { ...r, ...p } : r)) ?? null);

  async function search(key: number) {
    const row = rows?.find((r) => r.key === key);
    if (!row) return;
    patch(key, { searching: true, searchError: undefined });
    try {
      const { results } = await geocode.mutateAsync(row.start_label.trim());
      const first = results[0];
      if (first) {
        patch(key, { lat: first.lat, lon: first.lon, needsGeocode: false, searching: false });
      } else {
        patch(key, { searching: false, searchError: "Nie znaleziono adresu — dopisz miasto." });
      }
    } catch (err) {
      patch(key, { searching: false });
      fail(err, "Nie udało się wyszukać adresu.");
    }
  }

  async function submit() {
    if (!rows) return;
    try {
      await addMany.mutateAsync(
        rows.map((r) => ({
          name: r.name.trim(),
          start_label: r.start_label.trim(),
          mode: r.mode!,
          lat: r.lat!,
          lon: r.lon!,
        })),
      );
      toast.show(`Dodano ${osobyAcc(rows.length)}.`, "success");
      setRows(null);
      setUnparsed([]);
      setText("");
      setOpen(false);
    } catch (err) {
      fail(err, "Nie udało się dodać osób.");
    }
  }

  const ready = rows !== null && rows.length > 0 && rows.every(rowReady);

  if (!open) {
    return (
      <Button variant="secondary" onClick={() => setOpen(true)} className="w-full">
        <MessageSquareText size={16} aria-hidden /> Wklej z czatu
      </Button>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-3">
      <div>
        <label htmlFor="chat-text" className="mb-1 block text-sm font-medium">
          Wiadomość z czatu
        </label>
        <textarea
          id="chat-text"
          rows={4}
          maxLength={MAX}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="np. ja z Wrzeszcza autem, Ola z Gdyni SKM-ką, Kuba rowerem z Oliwy"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          aria-describedby="chat-count"
        />
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-500">
            AI przygotuje szkic — nic nie zapisze bez Twojej zgody.
          </p>
          <span id="chat-count" className="text-xs text-slate-500">
            {text.length}/{MAX}
          </span>
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={() => setOpen(false)}>
          Anuluj
        </Button>
        <Button onClick={recognize} disabled={!text.trim() || parse.isPending}>
          {parse.isPending ? "Rozpoznaję…" : "Rozpoznaj"}
        </Button>
      </div>

      {rows !== null && (
        <div className="space-y-2 border-t border-slate-200 pt-3">
          {rows.length === 0 ? (
            <p className="text-sm text-slate-600">Nie rozpoznano żadnych osób.</p>
          ) : (
            <DraftTable
              rows={rows}
              onChange={patch}
              onRemove={(key) => setRows((all) => all?.filter((r) => r.key !== key) ?? null)}
              onSearch={search}
            />
          )}
          {unparsed.length > 0 && (
            <p className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600">
              Nie zrozumiano: {unparsed.join(" · ")}
            </p>
          )}
          {rows.length > 0 && (
            <div className="flex justify-end">
              <Button onClick={submit} disabled={!ready || addMany.isPending}>
                Dodaj {osobyAcc(rows.length)}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
