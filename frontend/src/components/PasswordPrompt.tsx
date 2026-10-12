import { KeyRound } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { ApiError } from "../lib/api";
import Banner from "./Banner";
import Button from "./Button";

/** Asks for the password inside the page, with a masked field (window.prompt shows what you type). */
export default function PasswordPrompt({ title, onSubmit, onClose }: { title: string; onSubmit: (password: string) => Promise<void>; onClose: () => void }) {
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    input.current?.focus();
    return () => opener?.focus();
  }, []);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSubmit(password);
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : err instanceof Error ? err.message : "Something went wrong.");
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/55" onKeyDown={(e) => e.key === "Escape" && !busy && onClose()}>
      <form onSubmit={submit} role="dialog" aria-modal="true" aria-labelledby="pw-title"
            className="bg-card border border-ink rounded shadow-hard-lg w-[420px] max-w-full p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-full bg-cyan border border-ink flex items-center justify-center shrink-0"><KeyRound size={20} aria-hidden /></div>
          <h2 id="pw-title">{title}</h2>
        </div>
        <label className="block"><span className="label block mb-1">Password</span>
          <input ref={input} className="input" type="password" autoComplete="current-password" value={password}
                 onChange={(e) => setPassword(e.target.value)} required maxLength={200} /></label>
        {error && <Banner kind="error" title={error} />}
        <div className="flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={onClose} disabled={busy}>Cancel</Button>
          <Button type="submit" loading={busy}>Confirm</Button>
        </div>
      </form>
    </div>
  );
}
