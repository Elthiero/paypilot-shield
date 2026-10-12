import { CircleAlert } from "lucide-react";
import { useId } from "react";
import type { InputHTMLAttributes } from "react";

interface Props extends InputHTMLAttributes<HTMLInputElement> { label: string; helper?: string; error?: string | null; }

/** Label above, 2px outline, hard shadow; error is a pink banner with icon and text (DESIGN.md 6.3). */
export default function Input({ label, helper, error, className = "", ...rest }: Props) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="label block mb-1.5">{label}</label>
      <input id={id} className={`input ${className}`} aria-invalid={!!error} aria-describedby={error ? `${id}-e` : helper ? `${id}-h` : undefined} {...rest} />
      {helper && !error && <p id={`${id}-h`} className="text-[13px] text-ink-mute mt-1.5">{helper}</p>}
      {error && (
        <p id={`${id}-e`} role="alert" className="bg-pink text-ink border border-ink rounded px-3 py-1.5 mt-2 text-[13px] flex items-center gap-2">
          <CircleAlert size={14} aria-hidden />{error}
        </p>
      )}
    </div>
  );
}
