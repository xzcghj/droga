import { Check, Scale } from "lucide-react";
import type { CandidateRead, ParticipantRead } from "../../api/client";
import { Button } from "../../components/ui/Button";
import { formatMinutes } from "../../lib/format";
import { FairnessBar } from "./FairnessBar";

export function SuggestionCard({
  index,
  candidate,
  participants,
  chosen,
  choosing,
  onChoose,
  onHighlight,
}: {
  index: number;
  candidate: CandidateRead;
  participants: ParticipantRead[];
  chosen: boolean;
  choosing: boolean;
  onChoose: () => void;
  onHighlight: (id: string | null) => void;
}) {
  const hasEstimate = candidate.travel.some((t) => t.data_source === "estimate");
  return (
    <article
      tabIndex={0}
      aria-label={`${index}. ${candidate.name}`}
      onMouseEnter={() => onHighlight(candidate.osm_id)}
      onMouseLeave={() => onHighlight(null)}
      onFocus={() => onHighlight(candidate.osm_id)}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) onHighlight(null);
      }}
      className={`rounded-xl border bg-white p-3 shadow-sm outline-none transition-shadow hover:shadow-md focus-visible:ring-2 focus-visible:ring-indigo-400 ${
        chosen ? "border-rose-600 ring-1 ring-rose-600" : "border-slate-200"
      }`}
    >
      <header className="mb-2 flex items-start gap-2">
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-700 text-xs font-bold text-white">
          {index}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold">{candidate.name}</h3>
          <p className="text-xs text-slate-600">
            Najdłuższy dojazd: {formatMinutes(candidate.max_minutes)}
            {hasEstimate && <span className="ml-1 text-amber-800">· ≈ szacunek</span>}
          </p>
        </div>
        <span className="inline-flex items-center gap-1 whitespace-nowrap rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-800">
          <Scale size={12} aria-hidden /> Różnica: {formatMinutes(candidate.spread_minutes)}
        </span>
      </header>
      <FairnessBar
        travel={candidate.travel}
        participants={participants}
        maxMinutes={candidate.max_minutes}
      />
      <div className="mt-3 flex justify-end">
        {chosen ? (
          <span className="inline-flex items-center gap-1 text-sm font-medium text-rose-700">
            <Check size={16} aria-hidden /> Wybrane
          </span>
        ) : (
          <Button
            variant="secondary"
            onClick={onChoose}
            disabled={choosing}
            aria-label={`Wybierz: ${candidate.name}`}
          >
            Wybierz
          </Button>
        )}
      </div>
    </article>
  );
}
