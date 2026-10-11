import { CircleCheck, TriangleAlert } from "lucide-react";
import { money } from "../lib/format";
import type { Decision, Risk } from "../lib/types";
import StatusBadge from "./StatusBadge";

interface Props {
  invoice: string;
  supplier?: string;
  amount: number;
  currency?: string;
  decision: Decision;
  risk: Risk;
  reasons: string[];
  /** 0.6 only on the Agent screen */
  tilt?: number;
}

const LEAD: Record<Decision, string> = {
  BLOCKED: "blocked because:",
  NEEDS_APPROVAL: "needs your approval because:",
  AUTO_PAY: "all clear:",
};

export default function DecisionCard({ invoice, supplier, amount, currency, decision, risk, reasons, tilt = 0 }: Props) {
  const pass = decision === "AUTO_PAY";
  return (
    <div className="relative bg-card border border-ink rounded shadow-hard-lg p-5 pt-7" style={{ transform: `rotate(${tilt}deg)` }}>
      <span className="tape -top-3 -left-3 -rotate-6" aria-hidden />
      <span className="tape -top-3 -right-3 rotate-[5deg]" aria-hidden />
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="label text-ink-mute">Invoice</p>
          <p className="text-xl font-extrabold">{invoice}</p>
          {supplier && <p className="text-[13px] text-ink-mute">{supplier}</p>}
        </div>
        <p className="pixel text-2xl money">{money(amount, currency)}</p>
      </div>
      <div className="flex gap-3 mt-3 flex-wrap">
        <StatusBadge value={decision} rotate={-2} />
        <StatusBadge value={risk} rotate={1.5} />
      </div>
      <p className="note mt-3">{LEAD[decision]}</p>
      <ul className="mt-1 space-y-1">
        {reasons.map((r) => (
          <li key={r} className="flex items-start gap-2 text-[14px]">
            {pass ? <CircleCheck size={16} className="mt-0.5 shrink-0" aria-hidden /> : <TriangleAlert size={16} className="mt-0.5 shrink-0" aria-hidden />}
            {r}
          </li>
        ))}
      </ul>
      <p className="note text-[20px] text-center border-t border-dashed border-ink mt-4 pt-3">decided by rules, not by AI</p>
    </div>
  );
}
