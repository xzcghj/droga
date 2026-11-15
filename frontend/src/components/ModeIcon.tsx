import type { TravelMode } from "../api/client";
import { MODES } from "../lib/modes";

/** Środek transportu: kolor + ikona + etykieta dla czytników ekranu. */
export function ModeIcon({ mode, size = 28 }: { mode: TravelMode; size?: number }) {
  const { color, icon: Icon, label } = MODES[mode];
  return (
    <span
      role="img"
      aria-label={label}
      title={label}
      className="inline-flex shrink-0 items-center justify-center rounded-full text-white"
      style={{ backgroundColor: color, width: size, height: size }}
    >
      <Icon size={Math.round(size * 0.55)} aria-hidden />
    </span>
  );
}
