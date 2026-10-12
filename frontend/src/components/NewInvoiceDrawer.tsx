import { useState } from "react";
import type { FormEvent } from "react";
import { ApiError, api } from "../lib/api";
import type { Invoice, Supplier } from "../lib/types";
import Banner from "./Banner";
import Button from "./Button";
import Drawer from "./Drawer";

export default function NewInvoiceDrawer({ suppliers, onClose, onCreated }: { suppliers: Supplier[]; onClose: () => void; onCreated: (i: Invoice) => void }) {
  const [supplierId, setSupplierId] = useState("");
  const [email, setEmail] = useState("");
  const [number, setNumber] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pick = (id: string) => {
    setSupplierId(id);
    setEmail(suppliers.find((s) => String(s.id) === id)?.paypal_email ?? "");  // editable: a different email is flagged at payment time
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const inv = await api<Invoice>("/invoices", {
        body: { supplier_id: Number(supplierId), number: number.trim() || null, description, amount, payee_email: email.trim() },
      });
      onCreated(inv);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Could not reach the server.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Drawer title="New invoice" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        <label className="block"><span className="label block mb-1">Supplier</span>
          <select className="input" value={supplierId} onChange={(e) => pick(e.target.value)} required>
            <option value="" disabled>Choose a supplier</option>
            {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}{s.verified ? "" : " (unverified)"}</option>)}
          </select></label>
        <label className="block"><span className="label block mb-1">Payee email</span>
          <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required maxLength={255} /></label>
        <label className="block"><span className="label block mb-1">Amount</span>
          <input className="input" type="number" min="0.01" max="100000" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required /></label>
        <label className="block"><span className="label block mb-1">Invoice number (optional)</span>
          <input className="input" value={number} onChange={(e) => setNumber(e.target.value)} maxLength={50} pattern="[A-Za-z0-9._\-]+" placeholder="Next INV-00N if blank" /></label>
        <label className="block"><span className="label block mb-1">Description</span>
          <textarea className="input !h-28 py-2" value={description} onChange={(e) => setDescription(e.target.value)} required maxLength={2000} /></label>
        {error && <Banner kind="error" title={error} />}
        <Button type="submit" loading={busy}>Add invoice</Button>
      </form>
    </Drawer>
  );
}
