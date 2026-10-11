import type { ColDef, ICellRendererParams } from "ag-grid-community";
import { TriangleAlert } from "lucide-react";
import ErrorState from "../components/ErrorState";
import OpsGrid from "../components/OpsGrid";
import PageHeader from "../components/PageHeader";
import StatusBadge from "../components/StatusBadge";
import useApi from "../hooks/useApi";
import type { Supplier } from "../lib/types";

const differs = (s: Supplier) => !!s.last_payout_email && s.last_payout_email.toLowerCase() !== s.paypal_email.toLowerCase();

const cols: ColDef<Supplier>[] = [
  { field: "name", headerName: "Name" },
  { field: "country", headerName: "Country", maxWidth: 120 },
  { field: "paypal_email", headerName: "PayPal email", minWidth: 240 },
  { field: "verified", headerName: "Verified", maxWidth: 150,
    cellRenderer: (p: ICellRendererParams<Supplier>) => <StatusBadge value={p.value ? "VERIFIED" : "PENDING"} /> },
  { field: "last_payout_email", headerName: "Last payout email", minWidth: 240,
    cellRenderer: (p: ICellRendererParams<Supplier>) => p.data && differs(p.data)
      ? <span className="flex items-center gap-1.5 font-semibold" title="Differs from the PayPal email on file"><TriangleAlert size={16} aria-hidden /><span className="sr-only">Differs from the email on file. </span>{p.value}</span>
      : <span>{p.value ?? "None yet"}</span> },
];

export default function Suppliers() {
  const { data, loading, error, reload } = useApi<Supplier[]>("/suppliers");
  return (
    <div>
      <PageHeader note="who you pay" title="Suppliers" text="Verified suppliers and the email each one was last paid at." />
      {error && <ErrorState message={error} onRetry={reload} />}
      <OpsGrid rows={error ? null : data} cols={cols} loading={loading} empty={{ note: "no suppliers", text: "Seed the demo data to see suppliers." }} />
    </div>
  );
}
