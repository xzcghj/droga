import { MapPin } from "lucide-react";
import { ApiError, type MeetupRead } from "../../api/client";
import { useUpdateMeetup } from "../../api/queries";
import { Button } from "../../components/ui/Button";
import { useToast } from "../../components/ui/Toast";

export function ChosenVenueBanner({ meetup }: { meetup: MeetupRead }) {
  const update = useUpdateMeetup(meetup.id);
  const toast = useToast();
  if (!meetup.chosen_venue) return null;
  return (
    <div className="flex items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 p-3">
      <MapPin className="shrink-0 text-rose-700" size={20} aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="text-xs uppercase tracking-wide text-rose-800">Wybrane miejsce</p>
        <p className="truncate text-sm font-semibold">{meetup.chosen_venue.name}</p>
      </div>
      <Button
        variant="secondary"
        disabled={update.isPending}
        onClick={() =>
          update.mutate(
            { chosen_venue: null },
            {
              onError: (err) =>
                toast.show(
                  err instanceof ApiError ? err.message : "Nie udało się zmienić.",
                  "error",
                ),
            },
          )
        }
      >
        Zmień
      </Button>
    </div>
  );
}
