import type { TravelMode } from "../api/client";
import { MODE_ORDER, MODES } from "../lib/modes";

export function ModePicker({
  name,
  value,
  onChange,
  invalid,
  describedBy,
}: {
  name: string;
  value: TravelMode | null;
  onChange: (m: TravelMode) => void;
  invalid?: boolean;
  describedBy?: string;
}) {
  return (
    <div
      role="radiogroup"
      aria-label="Środek transportu"
      aria-invalid={invalid}
      aria-describedby={describedBy}
      className="grid grid-cols-4 gap-1 rounded-lg bg-slate-100 p-1"
    >
      {MODE_ORDER.map((m) => {
        const { label, icon: Icon, color } = MODES[m];
        const checked = value === m;
        return (
          <label
            key={m}
            className={`flex cursor-pointer flex-col items-center gap-0.5 rounded-md px-1 py-1.5 text-xs font-medium focus-within:ring-2 focus-within:ring-indigo-300 ${
              checked ? "bg-white shadow-sm" : "text-slate-600 hover:bg-white/60"
            }`}
            style={checked ? { color } : undefined}
          >
            <input
              type="radio"
              name={name}
              value={m}
              checked={checked}
              onChange={() => onChange(m)}
              className="sr-only"
            />
            <Icon size={18} aria-hidden />
            {label}
          </label>
        );
      })}
    </div>
  );
}
