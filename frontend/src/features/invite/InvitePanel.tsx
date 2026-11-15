import { Copy, Save, Sparkles } from "lucide-react";
import { useState } from "react";
import { ApiError, type MeetupRead } from "../../api/client";
import { useGenerateInvite, useUpdateMeetup } from "../../api/queries";
import { Button } from "../../components/ui/Button";
import { useToast } from "../../components/ui/Toast";

const SOURCE_LABEL = { ai: "napisane przez AI", template: "z szablonu" } as const;
const MAX = 1000;

export function InvitePanel({ meetup }: { meetup: MeetupRead }) {
  const [text, setText] = useState<string | null>(meetup.invite_message ?? null);
  const [source, setSource] = useState<"ai" | "template" | null>(null);
  const generate = useGenerateInvite(meetup.id);
  const update = useUpdateMeetup(meetup.id);
  const toast = useToast();

  if (!meetup.chosen_venue) return null;

  const fail = (err: unknown, fallback: string) =>
    toast.show(err instanceof ApiError ? err.message : fallback, "error");

  async function write() {
    try {
      const invite = await generate.mutateAsync();
      setText(invite.message);
      setSource(invite.source);
    } catch (err) {
      fail(err, "Nie udało się przygotować zaproszenia.");
    }
  }

  async function copy() {
    if (text === null) return;
    try {
      await navigator.clipboard.writeText(text);
      toast.show("Skopiowano", "success");
    } catch {
      toast.show("Nie udało się skopiować — zaznacz tekst i skopiuj ręcznie.", "error");
    }
  }

  function save() {
    if (text === null) return;
    update.mutate(
      { invite_message: text },
      {
        onSuccess: () => toast.show("Zaproszenie zapisane.", "success"),
        onError: (err) => fail(err, "Nie udało się zapisać zaproszenia."),
      },
    );
  }

  return (
    <div className="space-y-3">
      <Button
        variant={text === null ? "primary" : "secondary"}
        className="w-full"
        onClick={write}
        disabled={generate.isPending || meetup.participants.length < 2}
      >
        <Sparkles size={16} aria-hidden />
        {generate.isPending ? "Piszę…" : "Napisz zaproszenie"}
      </Button>
      {text !== null && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label htmlFor="invite-text" className="text-sm font-medium">
              Treść zaproszenia
            </label>
            {source && (
              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                {SOURCE_LABEL[source]}
              </span>
            )}
          </div>
          <textarea
            id="invite-text"
            rows={7}
            maxLength={MAX}
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          />
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={copy}>
              <Copy size={16} aria-hidden /> Kopiuj
            </Button>
            <Button variant="secondary" onClick={save} disabled={update.isPending}>
              <Save size={16} aria-hidden /> Zapisz
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
