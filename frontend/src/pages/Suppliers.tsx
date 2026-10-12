import type { ColDef, ICellRendererParams } from "ag-grid-community";
import { Plus, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import AddSupplierDrawer from "../components/AddSupplierDrawer";
import Banner from "../components/Banner";
import Button from "../components/Button";
import Drawer from "../components/Drawer";
import ErrorState from "../components/ErrorState";
import OpsGrid from "../components/OpsGrid";
import PageHeader from "../components/PageHeader";
import SigningModal from "../components/SigningModal";
import Skeleton from "../components/Skeleton";
import StatusBadge from "../components/StatusBadge";
import useApi from "../hooks/useApi";
import { api } from "../lib/api";
import { money, stepLabel, when } from "../lib/format";
import type { Supplier, SupplierAnalytics } from "../lib/types";

const differs = (s: Supplier) => !!s.last_payout_email && s.last_payout_email.toLowerCase() !== s.paypal_email.toLowerCase();

const cols: ColDef<Supplier>[] = [
  { field: "name", headerName: "Name" },
  { field: "country", headerName: "Country", maxWidth: 120 },
  { field: "paypal_email", headerName: "PayPal email", minWidth: 240 },
  { field: "verified", headerName: "Verified", maxWidth: 150,
    cellRenderer: (p: ICellRendererParams<Supplier>) => <StatusBadge value={p.value ? "VERIFIED" : "UNVERIFIED"} /> },
  { field: "last_payout_email", headerName: "Last payout email", minWidth: 240,
    cellRenderer: (p: ICellRendererParams<Supplier>) => p.data && differs(p.data)
      ? <span className="flex items-center gap-1.5 font-semibold" title="Differs from the PayPal email on file"><TriangleAlert size={16} aria-hidden /><span className="sr-only">Differs from the email on file. </span>{p.value}</span>
      : <span>{p.value ?? "None yet"}</span> },
];

/** Bars of successful payouts in order, with a dashed line at the median. Inline SVG, no chart library. */
function PayoutChart({ payments, median }: { payments: SupplierAnalytics["payments"]; median: number | null }) {
  if (payments.length === 0) return null;
  const W = 420, H = 140, pad = 24;
  const max = Math.max(...payments.map((p) => p.amount)) * 1.1;
  const y = (v: number) => H - pad - (v / max) * (H - pad * 2);
  const bw = Math.min(40, (W - pad * 2) / payments.length - 6);
  const x = (i: number) => pad + ((W - pad * 2) / payments.length) * (i + 0.5) - bw / 2;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img"
      aria-label={`Payout amounts: ${payments.map((p) => `${p.invoice} ${money(p.amount, p.currency)}`).join(", ")}`}>
      <line x1={pad} x2={W - pad} y1={H - pad} y2={H - pad} className="stroke-ink" />
      {payments.map((p, i) => (
        <g key={i}>
          <rect x={x(i)} y={y(p.amount)} width={bw} height={H - pad - y(p.amount)} className="fill-blue stroke-ink" />
          <text x={x(i) + bw / 2} y={y(p.amount) - 4} textAnchor="middle" fontSize="10" className="fill-ink">{money(p.amount, p.currency)}</text>
          <text x={x(i) + bw / 2} y={H - 8} textAnchor="middle" fontSize="10" className="fill-ink">{p.invoice}</text>
        </g>
      ))}
      {median !== null && (
        <g>
          <line x1={pad} x2={W - pad} y1={y(median)} y2={y(median)} strokeDasharray="4 3" className="stroke-ink" />
          <text x={W - pad} y={y(median) - 3} textAnchor="end" fontSize="10" className="fill-ink">median</text>
        </g>
      )}
    </svg>
  );
}

function Analytics({ id, onClose, onVerified }: { id: number; onClose: () => void; onVerified: () => void }) {
  const { data: a, loading, error, reload } = useApi<SupplierAnalytics>(`/suppliers/${id}/analytics`);
  const [signing, setSigning] = useState(false);
  const [payload, setPayload] = useState<string | null>(null);
  const [prepError, setPrepError] = useState<string | null>(null);
  useEffect(() => {
    if (!signing) return;
    api<{ payload: string }>(`/suppliers/${id}/verify-payload`).then((r) => setPayload(r.payload), () => setPrepError("Could not prepare the signing data."));
  }, [signing, id]);
  const closeSigning = () => { setSigning(false); setPayload(null); setPrepError(null); reload(); onVerified(); };
  return (
    <>
    <Drawer title={a?.supplier.name ?? "Supplier"} onClose={onClose}>
      {loading && <Skeleton rows={3} />}
      {error && <Banner kind="error" title="Could not load this supplier">{error}</Banner>}
      {a && (
        <div className="space-y-4">
          {!a.supplier.verified && <Button onClick={() => setSigning(true)}>Verify supplier</Button>}
          <dl className="grid grid-cols-2 gap-3 text-[14px]">
            <div><dt className="label">Paid</dt><dd className="money">{money(a.paid_total)} in {a.paid_count}</dd></div>
            <div><dt className="label">Median payout</dt><dd className="money">{a.paid_median === null ? "None yet" : money(a.paid_median)}</dd></div>
            <div><dt className="label">Largest payout</dt><dd className="money">{a.paid_max === null ? "None yet" : money(a.paid_max)}</dd></div>
            <div><dt className="label">Last paid</dt><dd>{a.last_paid_at ? when(a.last_paid_at) : "Never"}</dd></div>
            <div><dt className="label">Invoices</dt><dd>{a.invoices}</dd></div>
            <div><dt className="label">Decisions</dt><dd>{Object.entries(a.decisions).map(([k, v]) => `${v} ${stepLabel(k).toLowerCase()}`).join(", ") || "None yet"}</dd></div>
          </dl>
          <div>
            <p className="label">Flags raised</p>
            <p className="text-[14px]">{Object.entries(a.flags).map(([k, v]) => `${stepLabel(k)} (${v})`).join(", ") || "None"}</p>
          </div>
          <div>
            <p className="label">Trust history</p>
            {a.events.length === 0 ? <p className="text-[14px]">No changes recorded. Seeded suppliers start verified.</p> : (
              <ul className="text-[14px] space-y-1">
                {a.events.map((e, i) => <li key={i}>{e.step === "supplier_created" ? "Added" : "Verified"}{e.by ? ` by ${e.by}` : ""}{e.signed ? " with a signature" : ""} · {when(e.at)}</li>)}
              </ul>
            )}
          </div>
          <div>
            <p className="label">Payment history</p>
            <PayoutChart payments={a.payments} median={a.paid_median} />
            {a.payments.length === 0 ? <p className="text-[14px]">No successful payouts yet.</p> : (
              <ul className="text-[14px] space-y-1">
                {a.payments.map((p, i) => <li key={i} className="flex justify-between"><span>{p.invoice} · {when(p.at)}</span><span className="money">{money(p.amount, p.currency)}</span></li>)}
              </ul>
            )}
          </div>
        </div>
      )}
    </Drawer>
      {signing && a && (
        <SigningModal title="Verify this supplier" confirmLabel="Sign and verify" payload={payload} prepError={prepError} onClose={closeSigning}
          summary={<p className="text-[14px]">You are trusting <strong>{a.supplier.name}</strong> ({a.supplier.country}). Once verified, its invoices are no longer blocked as unverified. Your signature covers this exact name, country and PayPal email.</p>}
          onConfirm={async (signature) => { await api(`/suppliers/${id}/verify`, { body: { signature } }); return <>{a.supplier.name} is now verified.</>; }} />
      )}
    </>
  );
}

export default function Suppliers() {
  const [open, setOpen] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);
  const { data, loading, error, reload } = useApi<Supplier[]>("/suppliers");
  return (
    <div>
      <PageHeader note="who you pay" title="Suppliers" text="Verified suppliers and the email each one was last paid at. Open one for its payment history."
        action={<Button onClick={() => setAdding(true)}><Plus size={14} aria-hidden />Add supplier</Button>} />
      {error && <ErrorState message={error} onRetry={reload} />}
      <OpsGrid rows={error ? null : data} cols={cols} loading={loading} onRowClicked={(r) => setOpen(r.id)} empty={{ note: "no suppliers", text: "Seed the demo data to see suppliers." }} />
      {open !== null && <Analytics id={open} onClose={() => setOpen(null)} onVerified={reload} />}
      {adding && <AddSupplierDrawer onClose={() => setAdding(false)} onCreated={() => { setAdding(false); reload(); }} />}
    </div>
  );
}
