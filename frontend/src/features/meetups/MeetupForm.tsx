import { useState, type FormEvent } from "react";
import { ApiError, fieldErrors, type VenueCategory } from "../../api/client";
import { useCreateMeetup } from "../../api/queries";
import { FieldError } from "../../components/FieldError";
import { Button } from "../../components/ui/Button";
import { useToast } from "../../components/ui/Toast";
import { warsawLocalToIso } from "../../lib/format";
import { CATEGORIES, CATEGORY_ICONS, CATEGORY_ORDER } from "../../lib/modes";

const inputCls =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-200 aria-[invalid=true]:border-red-600";

export function MeetupForm({ onCreated }: { onCreated: (id: number) => void }) {
  const [title, setTitle] = useState("");
  const [when, setWhen] = useState("");
  const [category, setCategory] = useState<VenueCategory>("cafe");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const create = useCreateMeetup();
  const toast = useToast();

  async function submit(e: FormEvent) {
    e.preventDefault();
    const local: Record<string, string> = {};
    if (!title.trim()) local.title = "Podaj nazwę spotkania.";
    if (!when) local.scheduled_at = "Wybierz datę i godzinę.";
    setErrors(local);
    if (Object.keys(local).length) return;
    try {
      const meetup = await create.mutateAsync({
        title: title.trim(),
        scheduled_at: warsawLocalToIso(when),
        venue_category: category,
      });
      onCreated(meetup.id);
    } catch (err) {
      const fields = fieldErrors(err);
      setErrors(fields);
      if (!Object.keys(fields).length) {
        toast.show(
          err instanceof ApiError ? err.message : "Nie udało się utworzyć spotkania.",
          "error",
        );
      }
    }
  }

  return (
    <form onSubmit={submit} noValidate className="space-y-4">
      <div>
        <label htmlFor="meetup-title" className="mb-1 block text-sm font-medium">
          Nazwa
        </label>
        <input
          id="meetup-title"
          className={inputCls}
          value={title}
          maxLength={100}
          placeholder="np. Kawa w sobotę"
          onChange={(e) => setTitle(e.target.value)}
          aria-invalid={Boolean(errors.title)}
          aria-describedby={errors.title ? "meetup-title-error" : undefined}
        />
        <FieldError id="meetup-title-error" message={errors.title} />
      </div>
      <div>
        <label htmlFor="meetup-when" className="mb-1 block text-sm font-medium">
          Data i godzina
        </label>
        <input
          id="meetup-when"
          type="datetime-local"
          className={inputCls}
          value={when}
          onChange={(e) => setWhen(e.target.value)}
          aria-invalid={Boolean(errors.scheduled_at)}
          aria-describedby={errors.scheduled_at ? "meetup-when-error" : "meetup-when-hint"}
        />
        <p id="meetup-when-hint" className="mt-1 text-xs text-slate-500">
          Czas polski.
        </p>
        <FieldError id="meetup-when-error" message={errors.scheduled_at} />
      </div>
      <fieldset>
        <legend className="mb-1 block text-sm font-medium">Typ miejsca</legend>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {CATEGORY_ORDER.map((c) => {
            const Icon = CATEGORY_ICONS[c];
            const checked = category === c;
            return (
              <label
                key={c}
                className={`flex cursor-pointer flex-col items-center gap-1 rounded-lg border px-2 py-3 text-sm focus-within:ring-2 focus-within:ring-indigo-300 ${
                  checked
                    ? "border-indigo-700 bg-indigo-50 text-indigo-900"
                    : "border-slate-300 hover:bg-slate-50"
                }`}
              >
                <input
                  type="radio"
                  name="venue_category"
                  value={c}
                  checked={checked}
                  onChange={() => setCategory(c)}
                  className="sr-only"
                />
                <Icon size={20} aria-hidden />
                {CATEGORIES[c]}
              </label>
            );
          })}
        </div>
      </fieldset>
      <div className="flex justify-end">
        <Button type="submit" disabled={create.isPending}>
          {create.isPending ? "Tworzę…" : "Utwórz spotkanie"}
        </Button>
      </div>
    </form>
  );
}
