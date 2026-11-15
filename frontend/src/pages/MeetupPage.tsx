import { ArrowLeft } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMeetup } from "../api/queries";
import { ErrorState } from "../components/ErrorState";
import { MeetupMap } from "../components/MeetupMap";
import { Skeleton } from "../components/ui/Spinner";
import { ChatImport } from "../features/participants/ChatImport";
import { ParticipantForm } from "../features/participants/ParticipantForm";
import { ParticipantList } from "../features/participants/ParticipantList";
import { formatDateTime } from "../lib/format";
import { CATEGORIES, CATEGORY_ICONS } from "../lib/modes";
import { useMediaQuery } from "../lib/useMediaQuery";

type Tab = "list" | "map";

export function MeetupPage() {
  const id = Number(useParams().id);
  const meetup = useMeetup(id);
  const wide = useMediaQuery("(min-width: 768px)");
  const [tab, setTab] = useState<Tab>("list");

  if (meetup.isPending) {
    return (
      <div className="mx-auto max-w-3xl space-y-3 p-6" aria-label="Ładowanie spotkania">
        <Skeleton className="h-10 w-1/2" />
        <Skeleton className="h-40" />
      </div>
    );
  }
  if (meetup.isError) {
    return (
      <div className="mx-auto max-w-xl p-6">
        <Link to="/" className="mb-4 inline-flex items-center gap-1 text-sm text-indigo-700">
          <ArrowLeft size={16} aria-hidden /> Wszystkie spotkania
        </Link>
        <ErrorState error={meetup.error} onRetry={() => meetup.refetch()} />
      </div>
    );
  }

  const m = meetup.data;
  const CategoryIcon = CATEGORY_ICONS[m.venue_category];
  const showPanel = wide || tab === "list";
  const showMap = wide || tab === "map";

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-slate-200 bg-white px-4 py-3">
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm text-indigo-700 hover:underline"
        >
          <ArrowLeft size={16} aria-hidden /> Wszystkie spotkania
        </Link>
        <h1 className="mt-1 text-xl font-bold">{m.title}</h1>
        <p className="flex flex-wrap items-center gap-x-3 text-sm text-slate-600">
          <span>{formatDateTime(m.scheduled_at)}</span>
          <span className="inline-flex items-center gap-1">
            <CategoryIcon size={14} aria-hidden /> {CATEGORIES[m.venue_category]}
          </span>
        </p>
      </header>

      {!wide && (
        <div
          role="tablist"
          aria-label="Widok"
          className="grid grid-cols-2 border-b border-slate-200 bg-white"
        >
          {(["list", "map"] as const).map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              onClick={() => setTab(t)}
              className={`py-2 text-sm font-medium ${tab === t ? "border-b-2 border-indigo-700 text-indigo-800" : "text-slate-600"}`}
            >
              {t === "list" ? "Lista" : "Mapa"}
            </button>
          ))}
        </div>
      )}

      <div className="flex min-h-0 flex-1">
        {showPanel && (
          <aside className="w-full space-y-6 overflow-y-auto p-4 md:w-[420px] md:shrink-0 md:border-r md:border-slate-200">
            <section aria-labelledby="people-h" className="space-y-3">
              <h2 id="people-h" className="text-base font-semibold">
                Uczestnicy ({m.participants.length}/10)
              </h2>
              <ParticipantList meetupId={m.id} participants={m.participants} />
              {m.participants.length < 10 && (
                <>
                  <ParticipantForm meetupId={m.id} />
                  <ChatImport meetupId={m.id} />
                </>
              )}
            </section>
          </aside>
        )}
        {showMap && (
          <div className="min-h-[60vh] flex-1 md:min-h-0">
            <MeetupMap participants={m.participants} chosen={m.chosen_venue} />
          </div>
        )}
      </div>
    </div>
  );
}
