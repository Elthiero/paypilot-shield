import { X } from "lucide-react";
import { useEffect, useRef } from "react";
import type { ReactNode } from "react";
import { trapTab } from "../lib/focus";
import Button from "./Button";

export default function Drawer({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    return () => opener?.focus();
  }, []);
  return (
    <div className="fixed inset-0 z-50 bg-ink/35" onClick={onClose}>
      <aside ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-label={title}
             onKeyDown={(e) => { if (e.key === "Escape") onClose(); trapTab(e, ref.current); }} onClick={(e) => e.stopPropagation()}
             className="absolute right-0 top-0 h-full w-[480px] max-w-full bg-card border-l border-ink shadow-[-6px_6px_0_theme(colors.ink.DEFAULT)] p-6 overflow-y-auto"
             style={{ animation: "pagein 200ms cubic-bezier(0.2,0,0,1)" }}>
        <div className="flex items-center justify-between mb-4">
          <h2>{title}</h2>
          <Button variant="secondary" onClick={onClose} aria-label="Close" className="!w-10 !px-0"><X size={14} /></Button>
        </div>
        {children}
      </aside>
    </div>
  );
}
