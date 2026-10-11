import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import Button from "../components/Button";
import DecisionCard from "../components/DecisionCard";
import DecisionTrace from "../components/DecisionTrace";
import ErrorState from "../components/ErrorState";
import PageHeader from "../components/PageHeader";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/StatusBadge";
import useApi from "../hooks/useApi";
import { duration } from "../lib/format";
import type { PaymentDetail, TraceEvent } from "../lib/types";

export default function Replay() {
  const { id } = useParams();
  const head = useApi<PaymentDetail>(`/payments/${id}`);
  const trace = useApi<TraceEvent[]>(`/payments/${id}/trace`);
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(trace.data, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch { /* clipboard blocked */ }
  };

  const err = head.error ?? trace.error;
  const d = head.data;
  return (
    <div className="max-w-[820px]">
      <PageHeader note="what happened" title={`Replay of request ${id}`} text="Every step the pipeline took, in order." action={<Link className="btn-secondary" to="/payments">Back to payments</Link>} />
      {err && <ErrorState message={err} onRetry={() => { head.reload(); trace.reload(); }} />}
      {(head.loading || trace.loading) && !err && <Spinner rows={4} />}
      {d && (
        <div className="mb-8 space-y-3">
          <DecisionCard invoice={d.invoice} supplier={d.supplier} amount={d.amount} currency={d.currency} decision={d.decision} risk={d.risk} reasons={d.reasons} />
          <p className="label flex items-center gap-2">Final status <StatusBadge value={d.status} /></p>
          {trace.data && trace.data.length > 1 && <p className="label">Time from first to last step: {duration(trace.data[0].at, trace.data[trace.data.length - 1].at)}</p>}
        </div>
      )}
      {trace.data && (
        <>
          <DecisionTrace events={trace.data} />
          <Button variant="secondary" className="mt-6" onClick={copy}>{copied ? <Check size={12} /> : <Copy size={12} />}{copied ? "Copied" : "Copy as JSON"}</Button>
        </>
      )}
    </div>
  );
}
