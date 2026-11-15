import type { ParticipantRead, TravelRead } from "../../api/client";
import { ModeIcon } from "../../components/ModeIcon";
import { formatMinutes } from "../../lib/format";
import { MODES } from "../../lib/modes";

export function FairnessBar({
  travel,
  participants,
  maxMinutes,
}: {
  travel: TravelRead[];
  participants: ParticipantRead[];
  maxMinutes: number;
}) {
  const names = new Map(participants.map((p) => [p.id, p.name]));
  return (
    <ul className="space-y-1.5">
      {travel.map((t) => {
        const pct = maxMinutes > 0 ? Math.round((t.minutes / maxMinutes) * 100) : 0;
        const estimate = t.data_source === "estimate";
        return (
          <li
            key={t.participant_id}
            className="grid grid-cols-[auto_5rem_1fr_auto] items-center gap-2"
          >
            <ModeIcon mode={t.mode} size={20} />
            <span className="truncate text-xs font-medium">
              {names.get(t.participant_id) ?? "?"}
            </span>
            <span className="h-2 overflow-hidden rounded-full bg-slate-100">
              <span
                data-testid={`bar-${t.participant_id}`}
                className="block h-full rounded-full"
                style={{ width: `${pct}%`, backgroundColor: MODES[t.mode].color }}
              />
            </span>
            <span
              className="whitespace-nowrap text-right text-xs tabular-nums text-slate-700"
              title={estimate ? "Szacunek (bez rozkładu jazdy / bez trasy z OSRM)" : "Czas z OSRM"}
            >
              {estimate ? `≈ ${formatMinutes(t.minutes)}` : formatMinutes(t.minutes)}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
