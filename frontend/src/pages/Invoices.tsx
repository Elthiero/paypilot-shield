import type { ColDef, ICellRendererParams } from "ag-grid-community";
import { BadgeCheck, Plus, TriangleAlert } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Banner from "../components/Banner";
import Button from "../components/Button";
import Drawer from "../components/Drawer";
import NewInvoiceDrawer from "../components/NewInvoiceDrawer";
import ErrorState from "../components/ErrorState";
import OpsGrid from "../components/OpsGrid";
import PageHeader from "../components/PageHeader";
import { refreshShell } from "../components/Shell";
import StatusBadge from "../components/StatusBadge";
import useApi from "../hooks/useApi";
import { ApiError, api } from "../lib/api";
import { money, reasonText } from "../lib/format";
import type { Invoice, PaymentSummary, Supplier } from "../lib/types";

export default function Invoices() {
  const inv = useApi<Invoice[]>("/invoices");
  const sup = useApi<Supplier[]>("/suppliers");
  const [filter, setFilter] = useState("ALL");
  const [open, setOpen] = useState<Invoice | null>(null);
  const [adding, setAdding] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; text: string; id?: number } | null>(null);

  const lastPayout = useMemo(() => new Map((sup.data ?? []).map((s) => [s.name, s.last_payout_email])), [sup.data]);
  const mismatch = (i: Invoice) => {
    const last = lastPayout.get(i.supplier ?? "");
    return !!last && last.toLowerCase() !== i.payee_email.toLowerCase();
  };

  const statuses = ["ALL", ...Array.from(new Set((inv.data ?? []).map((i) => i.status)))];
  const rows = (inv.data ?? []).filter((i) => filter === "ALL" || i.status === filter);

  const cols: ColDef<Invoice>[] = [
    { field: "number", headerName: "Number", maxWidth: 130 },
    { field: "supplier", headerName: "Supplier", minWidth: 170 },
    { field: "supplier_verified", headerName: "Verified", maxWidth: 120, sortable: false,
      cellRenderer: (p: ICellRendererParams<Invoice>) => p.value ? <span className="flex items-center gap-1"><BadgeCheck size={16} aria-hidden />Yes</span> : <span className="flex items-center gap-1 text-ink-mute"><TriangleAlert size={16} aria-hidden />No</span> },
    { field: "amount", headerName: "Amount", type: "rightAligned", maxWidth: 140,
      valueFormatter: (p) => money(p.value, p.data?.currency), cellClass: "money" },
    { field: "status", headerName: "Status", minWidth: 210, cellRenderer: (p: ICellRendererParams<Invoice>) => <StatusBadge value={p.value} /> },
    { field: "payee_email", headerName: "Payee email", minWidth: 340,
      cellRenderer: (p: ICellRendererParams<Invoice>) => p.data && mismatch(p.data)
        ? <span className="flex items-center gap-1.5 font-semibold" title="Differs from the supplier's last payout email"><TriangleAlert size={16} aria-hidden /><span className="sr-only">Differs from the last payout email. </span>{p.value}</span>
        : <span>{p.value}</span> },
  ];

  const request = async () => {
    if (!open) return;
    setBusy(true);
    setResult(null);
    try {
      const r = await api<PaymentSummary>("/payments", { body: { invoice_number: open.number } });
      setResult({ ok: r.status !== "BLOCKED", text: `${r.invoice}: ${r.note ?? r.reasons.map(reasonText).join("; ")} (${r.status})`, id: r.payment_request_id });
      inv.reload();
      refreshShell();
    } catch (e) {
      setResult({ ok: false, text: e instanceof ApiError ? e.detail : "Could not reach the server." });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <PageHeader note="your invoices" title="Invoices" text="Everything waiting to be paid. Open one to request payment."
        action={<Button onClick={() => setAdding(true)}><Plus size={14} aria-hidden />New invoice</Button>} />
      {inv.error && <ErrorState message={inv.error} onRetry={inv.reload} />}
      {!inv.error && <div className="flex gap-2 mb-4 flex-wrap" role="group" aria-label="Filter by status">
        {statuses.map((s) => (
          <button key={s} onClick={() => setFilter(s)} aria-pressed={filter === s}
            className={`label border border-ink rounded px-2.5 py-1 ${filter === s ? "bg-blue text-white" : "bg-card hover:bg-sky"}`}>{s === "ALL" ? "All" : s.replace(/_/g, " ")}</button>
        ))}
      </div>}
      <OpsGrid rows={inv.error ? null : rows} cols={cols} loading={inv.loading} onRowClicked={(r) => { setOpen(r); setResult(null); }}
        empty={{ note: "no invoices", text: "Nothing matches this filter." }} />
      {adding && <NewInvoiceDrawer suppliers={sup.data ?? []} onClose={() => setAdding(false)}
        onCreated={(i) => { setAdding(false); inv.reload(); setOpen(i); setResult(null); }} />}
      {open && (
        <Drawer title={open.number} onClose={() => setOpen(null)}>
          <div className="space-y-4">
            <p className="pixel text-2xl money">{money(open.amount, open.currency)}</p>
            <div className="flex gap-2 flex-wrap"><StatusBadge value={open.status} /></div>
            <dl className="text-[14px] space-y-1">
              <p><span className="label">Supplier</span> {open.supplier}</p>
              <p><span className="label">Payee</span> {open.payee_email}</p>
            </dl>
            {mismatch(open) && <Banner kind="warn" title="Payee email changed">It differs from the email of this supplier's last payout.</Banner>}
            <div className="border border-dashed border-ink rounded p-3 bg-card">
              <p className="text-[14px] break-words">{open.description}</p>
              <p className="text-[12px] text-ink-mute mt-2 flex items-start gap-1.5"><TriangleAlert size={14} className="shrink-0 mt-0.5" aria-hidden />Untrusted invoice text. Treated as data, never as instructions.</p>
            </div>
            {result && <Banner kind={result.ok ? "success" : "error"} title={result.text}>{result.id && <Link className="underline" to={`/replay/${result.id}`}>Replay the decision</Link>}</Banner>}
            <Button onClick={request} loading={busy} disabled={["PAID", "SENT"].includes(open.status)}>Request payment</Button>
          </div>
        </Drawer>
      )}
    </div>
  );
}
