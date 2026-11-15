import { ApiError } from "../api/client";
import { Button } from "./ui/Button";

export function ErrorState({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const message = error instanceof ApiError ? error.message : "Coś poszło nie tak.";
  return (
    <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
      <p className="text-sm text-red-800">{message}</p>
      <Button variant="secondary" className="mt-3" onClick={onRetry}>
        Spróbuj ponownie
      </Button>
    </div>
  );
}
