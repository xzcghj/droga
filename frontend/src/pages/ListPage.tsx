import { Plus } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, type MeetupSummary } from "../api/client";
import { useDeleteMeetup, useMeetups } from "../api/queries";
import { ErrorState } from "../components/ErrorState";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { Skeleton } from "../components/ui/Spinner";
import { useToast } from "../components/ui/Toast";
import { EmptyState } from "../features/meetups/EmptyState";
import { MeetupCard } from "../features/meetups/MeetupCard";
import { MeetupForm } from "../features/meetups/MeetupForm";

export function ListPage() {
  const meetups = useMeetups();
  const remove = useDeleteMeetup();
  const navigate = useNavigate();
  const toast = useToast();
  const [creating, setCreating] = useState(false);
  const [toDelete, setToDelete] = useState<MeetupSummary | null>(null);

  async function confirmDelete() {
    if (!toDelete) return;
    try {
      await remove.mutateAsync(toDelete.id);
      toast.show("Spotkanie usunięte.", "success");
    } catch (err) {
      toast.show(err instanceof ApiError ? err.message : "Nie udało się usunąć.", "error");
    } finally {
      setToDelete(null);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Pół Drogi</h1>
          <p className="text-sm text-slate-600">
            Sprawiedliwe miejsce spotkania — nikt nie jedzie 50 minut, gdy inni 5.
          </p>
        </div>
        {meetups.data && meetups.data.length > 0 && (
          <Button onClick={() => setCreating(true)}>
            <Plus size={16} aria-hidden /> Nowe spotkanie
          </Button>
        )}
      </header>

      {meetups.isPending && (
        <div className="space-y-3" aria-label="Ładowanie spotkań">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      )}
      {meetups.isError && <ErrorState error={meetups.error} onRetry={() => meetups.refetch()} />}
      {meetups.data?.length === 0 && <EmptyState onCreate={() => setCreating(true)} />}
      {meetups.data && meetups.data.length > 0 && (
        <ul className="space-y-3">
          {meetups.data.map((m) => (
            <li key={m.id}>
              <MeetupCard meetup={m} onDelete={setToDelete} />
            </li>
          ))}
        </ul>
      )}

      <Modal open={creating} title="Nowe spotkanie" onClose={() => setCreating(false)}>
        <MeetupForm
          onCreated={(id) => {
            setCreating(false);
            navigate(`/meetups/${id}`);
          }}
        />
      </Modal>
      <Modal open={toDelete !== null} title="Usunąć spotkanie?" onClose={() => setToDelete(null)}>
        <p className="text-sm text-slate-700">
          „{toDelete?.title}” zostanie usunięte razem z uczestnikami. Tej operacji nie można cofnąć.
        </p>
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="secondary" onClick={() => setToDelete(null)}>
            Anuluj
          </Button>
          <Button variant="danger" onClick={confirmDelete} disabled={remove.isPending}>
            Usuń
          </Button>
        </div>
      </Modal>
    </div>
  );
}
