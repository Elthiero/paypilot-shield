import type { ReactNode } from "react";

const TABS = ["bg-blue text-white", "bg-yellow text-ink", "bg-cyan text-ink", "bg-pink text-ink", "bg-green text-ink"];

interface Props { index: number; tab: string; right?: ReactNode; failed?: boolean; children: ReactNode; }

/** Trace entry: angled tab over a black body (DESIGN.md 6.7). */
export default function StepBlock({ index, tab, right, failed, children }: Props) {
  return (
    <div>
      <div className="flex items-end justify-between">
        <span
          className={`label inline-block py-[7px] pl-3.5 pr-6 border border-ink border-b-0 ${failed ? "bg-pink text-ink" : TABS[index % TABS.length]}`}
          style={{ clipPath: "polygon(0 0, calc(100% - 14px) 0, 100% 100%, 0 100%)" }}
        >
          {tab}
        </span>
        {right && <span className="font-mono text-[11px] text-ink-mute">{right}</span>}
      </div>
      <div className="bg-ink text-white border border-ink rounded-b px-4 py-3.5">{children}</div>
    </div>
  );
}
