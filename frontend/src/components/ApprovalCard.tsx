import { useState } from "react";
import { money, when } from "../lib/format";
import type { ApprovalItem } from "../lib/types";
import Button from "./Button";
import Input from "./Input";
import CodeBlock from "./CodeBlock";
import DecisionCard from "./DecisionCard";

interface Props {
  item: ApprovalItem;
  onSign: (item: ApprovalItem) => void;
  onReject: (item: ApprovalItem, reason: string) => Promise<void>;
}

export default function ApprovalCard({ item, onSign, onReject }: Props) {
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const reject = async () => {
    setBusy(true);
    try { await onReject(item, reason); } finally { setBusy(false); }
  };
  return (
    <div className="space-y-3">
      <DecisionCard invoice={item.invoice} supplier={item.supplier} amount={item.amount} currency={item.currency}
                    decision="NEEDS_APPROVAL" risk={item.risk} reasons={item.reasons} />
      <div className="card space-y-3">
        <p className="text-[13px] text-ink-mute">Requested {when(item.created_at)} for {money(item.amount, item.currency)}.</p>
        <details>
          <summary className="label cursor-pointer">What you are signing</summary>
          <div className="mt-2"><CodeBlock text={item.cart_payload} /></div>
        </details>
        {rejecting ? (
          <div className="space-y-2">
            <Input label="Reason (optional)" value={reason} onChange={(e) => setReason(e.target.value)} />
            <div className="flex gap-3 justify-end">
              <Button variant="secondary" onClick={() => setRejecting(false)} disabled={busy}>Cancel</Button>
              <Button variant="danger" onClick={reject} loading={busy}>Confirm reject</Button>
            </div>
          </div>
        ) : (
          <div className="flex gap-3 justify-end">
            <Button variant="danger" onClick={() => setRejecting(true)}>Reject</Button>
            <Button variant="primary" onClick={() => onSign(item)}>Review and sign</Button>
          </div>
        )}
      </div>
    </div>
  );
}
