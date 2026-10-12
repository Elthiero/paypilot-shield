import type { ReactNode } from "react";

interface Props { title?: string; action?: ReactNode; className?: string; children: ReactNode; }

/** White card, 2px outline, hard shadow (DESIGN.md 6.4). Tape is only for DecisionCard and SigningModal. */
export default function Card({ title, action, className = "", children }: Props) {
  return (
    <section className={`card ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between gap-3 mb-4">
          {title && <h2>{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
