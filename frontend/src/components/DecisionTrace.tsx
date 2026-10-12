import { useState } from "react";
import { duration, money, reasonText, stepLabel, when } from "../lib/format";
import type { TraceEvent } from "../lib/types";
import StepBlock from "./StepBlock";

const FAIL = /(failed|error|blocked|rejected|expired)/;

const list = (v: unknown): string => (Array.isArray(v) ? v.map(reasonText).join("; ") : "");
const usd = (v: unknown): string => (typeof v === "number" ? money(v) : String(v ?? ""));

/** One plain sentence per known step. Unknown future steps fall back to the generic reasons or failures. */
function summary(e: TraceEvent): string {
  const d = e.detail as Record<string, unknown>;
  switch (e.step) {
    case "request_received": return `Payment requested for ${d.invoice}.`;
    case "invoice_loaded": return `${d.supplier}, ${usd(d.amount)}, payee ${d.payee_email}.`;
    case "supplier_history_checked": return `${d.successful_payouts} earlier successful payout(s) to this supplier.`;
    case "truth_check_done": return list(d.blocking) ? `Failed: ${list(d.blocking)}.` : list(d.review) ? `Needs review: ${list(d.review)}.` : "No warning signs found.";
    case "decision_made": return `${d.decision} (${d.risk} risk): ${list(d.reasons)}.`;
    case "blocked_no_payout": return "Blocked. PayPal was never contacted.";
    case "approval_requested": return `Waiting for the owner to sign: ${list(d.reasons)}.`;
    case "approved": return `Owner signed the exact payment (${d.user}).`;
    case "rejected": return `Owner rejected it${d.reason ? `: ${d.reason}` : ""}.`;
    case "approval_expired": return "The approval window passed. The invoice must be submitted again.";
    case "verifier_passed": return "Signed policy, invoice snapshot, budget and signature all checked out.";
    case "verifier_failed": return `Refused before PayPal: ${list(d.failures)}.`;
    case "payout_sent": return `Sent ${usd(d.amount)} to ${d.receiver}.`;
    case "payout_confirmed": return `PayPal confirmed the payout (transaction ${d.paypal_txn_id}).`;
    case "payout_failed": return `PayPal reported ${d.batch_status}.`;
    case "payout_error": return `PayPal returned HTTP ${d.http_status}.`;
    default: return [list(d.reasons), list(d.failures)].filter(Boolean).join(" | ") || "Recorded.";
  }
}

function One({ e, i, start }: { e: TraceEvent; i: number; start: string }) {
  const [open, setOpen] = useState(false);
  const failed = FAIL.test(e.step) || (Array.isArray(e.detail.blocking) && e.detail.blocking.length > 0);
  return (
    <StepBlock index={i} tab={stepLabel(e.step)} right={i > 0 ? `${when(e.at)} (+${duration(start, e.at)})` : when(e.at)} failed={failed}>
      <p className="text-[14px]">{summary(e)}</p>
      <button className="font-mono text-[12px] underline mt-2 text-step" onClick={() => setOpen(!open)} aria-expanded={open}>
        {open ? "Hide" : "Show"} raw JSON
      </button>
      {open && <pre className="font-mono text-[12px] mt-2 whitespace-pre-wrap break-all text-step">{JSON.stringify(e.detail, null, 2)}</pre>}
    </StepBlock>
  );
}

export default function DecisionTrace({ events }: { events: TraceEvent[] }) {
  return <div className="space-y-3">{events.map((e, i) => <One key={e.id} e={e} i={i} start={events[0].at} />)}</div>;
}
