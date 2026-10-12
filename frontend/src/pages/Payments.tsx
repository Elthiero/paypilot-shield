import type { ColDef, ICellRendererParams } from "ag-grid-community";
import { BadgeCheck, Hourglass, ShieldX } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import Button from "../components/Button";
import ErrorState from "../components/ErrorState";
import OpsGrid from "../components/OpsGrid";
import PageHeader from "../components/PageHeader";
import TotalPaidChart from "../components/TotalPaidChart";
import StatusBadge from "../components/StatusBadge";
import useApi from "../hooks/useApi";
import { api } from "../lib/api";
import { duration, money, reasonText, when } from "../lib/format";
import type { PaymentRequest, Reason, Transaction } from "../lib/types";

function Stat({ label, value, icon, fill }: { label: string; value: ReactNode; icon: ReactNode; fill: string }) {
  return (
    <div className="card flex items-center justify-between">
      <div className="min-w-0"><p className="label text-ink-mute">{label}</p><p className="font-pixel font-bold text-[28px] leading-10 money">{value}</p></div>
      <span className={`w-12 h-12 shrink-0 ml-3 rounded-full border border-ink flex items-center justify-center ${fill}`}>{icon}</span>
    </div>
  );
}

export default function Payments() {
  const reqs = useApi<PaymentRequest[]>("/payments");
  const txns = useApi<Transaction[]>("/transactions");
  const [tab, setTab] = useState<"requests" | "payouts">("requests");

  const paid = useMemo(() => (txns.data ?? []).filter((t) => t.status === "SUCCESS").reduce((s, t) => s + t.amount, 0), [txns.data]);
  const awaiting = (reqs.data ?? []).filter((r) => r.status === "AWAITING_APPROVAL").length;
  const blocked = (reqs.data ?? []).filter((r) => r.status === "BLOCKED").length;

  // While a payout is PENDING, ask PayPal every 5 seconds. After about 2 minutes stop and leave the Refresh button.
  const rows = useRef<Transaction[]>([]);
  rows.current = txns.data ?? [];
  const polling = rows.current.some((t) => t.status === "PENDING");
  useEffect(() => {
    if (!polling) return;
    let tries = 0;
    const timer = setInterval(async () => {
      if (document.hidden) return;
      if (++tries > 24) return clearInterval(timer);
      const pending = rows.current.filter((t) => t.status === "PENDING");
      await Promise.allSettled(pending.map((t) => api(`/transactions/${t.id}/refresh`, { method: "POST", body: {} })));
      txns.reload();
      reqs.reload();
    }, 5000);
    return () => clearInterval(timer);
  }, [polling]); // eslint-disable-line react-hooks/exhaustive-deps

  const refresh = async (t: Transaction) => {
    await api(`/transactions/${t.id}/refresh`, { method: "POST", body: {} });
    txns.reload();
    reqs.reload();
  };

  const reqCols: ColDef<PaymentRequest>[] = [
    { field: "id", headerName: "ID", maxWidth: 90 },
    { field: "invoice", headerName: "Invoice", maxWidth: 130 },
    { field: "amount", headerName: "Amount", type: "rightAligned", maxWidth: 130, valueFormatter: (p) => money(p.value), cellClass: "money" },
    { field: "decision", headerName: "Decision", minWidth: 210, cellRenderer: (p: ICellRendererParams<PaymentRequest>) => <StatusBadge value={p.value} /> },
    { field: "risk", headerName: "Risk", minWidth: 165, cellRenderer: (p: ICellRendererParams<PaymentRequest>) => <StatusBadge value={p.value} /> },
    { field: "reasons", headerName: "Reasons", minWidth: 260, sortable: false,
      valueFormatter: (p) => { const r: Reason[] = p.value ?? []; return r.length ? reasonText(r[0]) + (r.length > 1 ? ` (+${r.length - 1})` : "") : ""; } },
    { field: "created_at", headerName: "Requested", minWidth: 190, valueFormatter: (p) => when(p.value) },
    { field: "status", headerName: "Status", minWidth: 210, cellRenderer: (p: ICellRendererParams<PaymentRequest>) => <StatusBadge value={p.value} /> },
    { headerName: "", maxWidth: 110, sortable: false, cellRenderer: (p: ICellRendererParams<PaymentRequest>) => p.data && <Link className="text-blue underline" to={`/replay/${p.data.id}`}>Replay</Link> },
  ];
  const txCols: ColDef<Transaction>[] = [
    { field: "invoice", headerName: "Invoice", maxWidth: 130 },
    { field: "amount", headerName: "Amount", type: "rightAligned", maxWidth: 130, valueFormatter: (p) => money(p.value, p.data?.currency), cellClass: "money" },
    { field: "status", headerName: "Status", minWidth: 150, cellRenderer: (p: ICellRendererParams<Transaction>) => <StatusBadge value={p.value} /> },
    { field: "payout_batch_id", headerName: "Batch id", minWidth: 160 },
    { field: "created_at", headerName: "Sent", minWidth: 190, valueFormatter: (p) => when(p.value) },
    { field: "completed_at", headerName: "Completed", minWidth: 190, valueFormatter: (p) => when(p.value) },
    { headerName: "Duration", minWidth: 120, sortable: false,
      valueGetter: (p) => p.data ? duration(p.data.created_at, p.data.completed_at) || (p.data.status === "PENDING" ? "pending" : "") : "" },
    { headerName: "", maxWidth: 130, sortable: false, cellRenderer: (p: ICellRendererParams<Transaction>) => p.data?.status === "PENDING" && <Button variant="secondary" className="!h-8" onClick={() => refresh(p.data!)}>Refresh</Button> },
  ];

  const err = reqs.error ?? txns.error;
  return (
    <div>
      <PageHeader note="the money trail" title="Payments" text="Every request and every payout, with its decision." />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Stat label="Paid total" value={money(paid)} fill="bg-green" icon={<BadgeCheck size={24} aria-hidden />} />
        <Stat label="Awaiting approval" value={awaiting} fill="bg-yellow" icon={<Hourglass size={24} aria-hidden />} />
        <Stat label="Blocked" value={blocked} fill="bg-pink" icon={<ShieldX size={24} aria-hidden />} />
      </div>
      <TotalPaidChart txns={txns.data ?? []} />
      <div className="flex mb-4" role="tablist">
        {(["requests", "payouts"] as const).map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
            className={`label border border-ink px-4 py-2 -ml-[2px] first:ml-0 ${tab === t ? "bg-yellow" : "bg-card hover:bg-butter"}`}>{t === "requests" ? "Requests" : "Payouts"}</button>
        ))}
      </div>
      {err && <ErrorState message={err} onRetry={() => { reqs.reload(); txns.reload(); }} />}
      {polling && <p className="note mb-2">a payout is still pending. checking PayPal every 5 seconds.</p>}
      {tab === "requests"
        ? <OpsGrid rows={reqs.error ? null : reqs.data} cols={reqCols} loading={reqs.loading} empty={{ note: "no payments yet", text: "Ask the agent to pay an invoice to see its decision here." }} />
        : <OpsGrid rows={txns.error ? null : txns.data} cols={txCols} loading={txns.loading} empty={{ note: "no payouts yet", text: "Payouts appear after a payment is sent to PayPal." }} />}
    </div>
  );
}
