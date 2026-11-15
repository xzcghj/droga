import { MapPinned } from "lucide-react";
import { Button } from "../../components/ui/Button";

export function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
      <MapPinned className="mx-auto text-indigo-700" size={36} aria-hidden />
      <h2 className="mt-3 text-lg font-semibold">Nie masz jeszcze spotkań</h2>
      <p className="mx-auto mt-1 max-w-sm text-sm text-slate-600">
        Dodaj znajomych, ich punkty startowe i środki transportu — znajdziemy miejsce, do którego
        każdy ma podobnie daleko.
      </p>
      <Button className="mt-5" onClick={onCreate}>
        Utwórz spotkanie
      </Button>
    </div>
  );
}
