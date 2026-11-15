const TZ = "Europe/Warsaw";

/** „sob., 21 lis 2026, 18:00” — zawsze w czasie polskim. */
export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat("pl-PL", {
    timeZone: TZ,
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

/** „18 min” albo „1 h 05 min”. */
export function formatMinutes(n: number): string {
  const total = Math.max(0, Math.round(n));
  if (total < 60) return `${total} min`;
  const h = Math.floor(total / 60);
  const m = total % 60;
  return `${h} h ${String(m).padStart(2, "0")} min`;
}

function warsawOffsetMinutes(utcMs: number): number {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: TZ,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).formatToParts(new Date(utcMs));
  const get = (t: string) => Number(parts.find((p) => p.type === t)?.value);
  const asUtc = Date.UTC(get("year"), get("month") - 1, get("day"), get("hour"), get("minute"));
  return Math.round((asUtc - Math.floor(utcMs / 60000) * 60000) / 60000);
}

/**
 * Wartość z <input type="datetime-local"> („2026-11-21T18:00”) traktowana jako czas polski
 * → ISO 8601 z offsetem („2026-11-21T18:00:00+01:00”), niezależnie od strefy przeglądarki.
 */
export function warsawLocalToIso(local: string): string {
  const [date = "", time = "00:00"] = local.split("T");
  const [y, mo, d] = date.split("-").map(Number);
  const [h, mi] = time.split(":").map(Number);
  const naiveUtc = Date.UTC(y!, mo! - 1, d!, h!, mi!);
  let offset = warsawOffsetMinutes(naiveUtc);
  offset = warsawOffsetMinutes(naiveUtc - offset * 60000);
  const sign = offset >= 0 ? "+" : "-";
  const abs = Math.abs(offset);
  const hh = String(Math.floor(abs / 60)).padStart(2, "0");
  const mm = String(abs % 60).padStart(2, "0");
  return `${date}T${time.slice(0, 5)}:00${sign}${hh}:${mm}`;
}

export function initials(name: string): string {
  const letters = name
    .trim()
    .split(/\s+/)
    .map((w) => w[0] ?? "")
    .join("");
  return letters.slice(0, 2).toUpperCase() || "?";
}

/** „1 osobę / 2 osoby / 5 osób” (biernik, np. „Dodaj 2 osoby”). */
export function osobyAcc(n: number): string {
  if (n === 1) return "1 osobę";
  if ([2, 3, 4].includes(n % 10) && ![12, 13, 14].includes(n % 100)) return `${n} osoby`;
  return `${n} osób`;
}
