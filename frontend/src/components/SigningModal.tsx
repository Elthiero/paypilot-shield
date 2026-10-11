import { BadgeCheck, KeyRound } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { ApiError } from "../lib/api";
import { signPayload } from "../lib/crypto";
import Banner from "./Banner";
import Button from "./Button";
import CodeBlock from "./CodeBlock";

interface Props {
  title?: string;
  confirmLabel: string;
  summary: ReactNode;
  /** exact string to sign; null while the server is still preparing it */
  payload: string | null;
  /** sends the signature to the server, returns text for the sealed screen */
  onConfirm: (signature: string) => Promise<ReactNode>;
  onClose: () => void;
  prepError?: string | null;
}

type Phase = "idle" | "signing" | "sealed" | "failed";

export default function SigningModal({ title = "Sign with your key", confirmLabel, summary, payload, onConfirm, onClose, prepError }: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<ReactNode>(null);
  const box = useRef<HTMLDivElement>(null);
  const phaseRef = useRef(phase);
  phaseRef.current = phase;

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    box.current?.focus();
    return () => opener?.focus();
  }, []);

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Escape" && phaseRef.current !== "signing") onClose();
    if (e.key !== "Tab" || !box.current) return;
    const f = box.current.querySelectorAll<HTMLElement>("button:not([disabled]), a[href], summary, [tabindex='0']");
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  };

  const sign = async () => {
    if (!payload) return;
    setPhase("signing");
    setError(null);
    try {
      const signature = await signPayload(payload);
      setDone(await onConfirm(signature));
      setPhase("sealed");
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : e instanceof Error ? e.message : "Signing failed.");
      setPhase("failed");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[rgba(17,17,17,0.55)]" onKeyDown={onKey}>
      <div ref={box} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby="sign-title"
           className="relative bg-card border border-ink rounded shadow-hard-lg w-[560px] max-w-full p-6 pt-8"
           style={{ animation: "pagein 200ms cubic-bezier(0.2,0,0,1)" }}>
        <span className="tape -top-3 -left-3 -rotate-6" aria-hidden />
        <span className="tape -top-3 -right-3 rotate-[5deg]" aria-hidden />
        <div className="max-h-[80vh] overflow-y-auto px-1 -mx-1">
        {phase === "sealed" ? (
          <div className="text-center py-4" aria-live="polite">
            <div className="mx-auto w-[72px] h-[72px] rounded-full bg-green border border-ink shadow-hard flex items-center justify-center" style={{ animation: "seal 400ms ease-out" }}>
              <BadgeCheck size={36} aria-hidden />
            </div>
            <p className="note mt-3">signed and verified!</p>
            <div className="text-[14px] mt-2">{done}</div>
            <Button variant="primary" className="mt-5" onClick={onClose}>Close</Button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-11 h-11 rounded-full bg-yellow border border-ink flex items-center justify-center shrink-0"><KeyRound size={20} aria-hidden /></div>
              <div>
                <h2 id="sign-title">{title}</h2>
                <p className="text-[13px] text-ink-mute">Your key never leaves this browser.</p>
              </div>
            </div>
            <div className="border border-ink rounded p-4 mb-4">{summary}</div>
            <details className="mb-4">
              <summary className="label cursor-pointer">Exact data you are signing</summary>
              <div className="mt-2">{payload ? <CodeBlock text={payload} /> : <p className="text-[13px]">Preparing...</p>}</div>
            </details>
            {(prepError || (phase === "failed" && error)) && <div className="mb-4"><Banner kind="error" title="Could not complete signing">{prepError ?? error}</Banner></div>}
            <div className="flex justify-end gap-3">
              <Button variant="secondary" onClick={onClose} disabled={phase === "signing"}>Cancel</Button>
              <Button variant="primary" onClick={sign} loading={phase === "signing"} disabled={!payload}>
                {phase === "signing" ? "Signing..." : phase === "failed" ? "Try again" : confirmLabel}
              </Button>
            </div>
          </>
        )}
        </div>
      </div>
    </div>
  );
}
