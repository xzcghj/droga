import { Search } from "lucide-react";
import { useState } from "react";
import { ApiError, type CandidateRead, type MeetupRead } from "../../api/client";
import { useSuggestions, useUpdateMeetup } from "../../api/queries";
import { ErrorState } from "../../components/ErrorState";
import { Button } from "../../components/ui/Button";
import { Skeleton } from "../../components/ui/Spinner";
import { useToast } from "../../components/ui/Toast";
import { SuggestionCard } from "./SuggestionCard";

/** Podpis składu: zmiana osób lub ich środków transportu wymaga ponownego „Znajdź miejsce”. */
function lineup(m: MeetupRead): string {
  return (
    m.participants.map((p) => `${p.id}:${p.mode}:${p.lat}:${p.lon}`).join("|") + m.venue_category
  );
}

export function SuggestionsPanel({
  meetup,
  onHighlight,
}: {
  meetup: MeetupRead;
  onHighlight: (id: string | null) => void;
}) {
  const [requestedFor, setRequestedFor] = useState<string | null>(null);
  const current = lineup(meetup);
  const enough = meetup.participants.length >= 2;
  const suggestions = useSuggestions(meetup.id, enough && requestedFor === current);
  const update = useUpdateMeetup(meetup.id);
  const toast = useToast();
  const active = requestedFor === current;

  function choose(c: CandidateRead) {
    update.mutate(
      { chosen_venue: { name: c.name, lat: c.lat, lon: c.lon, osm_id: c.osm_id } },
      {
        onSuccess: () => toast.show(`Wybrano: ${c.name}`, "success"),
        onError: (err) =>
          toast.show(
            err instanceof ApiError ? err.message : "Nie udało się zapisać wyboru.",
            "error",
          ),
      },
    );
  }

  return (
    <div className="space-y-3">
      <div>
        <Button
          className="w-full"
          disabled={!enough || (active && suggestions.isFetching)}
          onClick={() => {
            setRequestedFor(current);
            if (active) void suggestions.refetch();
          }}
        >
          <Search size={16} aria-hidden /> Znajdź miejsce
        </Button>
        {!enough && (
          <p className="mt-1 text-center text-xs text-slate-600">Dodaj co najmniej 2 osoby</p>
        )}
      </div>

      {active && suggestions.isFetching && !suggestions.data && (
        <div className="space-y-3" role="status">
          <p className="text-center text-sm text-slate-600">Szukam lokali i liczę dojazdy…</p>
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
        </div>
      )}
      {active && suggestions.isError && (
        <ErrorState error={suggestions.error} onRetry={() => suggestions.refetch()} />
      )}
      {active && suggestions.data && (
        <>
          {suggestions.data.venue_source === "snapshot" && (
            <p className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-900">
              Lista lokali z zapisanej bazy (usługa mapowa niedostępna)
            </p>
          )}
          {suggestions.data.candidates.length === 0 ? (
            <p className="rounded-lg bg-slate-100 px-3 py-4 text-center text-sm text-slate-600">
              Brak lokali tego typu w okolicy — spróbuj innej kategorii
            </p>
          ) : (
            <ol className="space-y-3">
              {suggestions.data.candidates.map((c, i) => (
                <li key={c.osm_id}>
                  <SuggestionCard
                    index={i + 1}
                    candidate={c}
                    participants={meetup.participants}
                    chosen={meetup.chosen_venue?.osm_id === c.osm_id}
                    choosing={update.isPending}
                    onChoose={() => choose(c)}
                    onHighlight={onHighlight}
                  />
                </li>
              ))}
            </ol>
          )}
          <p className="text-xs text-slate-500">
            Ranking: najkrótszy najdłuższy dojazd (nikt nie jedzie dużo dłużej od innych). „≈” =
            szacunek; komunikacja miejska zawsze szacowana.
          </p>
        </>
      )}
    </div>
  );
}
