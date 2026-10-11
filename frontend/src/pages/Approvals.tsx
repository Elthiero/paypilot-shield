import { useState } from "react";
import { Link } from "react-router-dom";
import ApprovalCard from "../components/ApprovalCard";
import Banner from "../components/Banner";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import PageHeader from "../components/PageHeader";
import { refreshShell } from "../components/Shell";
import SigningModal from "../components/SigningModal";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/StatusBadge";
import useApi from "../hooks/useApi";
import { ApiError, api } from "../lib/api";
import { hasKeypair, registerKey } from "../lib/crypto";
import { money } from "../lib/format";
import type { ApprovalItem, PaymentSummary } from "../lib/types";

export default function Approvals() {
  const { data, loading, error, reload } = useApi<ApprovalItem[]>("/approvals");
  const [signing, setSigning] = useState<ApprovalItem | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [missingKey, setMissingKey] = useState(false);

  const open = async (item: ApprovalItem) => {
    setMissingKey(!(await hasKeypair().catch(() => false)));
    setSigning(item);
  };

  const confirm = async (signature: string) => {
    const item = signing!;
    const r = await api<PaymentSummary>(`/approvals/${item.id}/approve`, { body: { signature } });
    reload();
    refreshShell();
    if (r.status === "BLOCKED") {
      throw new Error(`The verifier refused this payment: ${r.reasons.join("; ")}`);
    }
    return (
      <div className="space-y-2">
        <StatusBadge value={r.status} />
        <p>{item.invoice} {r.status === "PAID" ? "was paid" : "was sent"}. <Link className="text-blue underline" to={`/replay/${r.payment_request_id}`}>Replay the decision</Link></p>
      </div>
    );
  };

  const reject = async (item: ApprovalItem, reason: string) => {
    try {
      await api(`/approvals/${item.id}/reject`, { body: { reason } });
      setNotice(`${item.invoice} was rejected. No payment was made.`);
      reload();
      refreshShell();
    } catch (e) {
      setNotice(e instanceof ApiError ? e.detail : "Could not reject.");
    }
  };

  return (
    <div>
      <PageHeader note="your decision" title="Approvals" text="Payments the rules engine sent to you. You sign the exact payment." />
      {notice && <div className="mb-4"><Banner kind="info" title={notice} /></div>}
      {loading && !data && <Spinner />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && data.length === 0 && <EmptyState note="nothing is waiting for you" text="Ask the agent to pay an invoice that needs a decision." />}
      <div className="max-w-[720px] space-y-10">
        {data?.map((a) => <ApprovalCard key={a.id} item={a} onSign={open} onReject={reject} />)}
      </div>
      {signing && (
        <SigningModal
          confirmLabel="Sign and approve"
          payload={signing.cart_payload}
          onClose={() => { setSigning(null); setNotice(null); }}
          onConfirm={confirm}
          summary={
            <div className="space-y-1 text-[14px]">
              <p><span className="label">Invoice</span> {signing.invoice} ({signing.supplier})</p>
              <p><span className="label">Amount</span> <span className="money font-bold">{money(signing.amount, signing.currency)}</span></p>
              {missingKey && (
                <Banner kind="warn" title="This browser has no signing key" action={<button className="btn-secondary" onClick={async () => { await registerKey(); setMissingKey(false); }}>Create new key</button>}>
                  Create a new key to approve payments. You will need to sign the policy again.
                </Banner>
              )}
            </div>
          }
        />
      )}
    </div>
  );
}
