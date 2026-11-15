import { Trash2 } from "lucide-react";
import { ApiError, type ParticipantRead, type TravelMode } from "../../api/client";
import { useDeleteParticipant, useUpdateParticipant } from "../../api/queries";
import { ModeIcon } from "../../components/ModeIcon";
import { useToast } from "../../components/ui/Toast";
import { MODE_ORDER, MODES } from "../../lib/modes";

export function ParticipantList({
  meetupId,
  participants,
}: {
  meetupId: number;
  participants: ParticipantRead[];
}) {
  const update = useUpdateParticipant(meetupId);
  const remove = useDeleteParticipant(meetupId);
  const toast = useToast();

  const fail = (err: unknown) =>
    toast.show(err instanceof ApiError ? err.message : "Nie udało się zapisać zmiany.", "error");

  if (participants.length === 0) {
    return (
      <p className="rounded-lg bg-slate-100 px-3 py-4 text-center text-sm text-slate-600">
        Nikt jeszcze nie dołączył. Dodaj co najmniej 2 osoby.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
      {participants.map((p) => (
        <li key={p.id} className="flex items-center gap-3 px-3 py-2">
          <ModeIcon mode={p.mode} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{p.name}</p>
            <p className="truncate text-xs text-slate-600">{p.start_label}</p>
          </div>
          <label className="sr-only" htmlFor={`mode-${p.id}`}>
            Środek transportu: {p.name}
          </label>
          <select
            id={`mode-${p.id}`}
            value={p.mode}
            disabled={update.isPending}
            onChange={(e) =>
              update.mutate(
                { id: p.id, data: { mode: e.target.value as TravelMode } },
                { onError: fail },
              )
            }
            className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
          >
            {MODE_ORDER.map((m) => (
              <option key={m} value={m}>
                {MODES[m].label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => remove.mutate(p.id, { onError: fail })}
            aria-label={`Usuń: ${p.name}`}
            className="rounded p-1.5 text-slate-500 hover:bg-red-50 hover:text-red-700"
          >
            <Trash2 size={16} />
          </button>
        </li>
      ))}
    </ul>
  );
}
