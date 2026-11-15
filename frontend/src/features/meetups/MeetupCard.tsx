import { MapPin, Trash2, Users } from "lucide-react";
import { Link } from "react-router-dom";
import type { MeetupSummary } from "../../api/client";
import { Card } from "../../components/ui/Card";
import { formatDateTime } from "../../lib/format";
import { CATEGORIES, CATEGORY_ICONS } from "../../lib/modes";

function people(n: number): string {
  if (n === 1) return "1 osoba";
  if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)) return `${n} osoby`;
  return `${n} osób`;
}

export function MeetupCard({
  meetup,
  onDelete,
}: {
  meetup: MeetupSummary;
  onDelete: (m: MeetupSummary) => void;
}) {
  const Icon = CATEGORY_ICONS[meetup.venue_category];
  return (
    <Card className="flex items-start justify-between gap-3 transition-shadow hover:shadow-md">
      <Link
        to={`/meetups/${meetup.id}`}
        className="min-w-0 flex-1 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-indigo-600"
      >
        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-slate-500">
          <Icon size={14} aria-hidden />
          {CATEGORIES[meetup.venue_category]}
        </div>
        <h3 className="mt-1 truncate text-base font-semibold text-slate-900">{meetup.title}</h3>
        <p className="text-sm text-slate-600">{formatDateTime(meetup.scheduled_at)}</p>
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-700">
          <span className="inline-flex items-center gap-1">
            <Users size={14} aria-hidden /> {people(meetup.participant_count)}
          </span>
          <span className="inline-flex items-center gap-1">
            <MapPin size={14} aria-hidden />
            {meetup.chosen_venue_name ?? (
              <span className="text-slate-500">Miejsce nie wybrane</span>
            )}
          </span>
        </div>
      </Link>
      <button
        type="button"
        onClick={() => onDelete(meetup)}
        aria-label={`Usuń spotkanie ${meetup.title}`}
        className="rounded p-2 text-slate-500 hover:bg-red-50 hover:text-red-700"
      >
        <Trash2 size={16} />
      </button>
    </Card>
  );
}
